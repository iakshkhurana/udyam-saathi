import pandas as pd

from ..config import get_settings
from ..db import Base, SessionLocal, engine
from ..models import BusinessTypeSegment, CityTier, GstinRecord, Lead, Product, UdyamRecord
from .catalogue import get_catalogue

SEGMENT_CODES = {
    "Micro retail & services": "micro",
    "Professional offices": "prof",
    "Small multi-site businesses": "multi",
    "Small manufacturers": "mfg",
}
LEAD_DATE_COLS = ["created_date", "contacted_date", "needs_assessed_date", "quote_accepted_date",
                  "kyc_complete_date", "activated_date"]
LEAD_INT_COLS = ["days_lead_to_activation", "customer_follow_up_calls", "monthly_bundle_value_inr",
                 "one_time_setup_inr", "contract_months", "nps_score", "acquisition_cost_inr"]


def _records(df: pd.DataFrame) -> list[dict]:
    df = df.astype(object).where(df.notna(), None)
    return df.to_dict("records")


def load() -> dict[str, int]:
    data = get_settings().data_path
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    products = [Product(**p.as_dict()) for p in get_catalogue().values()]

    gst = pd.read_csv(data / "mock_gstin_registry.csv", parse_dates=["registration_date"])
    gst["registration_date"] = gst["registration_date"].dt.date
    udy = pd.read_csv(data / "mock_udyam_registry.csv", parse_dates=["date_of_registration"])
    udy["date_of_registration"] = udy["date_of_registration"].dt.date

    leads = pd.read_csv(data / "smb_leads.csv", dtype={"gstin": str, "udyam_number": str},
                        keep_default_na=False, na_values=[""])
    for col in LEAD_DATE_COLS:
        leads[col] = pd.to_datetime(leads[col]).dt.date
    for col in LEAD_INT_COLS:
        leads[col] = leads[col].astype("Int64")

    tiers = leads.groupby("city").agg(city_tier=("city_tier", "first"), state=("state", "first")).reset_index()
    seg = (leads.assign(segment=leads["segment"].map(SEGMENT_CODES))
           .groupby("business_type")["segment"].agg(lambda s: s.mode().iloc[0]).reset_index())

    with SessionLocal() as db:
        db.add_all(products)
        db.bulk_insert_mappings(GstinRecord, _records(gst))
        db.bulk_insert_mappings(UdyamRecord, _records(udy))
        db.bulk_insert_mappings(Lead, _records(leads))
        db.bulk_insert_mappings(CityTier, _records(tiers))
        db.bulk_insert_mappings(BusinessTypeSegment, _records(seg))
        db.commit()
    return {"products": len(products), "gstin": len(gst), "udyam": len(udy), "leads": len(leads),
            "cities": len(tiers), "business_types": len(seg)}
