from datetime import datetime, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import AdvisorSession, KycSubmission, Lead, Order
from ..schemas import KycDecision, Profile
from ..services.audit import audit_sold_bundles
from ..services.data_loader import SEGMENT_CODES
from ..services.kyc.service import submission_view
from ..services.propensity import CATEGORICAL, NUMERIC, action, label, score_frame, score_profile
from ..services.storage import audit
from ..services.tracker import set_status

ABANDON_AFTER = timedelta(minutes=30)


def require_pin(x_backoffice_pin: str = Header("")) -> None:
    if x_backoffice_pin != get_settings().backoffice_pin:
        raise HTTPException(401, "Back-office PIN required")


router = APIRouter(prefix="/backoffice", tags=["backoffice"], dependencies=[Depends(require_pin)])


def ensure_lead_scores(db: Session) -> None:
    leads = db.scalars(select(Lead).where(Lead.propensity.is_(None))).all()
    if not leads:
        return
    df = pd.DataFrame([{c: getattr(lead, c) for c in CATEGORICAL + NUMERIC} for lead in leads])
    for lead, score in zip(leads, score_frame(df)):
        lead.propensity = float(score)
    db.commit()


@router.get("/sessions")
def sessions(db: Session = Depends(get_db)):
    stale = datetime.now() - ABANDON_AFTER
    rows = db.scalars(select(AdvisorSession).where(or_(
        AdvisorSession.status == "lead",
        (AdvisorSession.status == "open") & (AdvisorSession.updated_at < stale))).order_by(
        AdvisorSession.updated_at.desc())).all()
    out = []
    for s in rows:
        state = s.state or {}
        profile = Profile(**state["profile"]) if "profile" in state else Profile()
        score = s.propensity if s.propensity is not None else score_profile(profile)
        reason = s.close_reason or "Abandoned chat"
        if s.channel == "referral":
            reason, profile_view = s.close_reason, {"referral": state.get("referral", {}).get("business_name")}
        else:
            profile_view = {k: v for k, v in profile.model_dump().items()
                            if k in ("business_type", "segment", "employees", "sites", "city", "needs", "gstin_status")}
        out.append({"id": s.id, "created_at": s.created_at.isoformat(), "channel": s.channel, "language": s.language,
                    "reason": reason, "score": round(score, 1), "label": label(score),
                    "action": action(score, profile.segment, profile.gstin_active), "profile": profile_view,
                    "bundle_name": (s.bundle or {}).get("bundle_name"), "monthly_total": (s.bundle or {}).get("monthly_total")})
    return sorted(out, key=lambda r: -r["score"])


@router.get("/leads")
def leads(segment: str = "", city: str = "", source: str = "", limit: int = 100, db: Session = Depends(get_db)):
    ensure_lead_scores(db)
    q = select(Lead).where(Lead.outcome == "Dropped")
    if segment:
        q = q.where(Lead.segment == next((k for k, v in SEGMENT_CODES.items() if v == segment), segment))
    if city:
        q = q.where(Lead.city == city)
    if source:
        q = q.where(Lead.lead_source == source)
    rows = db.scalars(q.order_by(Lead.propensity.desc()).limit(min(limit, 500))).all()
    return [{"lead_id": r.lead_id, "business_type": r.business_type, "segment": SEGMENT_CODES[r.segment],
             "city": r.city, "lead_source": r.lead_source, "language": r.preferred_language,
             "employees": r.employee_count, "has_gstin": r.has_gstin, "drop_reason": r.drop_reason,
             "stage_reached": r.stage_reached, "score": r.propensity, "label": label(r.propensity),
             "action": action(r.propensity, SEGMENT_CODES[r.segment], r.has_gstin == "Y")} for r in rows]


@router.get("/kyc-queue")
def kyc_queue(db: Session = Depends(get_db)):
    subs = db.scalars(select(KycSubmission).join(Order, Order.id == KycSubmission.order_id).where(
        Order.status == "KYC_REVIEW", KycSubmission.reviewer_decision.is_(None))).all()
    out = []
    for sub in subs:
        view = submission_view(sub)
        gst = view["documents"].get("gst_certificate", {}).get("fields", {})
        out.append({"order_id": sub.order_id, "status": sub.status, "business": gst.get("trade_name"),
                    "gstin": view["typed_gstin"], "warnings": [c for c in view["checks"] if c["status"] == "warn"],
                    "updated_at": sub.updated_at.isoformat()})
    return out


@router.post("/kyc/{order_id}/decision")
def decision(order_id: str, body: KycDecision, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    sub = db.scalar(select(KycSubmission).where(KycSubmission.order_id == order_id))
    if not order or not sub or order.status != "KYC_REVIEW":
        raise HTTPException(404, "Nothing to review for this order")
    sub.reviewer_decision = body.decision
    if body.decision == "approve":
        sub.status = "PASS"
        set_status(order, "KYC_VERIFIED")
    else:
        sub.status = "FAIL"
        set_status(order, "CONSENT_GIVEN")
    audit(db, "reviewer", f"kyc_{body.decision}", order_id)
    db.commit()
    return {"order_id": order_id, "decision": body.decision, "order_status": order.status}


@router.get("/kyc/{order_id}/full")
def full_view(order_id: str, db: Session = Depends(get_db)):
    sub = db.scalar(select(KycSubmission).where(KycSubmission.order_id == order_id))
    if not sub:
        raise HTTPException(404, "No KYC submission")
    audit(db, "reviewer", "full_identifiers_viewed", order_id)
    db.commit()
    gst = next((d.fields for d in sub.documents if d.doc_type == "gst_certificate"), {})
    sig = next((d.fields for d in sub.documents if d.doc_type == "signatory_id"), {})
    return {"typed_gstin": sub.typed_gstin or "", "typed_udyam": sub.typed_udyam or "",
            "certificate_gstin": gst.get("gstin", ""), "signatory_name": sig.get("name", ""),
            "signatory_id": sig.get("id_no", "")}


@router.get("/rules-audit")
def rules_audit(db: Session = Depends(get_db)):
    return audit_sold_bundles(db)
