import secrets
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _short_id() -> str:
    return secrets.token_hex(4).upper()


def _now() -> datetime:
    return datetime.now()


class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(String(4), primary_key=True)
    category: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(20))
    price_min: Mapped[int] = mapped_column(Integer)
    price_max: Mapped[int] = mapped_column(Integer)
    setup: Mapped[int] = mapped_column(Integer)
    min_contract_months: Mapped[int] = mapped_column(Integer)
    city_tiers: Mapped[list] = mapped_column(JSON)
    min_employees: Mapped[int] = mapped_column(Integer)
    min_sites: Mapped[int] = mapped_column(Integer)
    requires_gstin: Mapped[bool] = mapped_column(Boolean)
    requires_one_of: Mapped[list] = mapped_column(JSON)
    install_days: Mapped[int] = mapped_column(Integer)
    segments: Mapped[list] = mapped_column(JSON)


class GstinRecord(Base):
    __tablename__ = "gstin_registry"
    gstin: Mapped[str] = mapped_column(String(15), primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(200))
    trade_name: Mapped[str] = mapped_column(String(200))
    constitution: Mapped[str] = mapped_column(String(60))
    principal_place_of_business: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(40))
    registration_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20))


class UdyamRecord(Base):
    __tablename__ = "udyam_registry"
    udyam_number: Mapped[str] = mapped_column(String(19), primary_key=True)
    enterprise_name: Mapped[str] = mapped_column(String(200))
    enterprise_type: Mapped[str] = mapped_column(String(20))
    major_activity: Mapped[str] = mapped_column(String(40))
    nic_description: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(40))
    city: Mapped[str] = mapped_column(String(40))
    date_of_registration: Mapped[date] = mapped_column(Date)


class Lead(Base):
    __tablename__ = "leads"
    lead_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    created_date: Mapped[date] = mapped_column(Date)
    lead_source: Mapped[str] = mapped_column(String(40))
    business_name: Mapped[str] = mapped_column(String(200))
    business_type: Mapped[str] = mapped_column(String(60))
    segment: Mapped[str] = mapped_column(String(60))
    city: Mapped[str] = mapped_column(String(40))
    city_tier: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(40))
    preferred_language: Mapped[str] = mapped_column(String(20))
    employee_count: Mapped[int] = mapped_column(Integer)
    num_sites: Mapped[int] = mapped_column(Integer)
    annual_turnover_band: Mapped[str] = mapped_column(String(30))
    has_gstin: Mapped[str] = mapped_column(String(1))
    gstin: Mapped[str | None] = mapped_column(String(15), index=True)
    has_udyam: Mapped[str] = mapped_column(String(1))
    udyam_number: Mapped[str | None] = mapped_column(String(19), index=True)
    current_internet: Mapped[str] = mapped_column(String(40))
    current_provider: Mapped[str | None] = mapped_column(String(40))
    monthly_telecom_spend_inr: Mapped[int] = mapped_column(Integer)
    products_of_interest: Mapped[str | None] = mapped_column(String(80))
    contact_name: Mapped[str] = mapped_column(String(80))
    contact_role: Mapped[str] = mapped_column(String(30))
    stage_reached: Mapped[str] = mapped_column(String(30))
    outcome: Mapped[str] = mapped_column(String(20))
    drop_reason: Mapped[str | None] = mapped_column(String(80))
    contacted_date: Mapped[date | None] = mapped_column(Date)
    needs_assessed_date: Mapped[date | None] = mapped_column(Date)
    quote_accepted_date: Mapped[date | None] = mapped_column(Date)
    kyc_complete_date: Mapped[date | None] = mapped_column(Date)
    activated_date: Mapped[date | None] = mapped_column(Date)
    days_lead_to_activation: Mapped[int | None] = mapped_column(Integer)
    customer_follow_up_calls: Mapped[int | None] = mapped_column(Integer)
    bundle_products: Mapped[str | None] = mapped_column(String(120))
    monthly_bundle_value_inr: Mapped[int | None] = mapped_column(Integer)
    one_time_setup_inr: Mapped[int | None] = mapped_column(Integer)
    contract_months: Mapped[int | None] = mapped_column(Integer)
    churned_within_6_months: Mapped[str | None] = mapped_column(String(1))
    nps_score: Mapped[int | None] = mapped_column(Integer)
    acquisition_cost_inr: Mapped[int | None] = mapped_column(Integer)
    propensity: Mapped[float | None] = mapped_column(Float)


class CityTier(Base):
    __tablename__ = "city_tiers"
    city: Mapped[str] = mapped_column(String(40), primary_key=True)
    city_tier: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(40))


class BusinessTypeSegment(Base):
    __tablename__ = "business_type_segment"
    business_type: Mapped[str] = mapped_column(String(60), primary_key=True)
    segment: Mapped[str] = mapped_column(String(10))


class AdvisorSession(Base):
    __tablename__ = "advisor_sessions"
    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=_short_id)
    language: Mapped[str] = mapped_column(String(20), default="en")
    mode: Mapped[str] = mapped_column(String(10), default="guided")
    channel: Mapped[str] = mapped_column(String(20), default="web")
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    history: Mapped[list] = mapped_column(JSON, default=list)
    bundle: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="open")
    close_reason: Mapped[str | None] = mapped_column(String(120))
    propensity: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=_short_id)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("advisor_sessions.id"))
    profile: Mapped[dict] = mapped_column(JSON)
    bundle_name: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    items: Mapped[list["QuoteItem"]] = relationship(cascade="all, delete-orphan", order_by="QuoteItem.position")


class QuoteItem(Base):
    __tablename__ = "quote_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.id"))
    position: Mapped[int] = mapped_column(Integer)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"))
    qty: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    optional: Mapped[bool] = mapped_column(Boolean, default=False)
    reason_en: Mapped[str] = mapped_column(Text, default="")
    reason_hi: Mapped[str] = mapped_column(Text, default="")


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=_short_id)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.id"))
    status: Mapped[str] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(5), default="en")
    snapshot: Mapped[dict] = mapped_column(JSON)
    schedule: Mapped[dict] = mapped_column(JSON, default=dict)
    delay: Mapped[dict | None] = mapped_column(JSON)
    credit_inr: Mapped[int] = mapped_column(Integer, default=0)
    nps: Mapped[int | None] = mapped_column(Integer)
    activated_on: Mapped[date | None] = mapped_column(Date)
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    events: Mapped[list["OrderEvent"]] = relationship(cascade="all, delete-orphan", order_by="OrderEvent.id")


class OrderEvent(Base):
    __tablename__ = "order_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    status: Mapped[str] = mapped_column(String(20))
    on_date: Mapped[date] = mapped_column(Date)
    message_en: Mapped[str] = mapped_column(Text)
    message_hi: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Consent(Base):
    __tablename__ = "consents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    purposes: Mapped[list] = mapped_column(JSON)
    notice_version: Mapped[str] = mapped_column(String(10))
    language: Mapped[str] = mapped_column(String(5))
    ip_hash: Mapped[str] = mapped_column(String(64))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class KycSubmission(Base):
    __tablename__ = "kyc_submissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), unique=True)
    typed_gstin: Mapped[str | None] = mapped_column(String(15))
    typed_udyam: Mapped[str | None] = mapped_column(String(19))
    no_udyam: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    esigned: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewer_decision: Mapped[str | None] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
    documents: Mapped[list["KycDocument"]] = relationship(cascade="all, delete-orphan")
    checks: Mapped[list["KycCheck"]] = relationship(cascade="all, delete-orphan")


class KycDocument(Base):
    __tablename__ = "kyc_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("kyc_submissions.id"))
    doc_type: Mapped[str] = mapped_column(String(30))
    storage_key: Mapped[str | None] = mapped_column(String(80))
    detected_type: Mapped[str | None] = mapped_column(String(30))
    blur_score: Mapped[float | None] = mapped_column(Float)
    fields: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class KycCheck(Base):
    __tablename__ = "kyc_checks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("kyc_submissions.id"))
    check_id: Mapped[str] = mapped_column(String(4))
    status: Mapped[str] = mapped_column(String(5))
    message_en: Mapped[str] = mapped_column(Text)
    message_hi: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(60))
    target: Mapped[str] = mapped_column(String(60))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
