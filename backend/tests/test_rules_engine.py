import random

import pytest

from app.schemas import BundleItem, Profile
from app.services.audit import audit_sold_bundles
from app.services.catalogue import get_catalogue
from app.services.rules_engine import (NEEDS, IneligibleBundleError, enforce_dependencies, failed_rules,
                                       recommend_bundle, validate)

CAT = get_catalogue()


def random_profile(rng: random.Random) -> Profile:
    return Profile(
        segment=rng.choice(["micro", "prof", "multi", "mfg"]),
        employees=rng.choice([1, 2, 3, 4, 5, 6, 9, 10, 11, 24, 25, 40, 120]),
        sites=rng.choice([1, 1, 2, 3, 4, 8]),
        city_tier=rng.choice([1, 2]),
        gstin_status=rng.choice([None, "Active", "Active", "Cancelled", "Suspended", "Invalid"]),
        needs=rng.sample(NEEDS, rng.randint(0, 5)),
        requested_products=rng.sample(list(CAT), rng.randint(0, 3)),
        current_spend=rng.choice([None, 500, 3000, 20000]),
        vehicles=rng.randint(1, 10),
        no_fibre=rng.random() < 0.2,
        mobile_only=rng.random() < 0.05,
        cheapest=rng.random() < 0.05,
    )


def test_never_returns_ineligible_item_across_500_profiles():
    rng = random.Random(2026)
    for _ in range(500):
        profile = random_profile(rng)
        result = recommend_bundle(profile)
        ids = [i.product_id for i in result.items]
        for item in result.items:
            assert not failed_rules(CAT[item.product_id], profile, ids), (profile, item.product_id)
        assert result.monthly_total == sum(i.monthly for i in result.items if i.enabled)
        assert not set(result.unlocks_with_gstin) & {i.product_id for i in result.items if i.enabled}


def test_validate_raises_on_ineligible_item():
    profile = Profile(segment="micro", employees=2, city_tier=2)
    p = CAT["P03"]
    item = BundleItem(product_id="P03", name=p.name, category=p.category, unit=p.unit, qty=1, unit_price=p.price_min,
                      monthly=p.price_min, setup=0, reason_en="", reason_hi="")
    with pytest.raises(IneligibleBundleError):
        validate([item], profile)


def test_turning_off_base_removes_dependents():
    profile = Profile(segment="micro", employees=2, needs=["cctv"])
    items = recommend_bundle(profile).items
    next(i for i in items if i.is_base).enabled = False
    warnings = enforce_dependencies(items, profile)
    assert not next(i for i in items if i.product_id == "P23").enabled
    assert warnings


def test_prices_use_min_and_setup_per_unit():
    r = recommend_bundle(Profile(segment="multi", employees=40, sites=4, city_tier=1, gstin_status="Active"))
    cctv = next(i for i in r.items if i.product_id == "P23")
    assert cctv.qty == 8 and cctv.unit_price == 199 and cctv.setup == 1800 * 8
    assert r.contract_months == 24 and r.install_days == 14


def test_audit_reproduces_48_missold_bundles(db):
    result = audit_sold_bundles(db)
    assert result["activated"] == 368
    assert result["flagged"] == 48
    assert result["by_type"] == {"city tier": 24, "GSTIN": 12, "dependency": 9, "employees": 8}
