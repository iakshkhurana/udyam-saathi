import logging
import re
from datetime import date

import pytest

from app.config import BACKEND_DIR
from app.schemas import Profile
from app.services.kyc.ocr import ocr_available
from app.services.tracker import add_days_skip_sundays

needs_ocr = pytest.mark.skipif(not ocr_available(), reason="Tesseract is not installed")
RAW_GSTIN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")
RAW_UDYAM = re.compile(r"UDYAM-[A-Z]{2}-\d{2}-\d{7}")
RAW_PHONE = re.compile(r"(?<!\d)[6-9]\d{9}(?!\d)")


def new_order(client, **profile) -> str:
    p = Profile(segment="micro", employees=3, needs=["cctv", "pos"], **profile).model_dump()
    q = client.post("/api/quotes", json={"profile": p}).json()
    return client.post(f"/api/quotes/{q['id']}/accept").json()["id"]


def consent(client, order_id: str):
    return client.post("/api/consents", json={"order_id": order_id, "kyc": True, "language": "en"})


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["mode"] == "Guided" and body["today"] == "2026-07-15"


def test_full_guided_journey_to_quote(client):
    sid = client.post("/api/advisor/sessions", json={"language": "hi"}).json()["session_id"]
    for chip in ["bt:Kirana store", "emp:1", "sites:1", "city:Lucknow", "net:Mobile hotspot", "spend:800",
                 "needs:none", "gst:none"]:
        out = client.post(f"/api/advisor/sessions/{sid}/message", json={"chip": chip}).json()
    assert out["bundle"]["bundle_name"].startswith("Dukaan Digital")
    q = client.post("/api/quotes", json={"session_id": sid}).json()
    assert q["monthly_total"] == out["bundle"]["monthly_total"] and "wa.me" in q["whatsapp_url"]


def test_quote_toggle_base_removes_dependents(client):
    q = client.post("/api/quotes", json={"profile": Profile(needs=["cctv"]).model_dump()}).json()
    out = client.patch(f"/api/quotes/{q['id']}", json={"items": [{"product_id": "P01", "enabled": False}]}).json()
    assert not next(i for i in out["items"] if i["product_id"] == "P23")["enabled"] and out["warnings_en"]
    out = client.patch(f"/api/quotes/{q['id']}", json={"items": [{"product_id": "P22", "enabled": True, "qty": 1},
                                                                 {"product_id": "P01", "enabled": True}]}).json()
    assert next(i for i in out["items"] if i["product_id"] == "P22")["enabled"]


def test_kyc_refused_without_consent(client):
    oid = new_order(client)
    assert client.post(f"/api/kyc/{oid}/identifiers", json={"gstin": "27XUIXG0767D1ZP"}).status_code == 403
    files = {"file": ("x.png", b"123", "image/png")}
    assert client.post(f"/api/kyc/{oid}/documents/gst_certificate", files=files).status_code == 403
    assert client.post(f"/api/kyc/{oid}/load-sample/K03").status_code == 403
    assert consent(client, oid).status_code == 200
    card = client.post(f"/api/kyc/{oid}/identifiers", json={"gstin": "27XUIXG0767D1ZP"}).json()["gstin"]
    assert card["trade_name"] == "Ganesh Woodcraft" and card["status"] == "Active"


@needs_ocr
def test_kyc_k03_passes_and_order_moves_on(client):
    oid = new_order(client)
    consent(client, oid)
    view = client.post(f"/api/kyc/{oid}/load-sample/K03").json()
    assert all(d["status"] == "pass" for d in view["documents"].values())
    assert view["typed_gstin"] == "27••••••••••1ZP"
    assert client.post(f"/api/kyc/{oid}/esign", json={"otp": "000000"}).status_code == 422
    assert client.post(f"/api/kyc/{oid}/esign", json={"otp": "123456"}).json()["esigned"]
    out = client.post(f"/api/kyc/{oid}/verify").json()
    assert out["status"] == "PASS" and out["order"]["status"] == "KYC_VERIFIED"


@needs_ocr
def test_kyc_k01_fails_with_fix_messages(client):
    oid = new_order(client)
    consent(client, oid)
    client.post(f"/api/kyc/{oid}/load-sample/K01")
    out = client.post(f"/api/kyc/{oid}/verify").json()
    assert out["status"] == "FAIL" and out["order"]["status"] == "CONSENT_GIVEN"
    failed = {c["id"] for c in out["checks"] if c["status"] == "fail"}
    assert {"C05", "C09"} <= failed and all(c["message_hi"] for c in out["checks"])


@needs_ocr
def test_kyc_warnings_go_to_review_queue(client):
    oid = new_order(client)
    consent(client, oid)
    client.post(f"/api/kyc/{oid}/load-sample/K08")
    out = client.post(f"/api/kyc/{oid}/verify").json()
    assert out["order"]["status"] == "KYC_REVIEW"


def test_tracker_advance_delay_activate_nps_referral(client):
    oid = new_order(client)
    consent(client, oid)
    for _ in range(2):
        client.post(f"/api/orders/{oid}/advance")
    t = client.post(f"/api/orders/{oid}/delay").json()
    assert t["delay"]["credit_inr"] == 100 and t["credit_inr"] == 100
    assert t["notifications"][-1]["status"] == "DELAYED" and "credit" in t["notifications"][-1]["message_en"]
    assert client.post(f"/api/orders/{oid}/nps", json={"score": 9}).status_code == 409
    for _ in range(2):
        t = client.post(f"/api/orders/{oid}/advance").json()
    assert t["status"] == "ACTIVATED" and t["progress"] == 100
    assert client.post(f"/api/orders/{oid}/advance").status_code == 409
    assert client.post(f"/api/orders/{oid}/nps", json={"score": 10}).json()["nps"] == 10
    assert client.post("/api/referrals", json={"order_id": oid, "business_name": "Sharma Sweets",
                                               "phone": "9876543210"}).json()["ok"]


def test_install_date_skips_sundays():
    assert add_days_skip_sundays(date(2026, 7, 15), 5) == date(2026, 7, 21)


@needs_ocr
def test_privacy_delete_and_withdraw(client):
    oid = new_order(client)
    consent(client, oid)
    client.post(f"/api/kyc/{oid}/load-sample/K12")
    held = client.get(f"/api/privacy/{oid}").json()
    assert all(d["stored"] for d in held["documents"]) and "•" in held["gstin"]
    assert client.delete(f"/api/privacy/data/{oid}").json()["documents_deleted"] == 4
    out = client.post("/api/privacy/withdraw", json={"order_id": oid}).json()
    assert out["order_status"] == "CANCELLED"
    assert client.post(f"/api/kyc/{oid}/identifiers", json={}).status_code == 403


def test_retention_job(client):
    assert "documents_deleted" in client.post("/api/admin/run-retention").json()


def test_no_unmasked_identifiers_in_logs(client):
    logging.getLogger("app.test").info("lookup 27XUIXG0767D1ZP UDYAM-MH-00-6131836 phone 9876543210 SYN-ID-123456")
    client.get("/api/gstin/27XUIXG0767D1ZP")
    for h in logging.getLogger().handlers:
        h.flush()
    text = (BACKEND_DIR / "logs" / "app.log").read_text(encoding="utf-8")
    assert "27••••••••••1ZP" in text
    assert not RAW_GSTIN.search(text) and not RAW_UDYAM.search(text) and not RAW_PHONE.search(text)
    assert "SYN-ID-123456" not in text
