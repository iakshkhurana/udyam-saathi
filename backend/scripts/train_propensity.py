"""Train the lead propensity model, save it, score every lead and write docs/propensity_metrics.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ROOT_DIR
from app.db import SessionLocal
from app.models import Lead
from app.routers.backoffice import ensure_lead_scores
from app.services.propensity import MODEL_PATH, train


def main() -> dict:
    metrics = train()
    with SessionLocal() as db:
        db.query(Lead).update({Lead.propensity: None})
        db.commit()
        ensure_lead_scores(db)
    (ROOT_DIR / "docs" / "propensity_metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    m = main()
    print(f"ROC-AUC {m['roc_auc']} – model saved to {MODEL_PATH}")
    for name, coef in m["top_coefficients"]:
        print(f"{coef:+.3f}  {name}")
