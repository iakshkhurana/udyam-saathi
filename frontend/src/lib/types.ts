// Shapes returned by the FastAPI backend. Advisor + registry types mirror
// backend/app/schemas.py and services/advisor.py. Quote, KYC, order and
// back-office types are the contract the Phase 4–6 routers must return.

export type Lang = "en" | "hi" | "ta" | "te" | "kn" | "mr" | "gu" | "bn" | "pa" | "ml";

export interface Health {
  status: string;
  mode: "AI" | "Guided";
  ocr_available: boolean;
  today: string;
}

export interface Chip {
  label: string;
  value: string;
  selected?: boolean;
}

export interface BundleItem {
  product_id: string;
  name: string;
  category: string;
  unit: string;
  qty: number;
  unit_price: number;
  monthly: number;
  setup: number;
  reason_en: string;
  reason_hi: string;
  optional: boolean;
  enabled: boolean;
  is_base: boolean;
}

export interface Excluded {
  product_id: string;
  name: string;
  reason_en: string;
  reason_hi: string;
  rules: string[];
}

export interface Bundle {
  bundle_name: string;
  items: BundleItem[];
  monthly_total: number;
  setup_total: number;
  contract_months: number;
  install_days: number;
  excluded: Excluded[];
  unlocks_with_gstin: string[];
  savings_vs_current: number | null;
  savings_line_en: string;
  savings_line_hi: string;
  why_en: string[];
  why_hi: string[];
  notes_en: string[];
  notes_hi: string[];
  gst_note_en: string;
  gst_note_hi: string;
}

export interface AdvisorTurn {
  session_id: string;
  reply: string;
  chips: Chip[];
  profile: Record<string, unknown>;
  bundle: Bundle | null;
  mode: "ai" | "guided";
  language: string;
  status: "open" | "lead" | "quoted" | string;
  slot?: string | null;
}

export interface GstinLookup {
  gstin: string;
  gstin_masked: string;
  format_ok: boolean;
  checksum_ok: boolean;
  found: boolean;
  status: "Active" | "Cancelled" | "Suspended" | "Invalid" | "NotFound";
  legal_name?: string;
  trade_name?: string;
  constitution?: string;
  address?: string;
  state?: string;
  registration_date?: string;
}

export interface UdyamLookup {
  udyam: string;
  udyam_masked: string;
  format_ok: boolean;
  found: boolean;
  enterprise_name?: string;
  enterprise_type?: string;
  major_activity?: string;
  state?: string;
  city?: string;
  date_of_registration?: string;
}

export interface Quote extends Bundle {
  id: string;
  session_id: string | null;
  status: "draft" | "accepted";
  warnings_en?: string[];
  warnings_hi?: string[];
}

export type OrderStatus =
  | "QUOTE_ACCEPTED"
  | "CONSENT_GIVEN"
  | "KYC_VERIFIED"
  | "KYC_REVIEW"
  | "INSTALL_SCHEDULED"
  | "INSTALLED"
  | "ACTIVATED"
  | "DELAYED"
  | "CANCELLED";

export type DocType = "gst_certificate" | "udyam_certificate" | "signatory_id" | "address_proof";
export type CheckStatus = "pass" | "warn" | "fail";

export interface KycCheck {
  name: string;
  status: CheckStatus;
  message_en: string;
  message_hi: string;
}

export interface KycDocResult {
  doc_type: DocType;
  status: CheckStatus;
  message_en: string;
  message_hi: string;
  checks: KycCheck[];
  fields?: Record<string, string | null>;
}

export interface KycIdentifiersResult {
  gstin: GstinLookup | null;
  udyam: UdyamLookup | null;
}

export interface KycSampleResult extends KycIdentifiersResult {
  documents: KycDocResult[];
}

export interface KycVerifyResult {
  status: "KYC_VERIFIED" | "KYC_REVIEW" | "KYC_FAILED";
  documents: KycDocResult[];
  checks: KycCheck[];
}

export interface OrderStage {
  status: OrderStatus;
  state: "done" | "current" | "pending";
  date: string | null;
}

export interface OrderNotification {
  id: string;
  created_at: string;
  text_en: string;
  text_hi: string;
}

export interface Order {
  id: string;
  short_code: string;
  status: OrderStatus;
  bundle_name: string;
  monthly_total: number;
  city: string | null;
  gstin_masked: string | null;
  consent_given: boolean;
  stages: OrderStage[];
  next_update_by: string | null;
  notifications: OrderNotification[];
  technician: { name: string; phone_masked: string; visit_en: string; visit_hi: string } | null;
  delay: { reason_en: string; reason_hi: string; new_date: string; credit_inr: number } | null;
  nps: number | null;
}

export interface BackofficeSession {
  id: string;
  created_at: string;
  language: string;
  reason: string;
  profile: Record<string, unknown>;
  score: number;
  label: "Hot" | "Warm" | "Cold";
  action: string;
}

export interface BackofficeLead {
  lead_id: string;
  business_type: string;
  segment: string;
  city: string;
  city_tier: number;
  lead_source: string;
  has_gstin: string;
  drop_reason: string | null;
  score: number;
  label: "Hot" | "Warm" | "Cold";
  action: string;
}

export interface KycQueueItem {
  order_id: string;
  short_code: string;
  business_name: string;
  gstin_masked: string | null;
  submitted_at: string;
  documents: KycDocResult[];
}

export interface AuditRow {
  lead_id: string;
  business_type: string;
  city: string;
  city_tier: number;
  employees: number;
  sites: number;
  has_gstin: string;
  gstin: string | null;
  bundle: string;
  monthly_value: number;
  violations: { product_id: string; product: string; rules: string[] }[];
}

// Same shape as docs/rules_audit.json
export interface RulesAudit {
  activated: number;
  flagged: number;
  by_type: Record<string, number>;
  rows: AuditRow[];
}
