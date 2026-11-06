from urllib.parse import quote as urlquote

from sqlalchemy.orm import Session

from ..models import AdvisorSession, Quote, QuoteItem
from ..schemas import BundleItem, BundleResult, Profile, QuotePatch
from .catalogue import get_catalogue
from .rules_engine import enforce_dependencies, inr, recommend_bundle, summarise


def create_quote(db: Session, session_id: str | None, profile: Profile | None) -> Quote:
    if session_id:
        session = db.get(AdvisorSession, session_id)
        if not session:
            raise LookupError("Advisor session not found")
        profile = Profile(**session.state["profile"])
        session.status = "quoted"
    if profile is None:
        raise ValueError("session_id or profile required")
    bundle = recommend_bundle(profile)
    q = Quote(session_id=session_id, profile=profile.model_dump(), bundle_name=bundle.bundle_name)
    q.items = [QuoteItem(position=n, product_id=i.product_id, qty=i.qty, enabled=i.enabled, optional=i.optional,
                         reason_en=i.reason_en, reason_hi=i.reason_hi) for n, i in enumerate(bundle.items)]
    db.add(q)
    db.flush()
    return q


def _bundle_items(q: Quote) -> list[BundleItem]:
    cat = get_catalogue()
    base_ids = {"P01", "P02", "P03", "P04", "P05", "P06"}
    return [BundleItem(product_id=i.product_id, name=cat[i.product_id].name, category=cat[i.product_id].category,
                       unit=cat[i.product_id].unit, qty=i.qty, unit_price=cat[i.product_id].price_min, monthly=0,
                       setup=0, reason_en=i.reason_en, reason_hi=i.reason_hi, optional=i.optional, enabled=i.enabled,
                       is_base=i.product_id in base_ids and not i.optional) for i in q.items]


def share_text(q: Quote, bundle: BundleResult) -> str:
    lines = [f"Udyam Saathi quote {q.id} – {bundle.bundle_name}"]
    lines += [f"• {i.name} ×{i.qty}: {inr(i.monthly)}/mo" for i in bundle.items if i.enabled]
    lines += [f"Total: {inr(bundle.monthly_total)}/month + GST", f"One-time setup: {inr(bundle.setup_total)}",
              f"Contract: {bundle.contract_months} months"]
    return "\n".join(lines)


def quote_view(q: Quote, warnings: list[tuple[str, str]] = ()) -> dict:
    profile = Profile(**q.profile)
    bundle = summarise(profile, _bundle_items(q), q.bundle_name or "Your bundle")
    text = share_text(q, bundle)
    return {"id": q.id, "status": q.status, "session_id": q.session_id, "language": profile.language,
            **bundle.model_dump(), "warnings_en": [w[0] for w in warnings], "warnings_hi": [w[1] for w in warnings],
            "share_text": text, "whatsapp_url": f"https://wa.me/?text={urlquote(text)}"}


def patch_quote(q: Quote, patch: QuotePatch) -> list[tuple[str, str]]:
    by_id = {i.product_id: i for i in q.items}
    for p in patch.items:
        item = by_id.get(p.product_id)
        if not item:
            raise LookupError(f"{p.product_id} is not in this quote")
        if p.enabled is not None:
            item.enabled = p.enabled
        if p.qty is not None:
            item.qty = p.qty
    items = _bundle_items(q)
    warnings = enforce_dependencies(items, Profile(**q.profile))
    for bi in items:
        by_id[bi.product_id].enabled = bi.enabled
    summarise(Profile(**q.profile), items, q.bundle_name or "")
    return warnings
