// Response shapes of the FastAPI backend (backend/app/routers, services/*_view).

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
  status: "open" | "lead" | "quoted";
  slot?: string | null;
}

export type GstinStatus = "Active" | "Cancelled" | "Suspended" | "Invalid" | "NotFound";

export interface GstinLookup {
  gstin_masked: string;
  format_ok: boolean;
  checksum_ok: boolean;
  found: boolean;
  status: GstinStatus;
  legal_name?: string;
  trade_name?: string;
  constitution?: string;
  address?: string;
  state?: string;
  registration_date?: string;
}

export interface UdyamLookup {
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
  status: "draft" | "accepted";
  session_id: string | null;
  language: string;
  warnings_en: string[];
  warnings_hi: string[];
  share_text: string;
  whatsapp_url: string;
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
  id: string;
  status: CheckStatus | "skip";
  message_en: string;
  message_hi: string;
  doc: DocType | null;
  evidence: Record<string, unknown>;
}

export type KycStatus = "PENDING" | "PASS" | "PASS_WITH_WARNINGS" | "FAIL" | "RETAKE" | "INCOMPLETE";

export interface KycView {
  order_id: string;
  status: KycStatus;
  esigned: boolean;
  no_udyam: boolean;
  typed_gstin: string | null;
  typed_udyam: string | null;
  documents: Partial<Record<DocType, { detected_type: string | null; blur_score: number | null; fields: Record<string, unknown>; status: CheckStatus | null }>>;
  checks: KycCheck[];
}

export interface KycIdentifiersResult {
  gstin?: GstinLookup;
  udyam?: UdyamLookup;
}

export interface OrderStage {
  status: OrderStatus;
  label_en: string;
  label_hi: string;
  state: "done" | "current" | "upcoming";
  date: string | null;
  expected: boolean;
}

export interface OrderNotification {
  status: OrderStatus;
  date: string;
  message_en: string;
  message_hi: string;
}

export interface Order {
  id: string;
  status: OrderStatus;
  cancelled: boolean;
  language: string;
  bundle_name: string;
  monthly_total: number;
  setup_total: number;
  contract_months: number;
  items: { product_id: string; name: string; qty: number; monthly: number }[];
  progress: number;
  stages: OrderStage[];
  next_update_by: string | null;
  technician: { name_en: string; name_hi: string; phone_masked: string; rating: number; slot_en: string; slot_hi: string; date: string | null };
  delay: { reason_en: string; reason_hi: string; old_date: string; new_date: string; credit_inr: number } | null;
  credit_inr: number;
  nps: number | null;
  notifications: OrderNotification[];
}

export interface PrivacyView {
  order_id: string;
  status: OrderStatus;
  gstin: string | null;
  udyam: string | null;
  documents: { type: DocType; stored: boolean; uploaded: string }[];
  kyc_result: KycStatus | null;
  consents: { purposes: string[]; given: string; withdrawn: string | null }[];
  retention_en: string;
  retention_hi: string;
}

export type Heat = "Hot" | "Warm" | "Cold";

export interface BackofficeSession {
  id: string;
  created_at: string;
  channel: string;
  language: string;
  reason: string;
  score: number;
  label: Heat;
  action: string;
  profile: Record<string, unknown>;
  bundle_name: string | null;
  monthly_total: number | null;
}

export interface BackofficeLead {
  lead_id: string;
  business_type: string;
  segment: string;
  city: string;
  lead_source: string;
  language: string;
  employees: number;
  has_gstin: string;
  drop_reason: string | null;
  stage_reached: string | null;
  score: number;
  label: Heat;
  action: string;
}

export interface KycQueueItem {
  order_id: string;
  status: KycStatus;
  business: string;
  gstin: string | null;
  warnings: KycCheck[];
  updated_at: string;
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

export interface RulesAudit {
  activated: number;
  flagged: number;
  by_type: Record<string, number>;
  rows: AuditRow[];
}
