"""Reproduce the case's key lead insights; write docs/insights.md and PNG charts to docs/charts/."""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ROOT_DIR
from app.services.propensity import load_leads
from train_propensity import main as train_main

DOCS = ROOT_DIR / "docs"
CHARTS = DOCS / "charts"
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES_1, SERIES_2 = "#2a78d6", "#eb6834"
FUNNEL = ["Lead", "Contacted", "Needs assessed", "Quote accepted", "KYC complete", "Activated"]
STAGE_DATE = {"Contacted": "contacted_date", "Needs assessed": "needs_assessed_date",
              "Quote accepted": "quote_accepted_date", "KYC complete": "kyc_complete_date", "Activated": "activated_date"}
FIXABLE = {
    "Owner had no time for a visit": "No visit: advisor + KYC on the phone",
    "Visit not scheduled by sales": "No visit: advisor + KYC on the phone",
    "Quote too complex to understand": "One plain-language monthly price",
    "Quote took too long to arrive": "Instant quote from the rules engine",
    "Missing GST or Udyam document": "Smart KYC with fix-it messages; no-GST starter",
    "Found paperwork too long": "5-minute Smart KYC",
    "Authorised signatory not available": "Remote e-sign (Aadhaar OTP)",
    "Document details did not match": "Live document checks before submission",
}
SEGMENTS = {"Micro retail & services": "micro", "Professional offices": "prof",
            "Small multi-site businesses": "multi", "Small manufacturers": "mfg"}


def style(ax, title: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold", pad=12)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_2, length=0)
    ax.grid(axis="x" if ax.get_ylabel() == "" else "y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def save(fig, name: str) -> str:
    fig.patch.set_facecolor(SURFACE)
    fig.tight_layout()
    path = CHARTS / name
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)
    return f"charts/{name}"


def pct(x: float) -> str:
    return f"{x:.1%}"


def inr(x: float) -> str:
    return "₹" + f"{x:,.0f}"


def md_table(df: pd.DataFrame) -> list[str]:
    cols = list(df.columns)
    return ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols),
            *["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]]


def main() -> dict:
    CHARTS.mkdir(parents=True, exist_ok=True)
    df = load_leads()
    act = df[df.outcome == "Activated"]
    n_act = len(act)
    total_cost = df.acquisition_cost_inr.sum()
    churn = (act.churned_within_6_months == "Y").mean()

    funnel = [len(df)] + [int(df[col].notna().sum()) for col in STAGE_DATE.values()]
    funnel_rows = pd.DataFrame({"Stage": FUNNEL, "Leads": funnel,
                                "% of previous": ["–"] + [pct(b / a) for a, b in zip(funnel, funnel[1:])]})
    drops = [(FUNNEL[i + 1], 1 - funnel[i + 1] / funnel[i]) for i in range(len(funnel) - 1)]

    src = df.groupby("lead_source").agg(leads=("lead_id", "size"), acts=("outcome", lambda s: (s == "Activated").sum()),
                                         cost=("acquisition_cost_inr", "sum"))
    src["rate"], src["cac"] = src.acts / src.leads, src.cost / src.acts
    src = src.sort_values("rate", ascending=False)

    calls = act.groupby("customer_follow_up_calls").agg(
        customers=("lead_id", "size"), churn=("churned_within_6_months", lambda s: (s == "Y").mean()))
    gst = df.groupby("has_gstin").outcome.apply(lambda s: (s == "Activated").mean())
    seg = df.groupby("segment").agg(leads=("lead_id", "size"), acts=("outcome", lambda s: (s == "Activated").sum()),
                                    cost=("acquisition_cost_inr", "sum"), value=("monthly_bundle_value_inr", "mean"))
    seg["rate"], seg["cac"] = seg.acts / seg.leads, seg.cost / seg.acts
    seg["value_6m"] = seg.value * 6
    seg = seg.loc[list(SEGMENTS)]
    lang = df.groupby("preferred_language").agg(leads=("lead_id", "size"),
                                                 rate=("outcome", lambda s: (s == "Activated").mean())).sort_values("rate")
    dropped = df[df.outcome == "Dropped"]
    reasons = dropped.drop_reason.value_counts()
    fixable = int(reasons[list(FIXABLE)].sum())
    sold = act.bundle_products.str.split(";").explode().str.split("x").str[0].value_counts()

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(FUNNEL[::-1], funnel[::-1], color=SERIES_1, height=0.6)
    for y, v in enumerate(funnel[::-1]):
        ax.text(v + 60, y, f"{v:,}", va="center", color=INK, fontsize=9)
    style(ax, "Lead funnel, Apr–Jun 2026 (5,000 leads → 368 activations)")
    ax.set_xlim(0, max(funnel) * 1.12)
    funnel_png = save(fig, "funnel.png")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    labels = list(src.index)
    a1.barh(labels, src.rate * 100, color=SERIES_1, height=0.6)
    a2.barh(labels, src.cac, color=SERIES_1, height=0.6)
    for y, (r, c) in enumerate(zip(src.rate, src.cac)):
        a1.text(r * 100 + 0.3, y, pct(r), va="center", color=INK, fontsize=9)
        a2.text(c + 300, y, inr(c), va="center", color=INK, fontsize=9)
    a1.invert_yaxis()
    style(a1, "Activation rate by source")
    style(a2, "CAC per activation by source")
    a1.set_xlim(0, src.rate.max() * 120)
    a2.set_xlim(0, src.cac.max() * 1.25)
    a2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"₹{v / 1000:.0f}k"))
    source_png = save(fig, "source_activation_cac.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.set_ylabel("Churned within 6 months (%)", color=INK_2)
    ax.plot(calls.index, calls.churn * 100, color=SERIES_1, linewidth=2, marker="o", markersize=8)
    for x, y in zip(calls.index, calls.churn * 100):
        ax.annotate(f"{y:.0f}%", (x, y), textcoords="offset points", xytext=(0, 10), ha="center", color=INK, fontsize=9)
    ax.set_xlabel("Status-chasing calls made by the customer", color=INK_2)
    ax.set_xticks(list(calls.index))
    ax.set_ylim(0, calls.churn.max() * 125)
    style(ax, "Churn rises with status-chasing calls: 6% at 1 call, 28% at 5")
    churn_png = save(fig, "churn_by_followup_calls.png")

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.set_ylabel("₹ per activated customer", color=INK_2)
    x = range(len(seg))
    ax.bar([i - 0.2 for i in x], seg.value_6m, width=0.38, color=SERIES_1, label="6-month bundle revenue")
    ax.bar([i + 0.2 for i in x], seg.cac, width=0.38, color=SERIES_2, label="Acquisition cost (CAC)")
    ax.set_xticks(list(x), [SEGMENTS[s] for s in seg.index])
    ax.legend(frameon=False, labelcolor=INK_2, loc="upper left")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"₹{v:,.0f}"))
    style(ax, "6-month revenue vs CAC by segment")
    segment_png = save(fig, "segment_value_vs_cac.png")

    metrics_file = DOCS / "propensity_metrics.json"
    if not metrics_file.exists():
        train_main()
    model = json.loads(metrics_file.read_text(encoding="utf-8"))

    referral, field = src.loc["Referral"], src.loc["Field sales"]
    lines = [
        "# Lead insights – Accel Business SMB funnel (Apr–Jun 2026)", "",
        "Generated by `backend/scripts/analyze_leads.py` from `smb_leads.csv` (5,000 synthetic leads).", "",
        "## Headline numbers", "",
        f"- **{n_act} activations** from {len(df):,} leads → **{pct(n_act / len(df))}** lead-to-activation",
        f"- **{act.days_lead_to_activation.mean():.1f} days** from lead to activation on average; "
        f"{act.customer_follow_up_calls.mean():.1f} status-chasing calls per activated customer",
        f"- **CAC {inr(total_cost / n_act)}** per activation (total acquisition spend {inr(total_cost)})",
        f"- **6-month churn {pct(churn)}**",
        f"- Steepest drop: **needs assessed → quote accepted** – only {pct(funnel[3] / funnel[2])} accept a quote",
        f"- **{fixable:,} of {len(dropped):,} drops ({pct(fixable / len(dropped))}) are fixable** by a digital journey "
        "(visit, quote and paperwork friction)", "",
        "## Funnel", "", *md_table(funnel_rows), "", f"![Funnel]({funnel_png})", "",
        "Drop-off at each step: " + "; ".join(f"→ {s}: {pct(d)} lost" for s, d in drops) + ".", "",
        "## Lead source – activation and cost", "",
        *md_table(pd.DataFrame({"Source": src.index, "Leads": src.leads, "Activations": src.acts,
                                "Activation rate": src.rate.map(pct), "CAC": src.cac.map(inr)})), "",
        f"![Source]({source_png})", "",
        f"Referral converts at **{pct(referral.rate)}** with CAC **{inr(referral.cac)}**; field sales converts at "
        f"**{pct(field.rate)}** with CAC **{inr(field.cac)}** – about {field.cac / referral.cac:.0f}× the cost. "
        "→ The tracker's referral card and a digital-first journey attack the most expensive channel.", "",
        "## Status-chasing calls drive churn", "",
        *md_table(pd.DataFrame({"Follow-up calls": calls.index, "Activated customers": calls.customers,
                                "Churn within 6 months": calls.churn.map(pct)})), "",
        f"![Churn]({churn_png})", "",
        f"1 call → {pct(calls.churn.loc[1])} churn; 5 calls → {pct(calls.churn.loc[5])}. "
        "→ The tracker must be **proactive** (WhatsApp-style updates, delay + credit before the customer asks).", "",
        "## GSTIN", "",
        f"Leads with a GSTIN activate at **{pct(gst['Y'])}** vs **{pct(gst['N'])}** without "
        f"({(df.has_gstin == 'N').sum():,} leads have no GSTIN). → Offer a **no-GST starter bundle** "
        "(Dukaan Digital without GST-only products) and show what unlocks once a GSTIN is added.", "",
        "## Segments", "",
        *md_table(pd.DataFrame({"Segment": [SEGMENTS[s] for s in seg.index], "Leads": seg.leads, "Activations": seg.acts,
                                "Activation rate": seg.rate.map(pct), "Avg bundle ₹/month": seg.value.map(inr),
                                "6-month revenue": seg.value_6m.map(inr), "CAC": seg.cac.map(inr)})), "",
        f"![Segments]({segment_png})", "",
        "Micro shops are 54% of leads but convert at 4.1% and cost more to acquire than they pay in six months – "
        "the self-serve advisor is the only economical way to serve them.", "",
        "## Language", "",
        *md_table(pd.DataFrame({"Language": lang.index, "Leads": lang.leads, "Activation rate": lang.rate.map(pct)})), "",
        "Tamil, Punjabi and Kannada leads convert at roughly half the Hindi/English rate → **vernacular advisor** "
        "(EN/HI guided mode; all 10 languages in AI mode; voice input).", "",
        "## Drop reasons", "",
        *md_table(pd.DataFrame({"Drop reason": reasons.index, "Leads": reasons.values,
                                "Fixed by": [FIXABLE.get(r, "–") for r in reasons.index]})), "",
        f"Fixable total: **{fixable:,} of {len(dropped):,}**.", "",
        "## Mis-sold bundles", "",
        "48 of the 368 sold bundles (13%) break catalogue rules (city tier 24, GSTIN 12, dependency 9, employees 8) – "
        "see `rules_audit.md`. → The rules engine is the single source of truth for every recommendation.", "",
        "## Most-sold products", "",
        *md_table(pd.DataFrame({"Product": sold.index[:10], "Bundles": sold.values[:10]})), "",
        "## Propensity model (back office)", "",
        f"Logistic regression (one-hot categorical + log-scaled size/spend, `class_weight='balanced'`), "
        f"80/20 stratified split: **ROC-AUC {model['roc_auc']}** on the held-out 20%. "
        "Scores are shown as 0–100 (Hot ≥ 70, Warm 40–69, Cold < 40).", "",
        "| Feature | Coefficient |", "|---|---|",
        *[f"| {name} | {coef:+.3f} |" for name, coef in model["top_coefficients"]], "",
    ]
    (DOCS / "insights.md").write_text("\n".join(lines), encoding="utf-8")
    return {"activations": n_act, "cac": round(total_cost / n_act), "churn": round(churn, 3),
            "referral": (round(referral.rate, 3), round(referral.cac)), "field": (round(field.rate, 3), round(field.cac)),
            "gstin": (round(gst["Y"], 3), round(gst["N"], 3)), "segments": seg.rate.round(3).to_dict(),
            "fixable": (fixable, len(dropped)), "churn_calls": calls.churn.round(2).to_dict(), "auc": model["roc_auc"]}


if __name__ == "__main__":
    print(main())
