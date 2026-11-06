from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import AdvisorSession
from ..schemas import AdvisorMessage, AdvisorStart, BundleResult, Profile
from ..services.advisor import Advisor, get_advisor
from ..services.rules_engine import recommend_bundle

router = APIRouter(prefix="/advisor", tags=["advisor"])


def _session(db: Session, session_id: str) -> AdvisorSession:
    s = db.get(AdvisorSession, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


@router.post("/sessions")
def start(body: AdvisorStart, db: Session = Depends(get_db)):
    s = AdvisorSession(language=body.language, channel=body.channel,
                       mode="ai" if get_settings().ai_mode else "guided")
    db.add(s)
    db.flush()
    out = Advisor(db, s).start()
    db.commit()
    return out


@router.post("/sessions/{session_id}/message")
def message(session_id: str, body: AdvisorMessage, db: Session = Depends(get_db)):
    s = _session(db, session_id)
    if not (body.text or body.chip):
        raise HTTPException(422, "text or chip required")
    out = get_advisor(db, s).turn((body.text or "").strip()[:500] or None, body.chip)
    db.commit()
    return out


@router.post("/sessions/{session_id}/abandon")
def abandon(session_id: str, db: Session = Depends(get_db)):
    s = _session(db, session_id)
    if s.status == "open":
        Advisor(db, s).create_lead("Abandoned chat")
        db.commit()
    return {"status": s.status}


@router.get("/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = _session(db, session_id)
    return {"id": s.id, "language": s.language, "mode": s.mode, "status": s.status,
            "profile": (s.state or {}).get("profile"), "bundle": s.bundle}


@router.post("/recommend", response_model=BundleResult)
def recommend(profile: Profile):
    return recommend_bundle(profile)
