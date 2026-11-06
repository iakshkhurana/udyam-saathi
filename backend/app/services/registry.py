from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import BusinessTypeSegment, CityTier, GstinRecord, UdyamRecord
from ..utils.masking import mask_gstin, mask_udyam
from ..utils.validators import gstin_checksum_ok, gstin_format_ok, normalise_gstin, normalise_udyam, udyam_valid


def lookup_gstin(db: Session, raw: str) -> dict:
    g = normalise_gstin(raw)
    result = {"gstin": g, "gstin_masked": mask_gstin(g), "format_ok": gstin_format_ok(g),
              "checksum_ok": gstin_format_ok(g) and gstin_checksum_ok(g)}
    if not result["checksum_ok"]:
        return {**result, "found": False, "status": "Invalid"}
    rec = db.get(GstinRecord, g)
    if not rec:
        return {**result, "found": False, "status": "NotFound"}
    return {**result, "found": True, "status": rec.status, "legal_name": rec.legal_name,
            "trade_name": rec.trade_name, "constitution": rec.constitution,
            "address": rec.principal_place_of_business, "state": rec.state,
            "registration_date": rec.registration_date.isoformat()}


def lookup_udyam(db: Session, raw: str) -> dict:
    u = normalise_udyam(raw)
    result = {"udyam": u, "udyam_masked": mask_udyam(u), "format_ok": udyam_valid(u)}
    rec = db.get(UdyamRecord, u) if result["format_ok"] else None
    if not rec:
        return {**result, "found": False}
    return {**result, "found": True, "enterprise_name": rec.enterprise_name, "enterprise_type": rec.enterprise_type,
            "major_activity": rec.major_activity, "state": rec.state, "city": rec.city,
            "date_of_registration": rec.date_of_registration.isoformat()}


def city_tier(db: Session, city: str) -> dict:
    cities = {c.city: c for c in db.scalars(select(CityTier))}
    match = process.extractOne(city.strip(), cities.keys(), scorer=fuzz.WRatio, score_cutoff=85)
    if not match:
        return {"city": city.strip().title(), "tier": 2, "known": False}
    rec = cities[match[0]]
    return {"city": rec.city, "tier": rec.city_tier, "state": rec.state, "known": True}


def map_business_type(db: Session, text: str) -> dict | None:
    types = {b.business_type: b.segment for b in db.scalars(select(BusinessTypeSegment))}
    match = process.extractOne(text.strip(), types.keys(), scorer=fuzz.WRatio, score_cutoff=70)
    if not match:
        return None
    return {"business_type": match[0], "segment": types[match[0]], "score": round(match[1])}
