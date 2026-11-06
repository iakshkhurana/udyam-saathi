from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Quote
from ..schemas import QuoteCreate, QuotePatch
from ..services import quote as svc
from ..services.rules_engine import IneligibleBundleError
from ..services.tracker import create_order, tracker_view

router = APIRouter(prefix="/quotes", tags=["quote"])


def _quote(db: Session, quote_id: str) -> Quote:
    q = db.get(Quote, quote_id)
    if not q:
        raise HTTPException(404, "Quote not found")
    return q


@router.post("")
def create(body: QuoteCreate, db: Session = Depends(get_db)):
    try:
        q = svc.create_quote(db, body.session_id, body.profile)
    except LookupError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    db.commit()
    return svc.quote_view(q)


@router.get("/{quote_id}")
def get(quote_id: str, db: Session = Depends(get_db)):
    return svc.quote_view(_quote(db, quote_id))


@router.patch("/{quote_id}")
def patch(quote_id: str, body: QuotePatch, db: Session = Depends(get_db)):
    q = _quote(db, quote_id)
    if q.status != "draft":
        raise HTTPException(409, "Quote already accepted")
    try:
        warnings = svc.patch_quote(q, body)
    except LookupError as e:
        raise HTTPException(404, str(e))
    except IneligibleBundleError as e:
        db.rollback()
        raise HTTPException(422, str(e))
    db.commit()
    return svc.quote_view(q, warnings)


@router.post("/{quote_id}/accept")
def accept(quote_id: str, db: Session = Depends(get_db)):
    q = _quote(db, quote_id)
    if q.status != "draft":
        raise HTTPException(409, "Quote already accepted")
    view = svc.quote_view(q)
    if not any(i["enabled"] for i in view["items"]):
        raise HTTPException(422, "Quote has no items")
    order = create_order(db, q, view)
    db.commit()
    return tracker_view(order)
