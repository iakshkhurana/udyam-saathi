import pytest

from app.services.kyc.ocr import ocr_available
from app.services.kyc.service import EXPECTED, SAMPLES, evaluate_sample

pytestmark = pytest.mark.skipif(not ocr_available(), reason="Tesseract is not installed")


@pytest.mark.parametrize("applicant", SAMPLES)
def test_primary_flag_caught(db, applicant):
    result = evaluate_sample(db, applicant)
    assert result["flags_caught"], (applicant, [(c["id"], c["status"]) for c in result["checks"]])
    assert result["status"] == EXPECTED[applicant][0]


def test_rotated_k02_parses_after_deskew(db):
    gst = evaluate_sample(db, "K02")["docs"]["gst_certificate"]
    assert abs(gst["angle"]) >= 5 and gst["fields"]["gstin"] == "19EOGXH4115Y1ZL"


def test_k03_positional_normalisation(db):
    gst = evaluate_sample(db, "K03")["docs"]["gst_certificate"]["fields"]
    assert gst["gstin"] == "27XUIXG0767D1ZP"


def test_k06_tampered_gstin_is_not_repaired(db):
    result = evaluate_sample(db, "K06")
    assert result["docs"]["gst_certificate"]["fields"]["gstin"] == "08YKZXS8189L1Z0"
    c04 = next(c for c in result["checks"] if c["id"] == "C04")
    assert c04["status"] == "fail" and c04["evidence"]["closest_registry_gstin"] == "08••••••••••1ZO"
