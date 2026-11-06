import csv

import pytest

from app.config import get_settings
from app.utils.masking import mask_gstin, mask_name, mask_phone, mask_text, mask_udyam
from app.utils.validators import gstin_valid, normalise_gstin, normalise_udyam, udyam_valid


def test_every_registry_gstin_is_valid():
    with open(get_settings().data_path / "mock_gstin_registry.csv", encoding="utf-8") as f:
        assert all(gstin_valid(r["gstin"]) for r in csv.DictReader(f))


@pytest.mark.parametrize("g", ["08YKZXS8189L1Z0", "27QHIXK0658U1ZL", "27XUIXG0767D1ZQ", "27XUIXG0767D1Z"])
def test_tampered_gstins_fail(g):
    assert not gstin_valid(normalise_gstin(g))


def test_ocr_variant_normalises_and_passes():
    assert normalise_gstin("27XUIXGO767D1ZP") == "27XUIXG0767D1ZP"
    assert gstin_valid(normalise_gstin("27 XUIXG-O767 D1ZP"))


def test_normalisation_never_repairs_checksum():
    assert normalise_gstin("08YKZXS8189L1Z0") == "08YKZXS8189L1Z0"


@pytest.mark.parametrize("raw,expected", [
    ("UDYAM-MH- 00-6131836", "UDYAM-MH-00-6131836"),
    ("UDYAM- PB-00-9719478", "UDYAM-PB-00-9719478"),
    ("udyam-kl-00-55218 86", "UDYAM-KL-00-5521886"),
])
def test_udyam_normalises(raw, expected):
    assert normalise_udyam(raw) == expected
    assert udyam_valid(normalise_udyam(raw))


def test_masking():
    assert mask_gstin("27XUIXG0767D1ZP") == "27••••••••••1ZP"
    assert mask_udyam("UDYAM-MH-00-6136696") == "UDYAM-MH-00-•••6696"
    assert mask_phone("9876543210") == "98•••••210"
    assert mask_name("Jaya Sharma") == "J. S."
    line = mask_text("27XUIXG0767D1ZP UDYAM-MH-00-6131836 9876543210 SYN-ID-123456")
    assert "27XUIXG0767D1ZP" not in line and "6131836" not in line and "9876543210" not in line
    assert "123456" not in line


def test_gstin_api(client):
    ok = client.get("/api/gstin/37IHKXV5167L1ZS").json()
    assert ok["found"] and ok["status"] == "Cancelled" and ok["gstin_masked"] == "37••••••••••1ZS"
    assert client.get("/api/gstin/08YKZXS8189L1Z0").json()["status"] == "Invalid"
    assert client.get("/api/udyam/UDYAM-KL-00-5521886").json()["found"]
    assert len(client.get("/api/products").json()) == 25
