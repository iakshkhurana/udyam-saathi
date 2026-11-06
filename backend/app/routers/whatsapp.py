import base64
import hashlib
import hmac
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import AdvisorSession
from ..services.advisor import Advisor, get_advisor
from ..services.quote import create_quote
from ..utils.masking import hash_ip

router = APIRouter(prefix="/webhooks", tags=["whatsapp"])
RESTART = {"hi", "hello", "restart", "start", "namaste", "menu"}


def valid_signature(url: str, params: dict, signature: str, token: str) -> bool:
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    expected = base64.b64encode(hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(expected, signature)


def twiml(text: str) -> Response:
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(text)}</Message></Response>',
                    media_type="application/xml")


def render(out: dict) -> str:
    lines = [out["reply"]]
    if out["chips"]:
        lines.append("")
        lines += [f"{n}. {c['label']}" for n, c in enumerate(out["chips"], 1)]
        lines.append("Reply with a number, or type your answer.")
    return "\n".join(lines)


@router.post("/whatsapp")
async def whatsapp(request: Request, db: Session = Depends(get_db)):
    form = dict(await request.form())
    settings = get_settings()
    if settings.twilio_auth_token and not valid_signature(
            str(request.url), form, request.headers.get("X-Twilio-Signature", ""), settings.twilio_auth_token):
        raise HTTPException(403, "Invalid Twilio signature")
    sender, body = str(form.get("From", "")), str(form.get("Body", "")).strip()
    if not sender:
        raise HTTPException(422, "From is required")
    session_id = hash_ip(sender, "whatsapp")[:8].upper()
    session = db.get(AdvisorSession, session_id)

    if session is None or body.lower() in RESTART or session.status != "open":
        if session:
            db.delete(session)
            db.flush()
        session = AdvisorSession(id=session_id, language="hi" if body.lower() == "namaste" else "en",
                                 channel="whatsapp", mode="ai" if settings.ai_mode else "guided")
        db.add(session)
        db.flush()
        out = Advisor(db, session).start()
    else:
        chips = (session.state or {}).get("wa_chips", [])
        chip = chips[int(body) - 1]["value"] if body.isdigit() and 0 < int(body) <= len(chips) else None
        if chip == "action:quote":
            q = create_quote(db, session.id, None)
            db.commit()
            return twiml(f"Your quote {q.id}: {settings.frontend_origin.split(',')[0]}/quote/{q.id}\n"
                         "Open it to switch add-ons on/off and accept.")
        out = get_advisor(db, session).turn(None if chip else body, chip)
    session.state = {**session.state, "wa_chips": out["chips"]}
    db.commit()
    return twiml(render(out))
