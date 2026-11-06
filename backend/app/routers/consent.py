from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Consent, Order
from ..schemas import ConsentCreate
from ..services.storage import audit
from ..services.tracker import set_status
from ..utils.masking import hash_ip

router = APIRouter(tags=["consent"])
NOTICE_VERSION = "v1.0"


def active_consent(db: Session, order_id: str) -> Consent | None:
    consents = db.scalars(select(Consent).where(Consent.order_id == order_id, Consent.withdrawn_at.is_(None)))
    return next((c for c in consents if "kyc_verification" in c.purposes), None)


def require_consent(order_id: str, db: Session = Depends(get_db)) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if not active_consent(db, order_id):
        raise HTTPException(403, "KYC consent is required before uploading documents")
    return order


@router.post("/consents")
def give_consent(body: ConsentCreate, request: Request, db: Session = Depends(get_db)):
    order = db.get(Order, body.order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if not body.kyc:
        raise HTTPException(422, "KYC verification consent is required to continue")
    purposes = ["kyc_verification", "installation_address_sharing"]
    if body.marketing_whatsapp:
        purposes.append("product_updates_whatsapp")
    consent = Consent(order_id=order.id, purposes=purposes, notice_version=NOTICE_VERSION, language=body.language,
                      ip_hash=hash_ip(request.client.host if request.client else None))
    db.add(consent)
    if order.status == "QUOTE_ACCEPTED":
        set_status(order, "CONSENT_GIVEN")
    audit(db, "customer", "consent_given", order.id, purposes=purposes, notice_version=NOTICE_VERSION)
    db.commit()
    return {"order_id": order.id, "purposes": purposes, "notice_version": NOTICE_VERSION,
            "created_at": consent.created_at.isoformat()}
