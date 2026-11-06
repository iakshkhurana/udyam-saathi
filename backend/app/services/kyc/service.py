import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...config import get_settings
from ...models import KycCheck, KycDocument, KycSubmission, Order
from ...utils.masking import mask_gstin, mask_name, mask_signatory_id, mask_udyam
from ...utils.validators import normalise_gstin, normalise_udyam
from .. import storage
from ..llm_client import get_llm_client
from ..tracker import set_status
from .checks import doc_status, final_status, run_checks
from .ocr import run_ocr
from .parsers import DOC_TYPES, FIELDS, detect_type, parse

log = logging.getLogger(__name__)
SAMPLES = [f"K{n:02d}" for n in range(1, 13)]


def get_submission(db: Session, order: Order) -> KycSubmission:
    sub = db.scalar(select(KycSubmission).where(KycSubmission.order_id == order.id))
    if not sub:
        sub = KycSubmission(order_id=order.id)
        db.add(sub)
        db.flush()
    return sub


def _vision_cross_check(doc_type: str, data: bytes, fields: dict) -> None:
    llm = get_llm_client()
    if not llm:
        return
    keys = sorted({k for k, _ in FIELDS[doc_type]})
    try:
        reply = llm.read_image(data, f"Extract these fields from this {DOC_TYPES[doc_type]} as one JSON object with "
                                     f"keys {keys}. Use \"\" for blank values. Reply with JSON only.")
        vision = json.loads(re.search(r"\{.*\}", reply, re.S).group())
    except Exception as exc:
        log.warning("Vision cross-check skipped: %s", exc)
        return
    diffs = [k for k in keys if str(vision.get(k, "")).strip().lower() != str(fields.get(k, "")).strip().lower()]
    if diffs:
        log.info("Vision/OCR disagreement on %s fields: %s", doc_type, diffs)


def process_document(db: Session, sub: KycSubmission, doc_type: str, data: bytes) -> KycDocument:
    ocr = run_ocr(data)
    detected = detect_type(ocr)
    fields = parse(detected if detected in DOC_TYPES else doc_type, ocr)
    _vision_cross_check(doc_type, data, fields)
    for old in [d for d in sub.documents if d.doc_type == doc_type]:
        storage.delete(old.storage_key)
        sub.documents.remove(old)
    doc = KycDocument(doc_type=doc_type, storage_key=storage.save(data), detected_type=detected,
                      blur_score=ocr.blur_score, fields={**fields, "deskew_angle": ocr.angle})
    sub.documents.append(doc)
    return doc


def evaluate(db: Session, sub: KycSubmission) -> list[dict]:
    docs = {d.doc_type: {"fields": d.fields, "blur": d.blur_score, "detected": d.detected_type} for d in sub.documents}
    checks = run_checks(db, docs, sub.typed_gstin, sub.typed_udyam, sub.no_udyam)
    sub.checks = [KycCheck(check_id=c["id"], status=c["status"], message_en=c["message_en"],
                           message_hi=c["message_hi"], evidence={**c["evidence"], "doc": c.get("doc")}) for c in checks]
    return checks


def verify(db: Session, order: Order, sub: KycSubmission) -> str:
    checks = evaluate(db, sub)
    status = final_status(checks)
    sub.status = status
    if status == "PASS" and order.status in ("CONSENT_GIVEN", "KYC_REVIEW"):
        set_status(order, "KYC_VERIFIED")
    elif status == "PASS_WITH_WARNINGS" and order.status == "CONSENT_GIVEN":
        set_status(order, "KYC_REVIEW")
    return status


def submission_view(sub: KycSubmission) -> dict:
    checks = [{"id": c.check_id, "status": c.status, "message_en": c.message_en, "message_hi": c.message_hi,
               "doc": c.evidence.get("doc"), "evidence": {k: v for k, v in c.evidence.items() if k != "doc"}}
              for c in sub.checks]
    def masked(fields: dict) -> dict:
        out = {}
        for k, v in fields.items():
            if k in ("gstin", "gstin_raw"):
                v = mask_gstin(v)
            elif k == "udyam_number":
                v = mask_udyam(v)
            elif k == "id_no":
                v = mask_signatory_id(v)
            elif k == "name":
                v = mask_name(v)
            out[k] = v
        return out

    return {
        "order_id": sub.order_id, "status": sub.status, "esigned": sub.esigned, "no_udyam": sub.no_udyam,
        "typed_gstin": mask_gstin(sub.typed_gstin), "typed_udyam": mask_udyam(sub.typed_udyam),
        "documents": {d.doc_type: {"detected_type": d.detected_type, "blur_score": d.blur_score,
                                   "fields": masked(d.fields), "status": doc_status(d.doc_type, checks) if checks else None}
                      for d in sub.documents},
        "checks": checks,
    }


def load_sample(db: Session, order: Order, applicant: str) -> KycSubmission:
    applicant = applicant.upper()
    if applicant not in SAMPLES:
        raise LookupError("Unknown sample applicant")
    sub = get_submission(db, order)
    for d in list(sub.documents):
        storage.delete(d.storage_key)
    sub.documents.clear()
    folder = get_settings().kyc_docs_path
    for doc_type in DOC_TYPES:
        path = folder / f"{applicant}_{doc_type}.png"
        if path.exists():
            process_document(db, sub, doc_type, path.read_bytes())
    fields = {d.doc_type: d.fields for d in sub.documents}
    sub.typed_gstin = normalise_gstin(fields.get("gst_certificate", {}).get("gstin", "")) or None
    sub.typed_udyam = normalise_udyam(fields.get("udyam_certificate", {}).get("udyam_number", "")) or None
    sub.no_udyam = False
    db.flush()
    return sub


EXPECTED = {
    "K01": ("FAIL", {"C05": "fail", "C09": "fail"}), "K02": ("PASS", {}), "K03": ("PASS", {}),
    "K04": ("RETAKE", {"C02": "fail", "C17": "warn"}), "K05": ("INCOMPLETE", {"C01": "fail"}),
    "K06": ("FAIL", {"C04": "fail"}), "K07": ("FAIL", {"C07": "fail"}),
    "K08": ("PASS_WITH_WARNINGS", {"C17": "warn"}), "K09": ("PASS_WITH_WARNINGS", {"C17": "warn"}),
    "K10": ("FAIL", {"C04": "fail", "C18": "warn"}), "K11": ("FAIL", {"C12": "fail"}), "K12": ("PASS", {}),
}


def evaluate_sample(db: Session, applicant: str) -> dict:
    """Run OCR + all checks for one specimen applicant without creating an order."""
    folder = get_settings().kyc_docs_path
    docs = {}
    for doc_type in DOC_TYPES:
        path = folder / f"{applicant}_{doc_type}.png"
        if path.exists():
            ocr = run_ocr(path.read_bytes())
            detected = detect_type(ocr)
            docs[doc_type] = {"fields": parse(doc_type, ocr), "blur": ocr.blur_score, "detected": detected,
                              "angle": ocr.angle}
    gstin = docs.get("gst_certificate", {}).get("fields", {}).get("gstin") or None
    udyam = docs.get("udyam_certificate", {}).get("fields", {}).get("udyam_number") or None
    checks = run_checks(db, docs, gstin, udyam, False)
    status = final_status(checks)
    expected_status, flags = EXPECTED[applicant]
    by_id: dict[str, set] = {}
    for c in checks:
        by_id.setdefault(c["id"], set()).add(c["status"])
    flags_caught = all(want in by_id.get(cid, set()) for cid, want in flags.items())
    return {"applicant": applicant, "docs": docs, "checks": checks, "status": status,
            "expected_status": expected_status, "expected_flags": flags, "flags_caught": flags_caught,
            "matches": flags_caught and status == expected_status}
