from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..limiter import limiter
from ..models import Order
from ..schemas import Esign, KycIdentifiers
from ..services.kyc.ocr import ocr_available
from ..services.kyc.parsers import DOC_TYPES
from ..services.kyc.service import evaluate, get_submission, load_sample, process_document, submission_view, verify
from ..services.registry import lookup_gstin, lookup_udyam
from ..services.storage import audit
from ..services.tracker import tracker_view
from ..utils.validators import normalise_gstin, normalise_udyam
from .consent import require_consent

router = APIRouter(prefix="/kyc", tags=["kyc"])
MAX_UPLOAD = 8 * 1024 * 1024
DEMO_OTP = "123456"


def _require_ocr() -> None:
    if not ocr_available():
        raise HTTPException(503, "OCR is not available on this server – install Tesseract")


@router.get("/{order_id}")
def get_kyc(order: Order = Depends(require_consent), db: Session = Depends(get_db)):
    return submission_view(get_submission(db, order))


@router.post("/{order_id}/identifiers")
@limiter.limit("30/minute")
def identifiers(request: Request, body: KycIdentifiers, order: Order = Depends(require_consent),
                db: Session = Depends(get_db)):
    sub = get_submission(db, order)
    result = {}
    if body.gstin:
        sub.typed_gstin = normalise_gstin(body.gstin)
        info = lookup_gstin(db, body.gstin)
        result["gstin"] = {k: v for k, v in info.items() if k != "gstin"}
    sub.no_udyam = body.no_udyam
    if body.udyam and not body.no_udyam:
        sub.typed_udyam = normalise_udyam(body.udyam)
        info = lookup_udyam(db, body.udyam)
        result["udyam"] = {k: v for k, v in info.items() if k != "udyam"}
    db.commit()
    return result


@router.post("/{order_id}/documents/{doc_type}")
async def upload(doc_type: str, file: UploadFile, order: Order = Depends(require_consent),
                 db: Session = Depends(get_db)):
    if doc_type not in DOC_TYPES:
        raise HTTPException(404, "Unknown document type")
    _require_ocr()
    data = await file.read()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "File too large (max 8 MB)")
    sub = get_submission(db, order)
    try:
        process_document(db, sub, doc_type, data)
    except ValueError as e:
        raise HTTPException(422, str(e))
    evaluate(db, sub)
    audit(db, "customer", "document_uploaded", order.id, doc_type=doc_type)
    db.commit()
    return submission_view(sub)


@router.post("/{order_id}/load-sample/{applicant}")
def sample(applicant: str, order: Order = Depends(require_consent), db: Session = Depends(get_db)):
    _require_ocr()
    try:
        sub = load_sample(db, order, applicant)
    except LookupError as e:
        raise HTTPException(404, str(e))
    evaluate(db, sub)
    audit(db, "demo", "sample_loaded", order.id, applicant=applicant.upper())
    db.commit()
    return submission_view(sub)


@router.post("/{order_id}/verify")
def run_verify(order: Order = Depends(require_consent), db: Session = Depends(get_db)):
    sub = get_submission(db, order)
    status = verify(db, order, sub)
    audit(db, "system", "kyc_verified", order.id, result=status)
    db.commit()
    return {**submission_view(sub), "order": tracker_view(order)}


@router.post("/{order_id}/esign")
def esign(body: Esign, order: Order = Depends(require_consent), db: Session = Depends(get_db)):
    if body.otp != DEMO_OTP:
        raise HTTPException(422, "Incorrect OTP")
    sub = get_submission(db, order)
    sub.esigned = True
    audit(db, "customer", "esigned", order.id, method="aadhaar_otp_mock")
    db.commit()
    return {"ok": True, "esigned": True}
