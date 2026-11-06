import re

from rapidfuzz import fuzz

from ...utils.validators import gstin_valid, normalise_gstin, normalise_udyam, udyam_valid
from .ocr import OcrResult

DOC_TYPES = {
    "gst_certificate": "GST Registration Certificate",
    "udyam_certificate": "Udyam Registration Certificate",
    "signatory_id": "Authorised Signatory ID",
    "address_proof": "Electricity Bill",
}
FIELDS = {
    "gst_certificate": [("gstin", "GSTIN"), ("legal_name", "Legal name"), ("trade_name", "Trade name"),
                        ("constitution", "Constitution"), ("address", "Address of principal"),
                        ("address", "place of business"), ("date_of_liability", "Date of liability"),
                        ("registration_type", "Type of registration")],
    "udyam_certificate": [("udyam_number", "Udyam reg. number"), ("enterprise_name", "Enterprise name"),
                          ("major_activity", "Major activity"), ("city", "City"), ("state", "State"),
                          ("date_of_registration", "Date of registration")],
    "address_proof": [("consumer_no", "Consumer no."), ("billed_to", "Billed to"),
                      ("supply_address", "Supply address"), ("bill_date", "Bill date"),
                      ("units_consumed", "Units consumed"), ("amount_due", "Amount due (INR)")],
    "signatory_id": [("name", "Name"), ("designation", "Designation"), ("for_business", "For business"),
                     ("id_no", "ID no."), ("valid_till", "Valid till")],
}
MANDATORY = {
    "gst_certificate": ["gstin", "legal_name", "trade_name", "address"],
    "udyam_certificate": ["enterprise_name", "state"],
    "signatory_id": ["name", "for_business", "valid_till"],
    "address_proof": ["billed_to", "supply_address", "bill_date"],
}
MULTILINE = {"address", "supply_address"}
DATE_FIELDS = {"date_of_liability", "date_of_registration", "bill_date", "valid_till"}
VALUE_COLUMN = 0.36
GSTIN_TOKEN = re.compile(r"\b[0-9OIl][0-9OISB][A-Z0-9]{10}[0-9A-Z2][Z2][0-9A-Z]\b")


def detect_type(ocr: OcrResult) -> str | None:
    head = " ".join(line.text for line in ocr.lines[:4])
    scores = {k: fuzz.partial_ratio(v.lower(), head.lower()) for k, v in DOC_TYPES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] >= 80 else None


def _clean(value: str) -> str:
    return re.sub(r"^[^\w(]+|[^\w).]+$", "", value).strip()


def _join(a: str, b: str) -> str:
    if not a:
        return b
    return a + b if a[-1].isalpha() and b[:1].islower() else f"{a} {b}"


def _match_label(text: str, labels: list[str]) -> int | None:
    text = text.lower().strip()
    if not text:
        return None
    scores = [max(fuzz.ratio(text, lab.lower()), fuzz.partial_ratio(lab.lower(), text) - 10) for lab in labels]
    best = max(range(len(labels)), key=scores.__getitem__)
    return best if scores[best] >= 70 else None


def _table(ocr: OcrResult, fields: list[tuple[str, str]]) -> dict:
    labels = [lab for _, lab in fields]
    split = int(ocr.width * VALUE_COLUMN)
    out: dict[str, str] = {}
    last = None
    for line in ocr.lines:
        label, value = line.split(split)
        idx = _match_label(label, labels)
        if idx is not None:
            key = fields[idx][0]
            out[key] = _join(out.get(key, ""), _clean(value)) if key in MULTILINE else _clean(value)
            last = key
        elif last in MULTILINE and value and len(_clean(label)) <= 2:
            out[last] = _join(out[last], _clean(value))
    return out


def _stacked(ocr: OcrResult, fields: list[tuple[str, str]]) -> dict:
    lines = [line.text for line in ocr.lines]
    out = {}
    for key, label in fields:
        for i, text in enumerate(lines[:-1]):
            if fuzz.ratio(text.lower(), label.lower()) >= 80:
                out[key] = _clean(lines[i + 1])
                break
    return out


def _date(value: str) -> str | None:
    v = value.upper().translate(str.maketrans("OIlSB", "01158"))
    m = re.search(r"(\d{4})\s*-\s*(\d{2})\s*-\s*(\d{2})", v)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


UDYAM_TOKEN = re.compile(r"UDYAM\s*-?\s*[A-Z0-9]{2}\s*-?\s*[0-9O]{2}\s*-?\s*[0-9OIlSB]{7}")


def _passes(ocr: OcrResult) -> list[str]:
    return [ocr.text, *ocr.alternative_texts]


def _best_gstin(raw: str, ocr: OcrResult) -> str:
    """Primary read first; other OCR passes only if it is missing or invalid. Characters are never edited."""
    primary = normalise_gstin(raw)
    if gstin_valid(primary):
        return primary
    for text in _passes(ocr):
        for line in text.upper().splitlines():
            for token in GSTIN_TOKEN.findall(line.replace(" ", "").replace("GSTIN", " ")):
                if gstin_valid(candidate := normalise_gstin(token)):
                    return candidate
    if primary:
        return primary
    return next((normalise_gstin(t) for text in _passes(ocr) for line in text.upper().splitlines()
                 for t in GSTIN_TOKEN.findall(line.replace(" ", "").replace("GSTIN", " "))), "")


def _best_udyam(raw: str, ocr: OcrResult) -> str:
    primary = normalise_udyam(raw) if re.search(r"\d", raw) else ""
    if primary and udyam_valid(primary):
        return primary
    for text in _passes(ocr):
        if (m := UDYAM_TOKEN.search(text.upper())) and udyam_valid(candidate := normalise_udyam(m.group())):
            return candidate
    return primary


def parse(doc_type: str, ocr: OcrResult) -> dict:
    fields = FIELDS[doc_type]
    raw = _stacked(ocr, fields) if doc_type == "signatory_id" else _table(ocr, fields)
    out = dict(raw)
    for key in DATE_FIELDS & raw.keys():
        out[key] = _date(raw[key])
    if doc_type == "gst_certificate":
        out["gstin_raw"] = raw.get("gstin", "")
        out["gstin"] = _best_gstin(out["gstin_raw"].replace(" ", ""), ocr)
    if doc_type == "udyam_certificate":
        out["udyam_number"] = _best_udyam(raw.get("udyam_number", ""), ocr)
    if doc_type == "signatory_id" and (m := re.search(r"SYN-?ID-?(\d{6})", raw.get("id_no", "").upper().replace(" ", ""))):
        out["id_no"] = f"SYN-ID-{m.group(1)}"
    for key in ("address", "supply_address"):
        if out.get(key) and (m := re.search(r"(\d(?:\s?\d){5})\D*$", out[key])):
            out[f"{key}_pin"] = m.group(1).replace(" ", "")
    out["missing"] = [k for k in MANDATORY[doc_type] if not out.get(k)]
    return out
