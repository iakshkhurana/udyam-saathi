"""Run the rules engine over every activated bundle and write docs/rules_audit.md."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ROOT_DIR
from app.db import SessionLocal
from app.services.audit import audit_sold_bundles
from app.services.catalogue import get_catalogue
from app.services.rules_engine import rule_reason


def main() -> dict:
    with SessionLocal() as db:
        result = audit_sold_bundles(db)
    lines = [
        "# Rules audit – sold bundles vs catalogue rules",
        "",
        f"The rules engine (`backend/app/services/rules_engine.py`) re-checked all **{result['activated']}** "
        f"activated bundles in `smb_leads.csv`. **{result['flagged']}** "
        f"({result['flagged'] / result['activated']:.0%}) break at least one catalogue rule – "
        "evidence that manual quoting mis-sells and that the rules engine must be the source of truth.",
        "",
        "Profile used per lead: segment, `employee_count`, `num_sites`, `city_tier`; GSTIN counts as present when "
        "`has_gstin == 'Y'`. Dependency = a product with `requires_one_of` sold without any of those products.",
        "",
        "## Violations by type",
        "",
        "| Rule | Violations |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in result["by_type"].items()],
        "",
        "A bundle can break more than one rule, so the total exceeds the number of flagged bundles.",
        "",
        "## Flagged bundles",
        "",
        "| Lead | Business | City (tier) | Staff | Sites | GSTIN | Bundle | Violations |",
        "|---|---|---|---|---|---|---|---|",
    ]
    cat = get_catalogue()
    for r in result["rows"]:
        v = "; ".join(f"{x['product_id']}: " + rule_reason(cat[x["product_id"]], x["rules"])[0]
                      for x in r["violations"])
        lines.append(f"| {r['lead_id']} | {r['business_type']} | {r['city']} ({r['city_tier']}) | {r['employees']} "
                     f"| {r['sites']} | {r['has_gstin']} | `{r['bundle']}` | {v} |")
    (ROOT_DIR / "docs" / "rules_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT_DIR / "docs" / "rules_audit.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


if __name__ == "__main__":
    res = main()
    print(res["activated"], res["flagged"], res["by_type"])
