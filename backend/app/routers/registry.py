from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..limiter import limiter
from ..services import registry
from ..services.catalogue import get_catalogue

router = APIRouter(tags=["registry"])


@router.get("/gstin/{gstin}")
@limiter.limit("30/minute")
def gstin_lookup(request: Request, gstin: str, db: Session = Depends(get_db)):
    return registry.lookup_gstin(db, gstin)


@router.get("/udyam/{udyam}")
@limiter.limit("30/minute")
def udyam_lookup(request: Request, udyam: str, db: Session = Depends(get_db)):
    return registry.lookup_udyam(db, udyam)


@router.get("/products")
def products():
    return [p.as_dict() for p in get_catalogue().values()]
