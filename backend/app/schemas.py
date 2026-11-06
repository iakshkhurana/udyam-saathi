from typing import Literal

from pydantic import BaseModel, Field

Segment = Literal["micro", "prof", "multi", "mfg"]
GstinStatus = Literal["Active", "Cancelled", "Suspended", "Invalid", "NotFound"]


class Profile(BaseModel):
    language: str = "en"
    business_type: str | None = None
    segment: Segment = "micro"
    employees: int = Field(1, ge=1)
    sites: int = Field(1, ge=1)
    city: str | None = None
    city_tier: int = 2
    current_internet: str | None = None
    current_spend: int | None = None
    needs: list[str] = []
    requested_products: list[str] = []
    gstin: str | None = None
    gstin_status: GstinStatus | None = None
    vehicles: int = 1
    no_fibre: bool = False
    mobile_only: bool = False
    cheapest: bool = False
    use_defaults: bool = False

    @property
    def gstin_active(self) -> bool:
        return self.gstin_status == "Active"


class BundleItem(BaseModel):
    product_id: str
    name: str
    category: str
    unit: str
    qty: int
    unit_price: int
    monthly: int
    setup: int
    reason_en: str
    reason_hi: str
    optional: bool = False
    enabled: bool = True
    is_base: bool = False


class Excluded(BaseModel):
    product_id: str
    name: str
    reason_en: str
    reason_hi: str
    rules: list[str]


class BundleResult(BaseModel):
    bundle_name: str
    items: list[BundleItem]
    monthly_total: int
    setup_total: int
    contract_months: int
    install_days: int
    excluded: list[Excluded] = []
    unlocks_with_gstin: list[str] = []
    savings_vs_current: int | None = None
    savings_line_en: str = ""
    savings_line_hi: str = ""
    why_en: list[str] = []
    why_hi: list[str] = []
    notes_en: list[str] = []
    notes_hi: list[str] = []
    gst_note_en: str = "Prices exclude 18% GST."
    gst_note_hi: str = "कीमतों में 18% GST शामिल नहीं है।"


class AdvisorStart(BaseModel):
    language: str = "en"
    channel: str = "web"


class AdvisorMessage(BaseModel):
    text: str | None = None
    chip: str | None = None


class QuoteCreate(BaseModel):
    session_id: str | None = None
    profile: Profile | None = None


class QuoteItemPatch(BaseModel):
    product_id: str
    enabled: bool | None = None
    qty: int | None = Field(None, ge=1, le=500)


class QuotePatch(BaseModel):
    items: list[QuoteItemPatch]


class ConsentCreate(BaseModel):
    order_id: str
    kyc: bool
    marketing_whatsapp: bool = False
    language: str = "en"


class KycIdentifiers(BaseModel):
    gstin: str | None = None
    udyam: str | None = None
    no_udyam: bool = False


class Esign(BaseModel):
    otp: str


class Nps(BaseModel):
    score: int = Field(ge=0, le=10)


class Referral(BaseModel):
    order_id: str
    business_name: str
    phone: str


class Withdraw(BaseModel):
    order_id: str


class KycDecision(BaseModel):
    decision: Literal["approve", "reject"]
    pin: str
