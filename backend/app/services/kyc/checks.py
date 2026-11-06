import re
from datetime import date, timedelta

from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...config import get_settings
from ...models import GstinRecord, Lead, UdyamRecord
from ...utils.masking import mask_gstin, mask_udyam
from ...utils.validators import gstin_valid, normalise_gstin, normalise_udyam, udyam_valid
from .ocr import BLUR_THRESHOLD

DOC_LABELS = {"gst_certificate": ("GST certificate", "GST सर्टिफ़िकेट"),
              "udyam_certificate": ("Udyam certificate", "उद्यम सर्टिफ़िकेट"),
              "signatory_id": ("Signatory ID", "हस्ताक्षरकर्ता ID"), "address_proof": ("Address proof", "पते का प्रमाण")}
DOC_CHECKS = {"gst_certificate": {"C04", "C05", "C06", "C07", "C08"},
              "udyam_certificate": {"C09", "C10", "C11"},
              "address_proof": {"C12", "C13", "C14"}, "signatory_id": {"C15", "C16", "C17", "C18"}}
PROP = re.compile(r"^(.*?)\s*\(\s*Prop\.?\s*(.*?)\)\s*$", re.I)


def ocr_canonical(g: str) -> str:
    """Collapse OCR-ambiguous pairs so edit distance counts only real differences."""
    return g.translate(str.maketrans("OI", "01"))


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).strip()


def sim(a: str | None, b: str | None) -> float:
    return fuzz.token_sort_ratio(norm(a), norm(b))


def legal_name_score(doc: str, reg: str) -> float:
    """For '<Person> (Prop. <Business>)' both parts must match, so a swapped business name cannot hide."""
    a, b = PROP.match(doc or ""), PROP.match(reg or "")
    if a and b:
        return min(sim(a.group(1), b.group(1)), sim(a.group(2), b.group(2)))
    return sim(doc, reg)


def _check(cid: str, status: str, en: str, hi: str, doc: str | None = None, **evidence) -> dict:
    return {"id": cid, "status": status, "message_en": en, "message_hi": hi, "doc": doc, "evidence": evidence}


def _pass(cid: str, en: str = "OK", hi: str = "ठीक है", doc: str | None = None, **ev) -> dict:
    return _check(cid, "pass", en, hi, doc, **ev)


def _skip(cid: str, en: str, hi: str, doc: str | None = None) -> dict:
    return _check(cid, "skip", en, hi, doc)


def constitution_of(gst: dict, reg: GstinRecord | None, names: list[str]) -> str:
    if reg:
        return reg.constitution
    if gst.get("constitution"):
        return gst["constitution"]
    joined = " ".join(n or "" for n in names).lower()
    if re.search(r"\bllp\b", joined):
        return "Limited Liability Partnership"
    if re.search(r"pvt|private limited", joined):
        return "Private Limited Company"
    return ""


def run_checks(db: Session, docs: dict[str, dict], typed_gstin: str | None, typed_udyam: str | None,
               no_udyam: bool) -> list[dict]:
    today = get_settings().app_today
    out: list[dict] = []
    gst = docs.get("gst_certificate", {}).get("fields", {})
    udy = docs.get("udyam_certificate", {}).get("fields", {})
    bill = docs.get("address_proof", {}).get("fields", {})
    sig = docs.get("signatory_id", {}).get("fields", {})

    missing = [d for d in DOC_LABELS if d not in docs and not (d == "udyam_certificate" and no_udyam)]
    if missing:
        en = ", ".join(DOC_LABELS[d][0] for d in missing)
        hi = ", ".join(DOC_LABELS[d][1] for d in missing)
        tip = (" – upload it or tap 'I don't have Udyam'", " – अपलोड करें या 'मेरे पास उद्यम नहीं है' दबाएँ") \
            if "udyam_certificate" in missing else ("", "")
        out.append(_check("C01", "fail", f"Missing: {en}{tip[0]}", f"नहीं मिला: {hi}{tip[1]}", missing=missing))
    else:
        out.append(_pass("C01", "All documents received", "सभी दस्तावेज़ मिल गए"))

    for doc_type, d in docs.items():
        label_en, label_hi = DOC_LABELS[doc_type]
        if d.get("blur", BLUR_THRESHOLD) < BLUR_THRESHOLD or d["fields"].get("missing"):
            reason = "blurry" if d.get("blur", BLUR_THRESHOLD) < BLUR_THRESHOLD else "hard to read"
            out.append(_check("C02", "fail", f"{label_en}: photo is {reason} – please retake in good light, flat and "
                              "fully in frame", f"{label_hi}: फ़ोटो साफ़ नहीं है – अच्छी रोशनी में, सीधा और पूरा दस्तावेज़ "
                              "दिखाते हुए दोबारा लें", doc_type, blur_score=d.get("blur"),
                              threshold=BLUR_THRESHOLD, unreadable_fields=d["fields"].get("missing")))
        else:
            out.append(_pass("C02", f"{label_en}: clear photo", f"{label_hi}: फ़ोटो साफ़ है", doc_type,
                             blur_score=d.get("blur")))
        if d.get("detected") and d["detected"] != doc_type:
            other_en, other_hi = DOC_LABELS[d["detected"]]
            out.append(_check("C03", "fail", f"This looks like a {other_en}, not a {label_en} – please upload it in the "
                              "right slot", f"यह {other_hi} लगता है, {label_hi} नहीं – सही जगह अपलोड करें", doc_type,
                              detected=d["detected"]))
        elif d.get("detected"):
            out.append(_pass("C03", f"{label_en}: correct document type", f"{label_hi}: सही दस्तावेज़", doc_type))

    reg = None
    cert_gstin = gst.get("gstin", "")
    if "gst_certificate" in docs and cert_gstin:
        if gstin_valid(cert_gstin):
            out.append(_pass("C04", "GSTIN format and checksum valid", "GSTIN फ़ॉर्मेट और चेकसम सही",
                             gstin=mask_gstin(cert_gstin)))
            reg = db.get(GstinRecord, cert_gstin)
            if not reg:
                out.append(_check("C05", "fail", "This GSTIN is not in the GST registry", "यह GSTIN GST रजिस्ट्री में नहीं है"))
            elif reg.status != "Active":
                out.append(_check("C05", "fail", f"This GSTIN is {reg.status} in the GST registry – we can only connect "
                                  "businesses with an Active GSTIN", f"यह GSTIN GST रजिस्ट्री में {reg.status} है – "
                                  "सिर्फ़ Active GSTIN वाले बिज़नेस जोड़े जा सकते हैं", registry_status=reg.status))
            else:
                out.append(_pass("C05", "GSTIN is Active in the registry", "GSTIN रजिस्ट्री में Active है"))
        else:
            closest = None
            prefix = cert_gstin[:2]
            for g in db.scalars(select(GstinRecord.gstin).where(GstinRecord.gstin.like(f"{prefix}%"))):
                if Levenshtein.distance(ocr_canonical(g), ocr_canonical(cert_gstin)) <= 1:
                    closest = g
                    break
            out.append(_check("C04", "fail", "GSTIN on the certificate is not valid – the document may be edited. "
                              "Please upload the original certificate", "सर्टिफ़िकेट पर GSTIN सही नहीं है – दस्तावेज़ "
                              "बदला हुआ हो सकता है। असली सर्टिफ़िकेट अपलोड करें", gstin_read=mask_gstin(cert_gstin),
                              closest_registry_gstin=mask_gstin(closest) if closest else None,
                              closest_distance=1 if closest else None))
            out.append(_skip("C05", "Registry status not checked (invalid GSTIN)", "रजिस्ट्री स्थिति नहीं जाँची गई"))
        if typed_gstin:
            typed = normalise_gstin(typed_gstin)
            if typed == cert_gstin:
                out.append(_pass("C06", "GSTIN you entered matches the certificate", "आपका GSTIN सर्टिफ़िकेट से मेल खाता है"))
            else:
                out.append(_check("C06", "fail", "The GSTIN you entered doesn't match the certificate",
                                  "आपका लिखा GSTIN सर्टिफ़िकेट से मेल नहीं खाता", typed=mask_gstin(typed),
                                  certificate=mask_gstin(cert_gstin)))
        if reg:
            legal, trade = legal_name_score(gst.get("legal_name", ""), reg.legal_name), sim(gst.get("trade_name"), reg.trade_name)
            low = min(legal, trade)
            ev = {"legal_name_score": round(legal), "trade_name_score": round(trade)}
            if low < 80:
                out.append(_check("C07", "fail", "Business name on the certificate doesn't match the GST registry",
                                  "सर्टिफ़िकेट पर बिज़नेस का नाम GST रजिस्ट्री से मेल नहीं खाता", **ev,
                                  registry_legal_name=reg.legal_name, certificate_legal_name=gst.get("legal_name")))
            elif low < 90:
                out.append(_check("C07", "warn", "Business name is slightly different from the GST registry – a reviewer "
                                  "will confirm", "बिज़नेस का नाम रजिस्ट्री से थोड़ा अलग है – टीम जाँच करेगी", **ev))
            else:
                out.append(_pass("C07", "Legal and trade name match the GST registry", "नाम GST रजिस्ट्री से मेल खाता है", **ev))
            if gst.get("date_of_liability") == reg.registration_date.isoformat():
                out.append(_pass("C08", "Registration date matches", "रजिस्ट्रेशन तारीख मेल खाती है"))
            else:
                out.append(_check("C08", "warn", "Date of liability differs from the registry", "तारीख रजिस्ट्री से अलग है",
                                  certificate=gst.get("date_of_liability"), registry=reg.registration_date.isoformat()))

    udyam_rec = None
    if "udyam_certificate" in docs:
        number = normalise_udyam(udy.get("udyam_number") or "")
        if not number:
            out.append(_check("C09", "fail", "Udyam number is blank on the certificate – upload the full certificate or "
                              "tap 'I don't have Udyam'", "उद्यम सर्टिफ़िकेट पर नंबर खाली है – पूरा सर्टिफ़िकेट अपलोड करें "
                              "या 'मेरे पास उद्यम नहीं है' दबाएँ"))
        elif not udyam_valid(number) or not (udyam_rec := db.get(UdyamRecord, number)):
            out.append(_check("C09", "fail", "Udyam number is not valid or not found in the Udyam registry",
                              "उद्यम नंबर सही नहीं है या रजिस्ट्री में नहीं मिला", udyam=mask_udyam(number)))
        else:
            out.append(_pass("C09", "Udyam number found in the registry", "उद्यम नंबर रजिस्ट्री में मिला",
                             udyam=mask_udyam(number)))
        if udyam_rec:
            scores = {"name": sim(udy.get("enterprise_name"), udyam_rec.enterprise_name),
                      "city": sim(udy.get("city"), udyam_rec.city), "state": sim(udy.get("state"), udyam_rec.state)}
            info = {"major_activity": [udy.get("major_activity"), udyam_rec.major_activity],
                    "date_of_registration": [udy.get("date_of_registration"),
                                             udyam_rec.date_of_registration.isoformat()]}
            if scores["name"] < 80:
                out.append(_check("C10", "fail", "Enterprise name doesn't match the Udyam registry",
                                  "उद्यम का नाम रजिस्ट्री से मेल नहीं खाता", **scores, info_only=info))
            elif min(scores.values()) < 90:
                out.append(_check("C10", "warn", "Udyam details differ slightly from the registry",
                                  "उद्यम विवरण रजिस्ट्री से थोड़ा अलग है", **scores, info_only=info))
            else:
                out.append(_pass("C10", "Udyam name, city and state match the registry", "उद्यम विवरण मेल खाते हैं",
                                 **scores, info_only=info))
        gst_names = [gst.get("trade_name"), gst.get("legal_name")] + ([reg.trade_name, reg.legal_name] if reg else [])
        if udy.get("enterprise_name") and any(gst_names):
            name_ok = max(sim(udy["enterprise_name"], n) for n in gst_names if n) >= 85
            gst_state = reg.state if reg else None
            state_ok = not gst_state or sim(udy.get("state"), gst_state) >= 90
            if name_ok and state_ok:
                out.append(_pass("C11", "Udyam and GST belong to the same business", "उद्यम और GST एक ही बिज़नेस के हैं"))
            else:
                out.append(_check("C11", "warn", "Udyam and GST details look different – a reviewer will confirm",
                                  "उद्यम और GST विवरण अलग लगते हैं – टीम जाँच करेगी", name_match=name_ok,
                                  state_match=state_ok))
    elif no_udyam:
        out.append(_skip("C09", "No Udyam – that's fine", "उद्यम नहीं है – कोई बात नहीं"))

    if "address_proof" in docs:
        bill_date = bill.get("bill_date")
        cutoff = today - timedelta(days=90)
        if bill_date and date.fromisoformat(bill_date) >= cutoff:
            out.append(_pass("C12", "Bill is recent", "बिल हाल का है", bill_date=bill_date))
        else:
            out.append(_check("C12", "fail", "Bill is older than 90 days – upload a recent one",
                              "बिल 90 दिन से पुराना है – हाल का बिल अपलोड करें", bill_date=bill_date,
                              oldest_allowed=cutoff.isoformat()))
        gst_address = reg.principal_place_of_business if reg else gst.get("address")
        if gst_address and bill.get("supply_address"):
            pin_match = re.search(r"(\d{6})\D*$", gst_address)
            gst_pin = pin_match.group(1) if pin_match else None
            score = sim(bill["supply_address"], gst_address)
            ev = {"address_score": round(score), "bill_pin": bill.get("supply_address_pin"), "gst_pin": gst_pin}
            if gst_pin and bill.get("supply_address_pin") != gst_pin:
                out.append(_check("C13", "fail", "Bill address PIN code doesn't match your GST address",
                                  "बिल का PIN कोड GST पते से मेल नहीं खाता", **ev))
            elif score < 85:
                out.append(_check("C13", "warn", "Bill address differs from the GST address", "बिल का पता GST पते से अलग है", **ev))
            else:
                out.append(_pass("C13", "Bill address matches the GST address", "बिल का पता GST पते से मेल खाता है", **ev))
        names = [n for n in (gst.get("trade_name"), gst.get("legal_name"), reg and reg.trade_name, reg and reg.legal_name) if n]
        if names and bill.get("billed_to"):
            if max(sim(bill["billed_to"], n) for n in names) >= 85:
                out.append(_pass("C14", "Bill is in the business name", "बिल बिज़नेस के नाम पर है"))
            else:
                out.append(_check("C14", "warn", "Bill is in a different name – a reviewer will confirm",
                                  "बिल किसी और नाम पर है – टीम जाँच करेगी", billed_to=bill["billed_to"]))

    if "signatory_id" in docs:
        valid_till = sig.get("valid_till")
        if valid_till and date.fromisoformat(valid_till) >= today:
            out.append(_pass("C15", "Signatory ID is valid", "हस्ताक्षरकर्ता ID मान्य है", valid_till=valid_till))
        else:
            out.append(_check("C15", "fail", "Signatory ID has expired – upload a valid one",
                              "हस्ताक्षरकर्ता ID की वैधता खत्म हो गई – मान्य ID अपलोड करें", valid_till=valid_till))
        names = [n for n in (gst.get("trade_name"), gst.get("legal_name"), reg and reg.trade_name, reg and reg.legal_name,
                             udy.get("enterprise_name")) if n]
        if names and sig.get("for_business"):
            if max(sim(sig["for_business"], n) for n in names) >= 85:
                out.append(_pass("C16", "Signatory belongs to this business", "हस्ताक्षरकर्ता इसी बिज़नेस का है"))
            else:
                out.append(_check("C16", "fail", "Signatory ID is for a different business",
                                  "हस्ताक्षरकर्ता ID किसी और बिज़नेस की है", for_business=sig["for_business"]))
        constitution = constitution_of(gst, reg, [sig.get("for_business"), udy.get("enterprise_name"), bill.get("billed_to")])
        designation = (sig.get("designation") or "").lower()
        legal = reg.legal_name if reg else gst.get("legal_name", "")
        if constitution == "Proprietorship":
            m = PROP.match(legal or "")
            name_ok = bool(m) and sim(sig.get("name"), m.group(1)) >= 90
            if not name_ok:
                out.append(_check("C17", "warn", "Signatory is not the proprietor – an authorisation letter is needed",
                                  "हस्ताक्षरकर्ता मालिक नहीं हैं – अधिकार पत्र चाहिए", constitution=constitution))
            elif "admin" in designation:
                out.append(_check("C17", "warn", "Designation is 'Office admin' but the name matches the proprietor – "
                                  "reviewer to confirm", "पद 'Office admin' है पर नाम मालिक से मेल खाता है – टीम पुष्टि करेगी",
                                  constitution=constitution, designation=sig.get("designation")))
            else:
                out.append(_pass("C17", "Signatory is the proprietor", "हस्ताक्षरकर्ता ही मालिक हैं"))
        elif constitution:
            out.append(_check("C17", "warn", f"{constitution}: authority can't be verified from the registry – needs a "
                              "board resolution / partner letter", f"{constitution}: अधिकार रजिस्ट्री से नहीं जाँचा जा सकता – "
                              "बोर्ड रेज़ोल्यूशन / पार्टनर पत्र चाहिए", constitution=constitution))
        lead = None
        if cert_gstin:
            lead = db.scalar(select(Lead).where(Lead.gstin == cert_gstin))
        udyam_number = normalise_udyam(udy.get("udyam_number") or typed_udyam or "")
        if not lead and udyam_number:
            lead = db.scalar(select(Lead).where(Lead.udyam_number == udyam_number))
        if lead and sig.get("name"):
            if sim(sig["name"], lead.contact_name) >= 85:
                out.append(_pass("C18", "Signatory matches our lead contact", "हस्ताक्षरकर्ता हमारे रिकॉर्ड से मेल खाते हैं"))
            else:
                out.append(_check("C18", "warn", "Signatory differs from the contact we have on file – reviewer to confirm",
                                  "हस्ताक्षरकर्ता हमारे रिकॉर्ड के संपर्क से अलग हैं – टीम पुष्टि करेगी",
                                  lead_id=lead.lead_id))
    owner = {cid: doc for doc, ids in DOC_CHECKS.items() for cid in ids}
    for c in out:
        c["doc"] = c["doc"] or owner.get(c["id"])
    return out


def final_status(checks: list[dict]) -> str:
    fails = {c["id"] for c in checks if c["status"] == "fail"}
    if "C01" in fails:
        return "INCOMPLETE"
    if "C02" in fails:
        return "RETAKE"
    if fails:
        return "FAIL"
    return "PASS_WITH_WARNINGS" if any(c["status"] == "warn" for c in checks) else "PASS"


def doc_status(doc_type: str, checks: list[dict]) -> str:
    relevant = [c for c in checks if c.get("doc") == doc_type]
    statuses = {c["status"] for c in relevant}
    return "fail" if "fail" in statuses else "warn" if "warn" in statuses else "pass"
