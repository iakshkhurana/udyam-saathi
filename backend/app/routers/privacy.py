from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Consent, KycSubmission, Order
from ..schemas import Withdraw
from ..services.storage import audit, delete_order_documents, run_retention
from ..services.tracker import cancel
from ..utils.masking import mask_gstin, mask_udyam

router = APIRouter(tags=["privacy"])


def _order(db: Session, order_id: str) -> Order:
    order = db.get(Order, order_id.upper())
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.get("/privacy/{order_id}")
def what_we_hold(order_id: str, db: Session = Depends(get_db)):
    order = _order(db, order_id)
    sub = db.scalar(select(KycSubmission).where(KycSubmission.order_id == order.id))
    consents = db.scalars(select(Consent).where(Consent.order_id == order.id)).all()
    return {
        "order_id": order.id, "status": order.status,
        "gstin": mask_gstin(sub.typed_gstin) if sub else None,
        "udyam": mask_udyam(sub.typed_udyam) if sub else None,
        "documents": [{"type": d.doc_type, "stored": bool(d.storage_key), "uploaded": d.created_at.isoformat()}
                      for d in (sub.documents if sub else [])],
        "kyc_result": sub.status if sub else None,
        "consents": [{"purposes": c.purposes, "given": c.created_at.isoformat(),
                      "withdrawn": c.withdrawn_at.isoformat() if c.withdrawn_at else None} for c in consents],
        "retention_en": "Documents are deleted 90 days after activation, or immediately if the order is cancelled.",
        "retention_hi": "दस्तावेज़ चालू होने के 90 दिन बाद, या ऑर्डर रद्द होते ही, हटा दिए जाते हैं।",
    }


@router.post("/privacy/withdraw")
def withdraw(body: Withdraw, db: Session = Depends(get_db)):
    order = _order(db, body.order_id)
    for c in db.scalars(select(Consent).where(Consent.order_id == order.id, Consent.withdrawn_at.is_(None))):
        c.withdrawn_at = datetime.now()
    deleted = delete_order_documents(db, order.id, "consent_withdrawn")
    if order.status != "ACTIVATED" and not order.cancelled:
        cancel(order)
    audit(db, "customer", "consent_withdrawn", order.id, documents_deleted=deleted)
    db.commit()
    return {"ok": True, "documents_deleted": deleted, "order_status": order.status}


@router.delete("/privacy/data/{order_id}")
def delete_data(order_id: str, db: Session = Depends(get_db)):
    order = _order(db, order_id)
    deleted = delete_order_documents(db, order.id, "erasure_request")
    audit(db, "customer", "erasure_request", order.id, documents_deleted=deleted)
    db.commit()
    return {"ok": True, "documents_deleted": deleted}


@router.post("/admin/run-retention")
def retention(db: Session = Depends(get_db)):
    result = run_retention(db)
    db.commit()
    return result
