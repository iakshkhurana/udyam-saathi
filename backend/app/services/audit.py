from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Lead
from ..schemas import Profile
from ..utils.masking import mask_gstin
from .catalogue import get_catalogue
from .data_loader import SEGMENT_CODES
from .rules_engine import failed_rules

RULE_LABELS = {"tier": "city tier", "gstin": "GSTIN", "dependency": "dependency", "employees": "employees",
               "sites": "sites"}


def parse_bundle(text: str) -> list[tuple[str, int]]:
    out = []
    for part in (text or "").split(";"):
        if "x" in part:
            pid, qty = part.strip().split("x")
            out.append((pid, int(qty)))
    return out


def audit_sold_bundles(db: Session) -> dict:
    cat = get_catalogue()
    leads = db.scalars(select(Lead).where(Lead.outcome == "Activated").order_by(Lead.lead_id)).all()
    flagged, by_type = [], Counter()
    for lead in leads:
        bundle = parse_bundle(lead.bundle_products)
        ids = [pid for pid, _ in bundle]
        profile = Profile(segment=SEGMENT_CODES[lead.segment], employees=lead.employee_count,
                          sites=lead.num_sites, city_tier=lead.city_tier,
                          gstin_status="Active" if lead.has_gstin == "Y" else None)
        violations = [{"product_id": pid, "product": cat[pid].name, "rules": rules}
                      for pid in ids if (rules := failed_rules(cat[pid], profile, ids))]
        if violations:
            for v in violations:
                by_type.update(v["rules"])
            flagged.append({
                "lead_id": lead.lead_id, "business_type": lead.business_type, "city": lead.city,
                "city_tier": lead.city_tier, "employees": lead.employee_count, "sites": lead.num_sites,
                "has_gstin": lead.has_gstin, "gstin": mask_gstin(lead.gstin), "bundle": lead.bundle_products,
                "monthly_value": lead.monthly_bundle_value_inr, "violations": violations})
    return {"activated": len(leads), "flagged": len(flagged),
            "by_type": {RULE_LABELS[k]: v for k, v in by_type.most_common()}, "rows": flagged}
