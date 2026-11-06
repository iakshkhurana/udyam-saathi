import base64
import hashlib
import hmac
import re

from app.config import get_settings
from app.routers.whatsapp import valid_signature

FROM = "whatsapp:+919876500001"


def send(client, body: str) -> str:
    res = client.post("/api/webhooks/whatsapp", data={"From": FROM, "Body": body, "ProfileName": "Test"})
    assert res.status_code == 200 and res.headers["content-type"].startswith("application/xml")
    return res.text


def option(reply: str, label: str) -> str:
    return re.search(rf"(\d+)\. {re.escape(label)}", reply).group(1)


def test_whatsapp_conversation_with_numbered_options(client):
    reply = send(client, "hi")
    assert "<Message>" in reply and "1. Kirana / shop" in reply
    send(client, option(reply, "Kirana / shop"))
    send(client, "2")
    reply = send(client, "1")
    reply = send(client, "Lucknow")
    reply = send(client, option(reply, "Mobile hotspot"))
    reply = send(client, option(reply, "Skip"))
    reply = send(client, option(reply, "Suggest for me"))
    reply = send(client, option(reply, "No GSTIN"))
    assert "Dukaan Digital" in reply
    reply = send(client, option(reply, "See quote"))
    assert "/quote/" in reply


def test_signature_validation(client, monkeypatch):
    params = {"From": FROM, "Body": "hi"}
    url = "http://testserver/api/webhooks/whatsapp"
    monkeypatch.setattr(get_settings(), "twilio_auth_token", "secret")
    assert client.post(url, data=params, headers={"X-Twilio-Signature": "bad"}).status_code == 403
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    sig = base64.b64encode(hmac.new(b"secret", payload.encode(), hashlib.sha1).digest()).decode()
    assert valid_signature(url, params, sig, "secret")
    assert client.post(url, data=params, headers={"X-Twilio-Signature": sig}).status_code == 200
