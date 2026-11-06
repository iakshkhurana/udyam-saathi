from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from ..config import BACKEND_DIR, get_settings
from ..schemas import Profile
from .data_loader import SEGMENT_CODES

MODEL_PATH = BACKEND_DIR / "models" / "propensity.joblib"
CATEGORICAL = ["segment", "lead_source", "city_tier", "preferred_language", "has_gstin", "has_udyam",
               "current_internet", "annual_turnover_band"]
NUMERIC = ["employee_count", "num_sites", "monthly_telecom_spend_inr"]
SEGMENT_NAMES = {v: k for k, v in SEGMENT_CODES.items()}
LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
                  "gu": "Gujarati", "bn": "Bengali", "pa": "Punjabi", "ml": "Malayalam"}


def _log_features(x):
    x = np.asarray(x, dtype=float).copy()
    x[:, [0, 2]] = np.log1p(x[:, [0, 2]])
    return x


def build_pipeline() -> Pipeline:
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", Pipeline([("log", FunctionTransformer(_log_features, feature_names_out="one-to-one")), ("scale", StandardScaler())]), NUMERIC),
    ])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(class_weight="balanced", max_iter=2000))])


def load_leads() -> pd.DataFrame:
    return pd.read_csv(get_settings().data_path / "smb_leads.csv", keep_default_na=False, na_values=[""])


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    x = df[CATEGORICAL + NUMERIC].copy()
    x["city_tier"] = x["city_tier"].astype(str)
    return x


def train(df: pd.DataFrame | None = None) -> dict:
    df = load_leads() if df is None else df
    x, y = prepare(df), (df["outcome"] == "Activated").astype(int)
    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.2, stratify=y, random_state=42)
    pipe = build_pipeline().fit(x_tr, y_tr)
    auc = roc_auc_score(y_te, pipe.predict_proba(x_te)[:, 1])
    pipe.fit(x, y)
    names = pipe.named_steps["pre"].get_feature_names_out()
    coefs = sorted(zip(names, pipe.named_steps["clf"].coef_[0]), key=lambda t: -abs(t[1]))
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    get_model.cache_clear()
    return {"roc_auc": round(float(auc), 3), "n_train": len(x_tr), "n_test": len(x_te),
            "top_coefficients": [(n.split("__", 1)[1], round(float(c), 3)) for n, c in coefs[:12]]}


@lru_cache
def get_model() -> Pipeline:
    if not MODEL_PATH.exists():
        train()
    return joblib.load(MODEL_PATH)


def score_frame(df: pd.DataFrame) -> np.ndarray:
    return np.round(get_model().predict_proba(prepare(df))[:, 1] * 100, 1)


def label(score: float) -> str:
    return "Hot" if score >= 70 else "Warm" if score >= 40 else "Cold"


def action(score: float, segment_code: str, has_gstin: bool) -> str:
    if not has_gstin:
        return "Offer the no-GST starter bundle"
    lab = label(score)
    if lab == "Hot":
        return "Field visit" if segment_code in ("multi", "mfg") else "Call + send WhatsApp quote"
    return "WhatsApp nudge" if lab == "Warm" else "Nurture via WhatsApp campaign"


def score_profile(profile: Profile) -> float:
    row = {
        "segment": SEGMENT_NAMES[profile.segment], "lead_source": "Website form", "city_tier": profile.city_tier,
        "preferred_language": LANGUAGE_NAMES.get(profile.language, "English"),
        "has_gstin": "Y" if profile.gstin_active else "N", "has_udyam": "N",
        "current_internet": profile.current_internet or "Mobile hotspot", "annual_turnover_band": "< 40 lakh",
        "employee_count": profile.employees, "num_sites": profile.sites,
        "monthly_telecom_spend_inr": profile.current_spend or 1000,
    }
    return float(score_frame(pd.DataFrame([row]))[0])
