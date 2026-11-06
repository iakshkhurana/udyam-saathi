from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AdvisorSession, Order
from ..schemas import Nps, Referral
from ..services import tracker
from ..services.storage import audit
from ..utils.masking import mask_phone

router = APIRouter(tags=["orders"])


def _order(db: Session, order_id: str) -> Order:
    order = db.get(Order, order_id.upper())
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.get("/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    return tracker.tracker_view(_order(db, order_id))


@router.post("/orders/{order_id}/advance")
def advance(order_id: str, db: Session = Depends(get_db)):
    order = _order(db, order_id)
    try:
        tracker.advance(order)
    except ValueError as e:
        raise HTTPException(409, str(e))
    db.commit()
    return tracker.tracker_view(order)


@router.post("/orders/{order_id}/delay")
def delay(order_id: str, db: Session = Depends(get_db)):
    order = _order(db, order_id)
    try:
        tracker.delay(order)
    except ValueError as e:
        raise HTTPException(409, str(e))
    db.commit()
    return tracker.tracker_view(order)


@router.post("/orders/{order_id}/nps")
def nps(order_id: str, body: Nps, db: Session = Depends(get_db)):
    order = _order(db, order_id)
    if order.status != "ACTIVATED":
        raise HTTPException(409, "NPS opens after activation")
    order.nps = body.score
    db.commit()
    return {"ok": True, "nps": order.nps}


@router.post("/referrals")
def referral(body: Referral, db: Session = Depends(get_db)):
    order = _order(db, body.order_id)
    lead = AdvisorSession(channel="referral", status="lead", language=order.language,
                          close_reason=f"Referred by order {order.id}",
                          state={"referral": {"business_name": body.business_name[:120], "phone": body.phone[-10:]}})
    db.add(lead)
    audit(db, "customer", "referral_created", order.id, phone=mask_phone(body.phone))
    db.commit()
    return {"ok": True, "referral_id": lead.id}
