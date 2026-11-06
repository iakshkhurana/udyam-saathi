import type {
  AdvisorTurn,
  BackofficeLead,
  BackofficeSession,
  Bundle,
  DocType,
  GstinLookup,
  Health,
  KycIdentifiersResult,
  KycQueueItem,
  KycView,
  Order,
  PrivacyView,
  Quote,
  RulesAudit,
  UdyamLookup,
} from "./types";

const BASE = `${import.meta.env.VITE_API_URL ?? ""}/api`;

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

const post = <T>(path: string, body?: unknown, init: RequestInit = {}) =>
  request<T>(path, { ...init, method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

const pinHeader = (pin: string) => ({ headers: { "X-Backoffice-Pin": pin } });

export const api = {
  health: () => request<Health>("/health"),

  gstin: (g: string) => request<GstinLookup>(`/gstin/${encodeURIComponent(g)}`),
  udyam: (u: string) => request<UdyamLookup>(`/udyam/${encodeURIComponent(u)}`),

  startSession: (language: string) => post<AdvisorTurn>("/advisor/sessions", { language, channel: "web" }),
  sendMessage: (id: string, msg: { text?: string; chip?: string }) =>
    post<AdvisorTurn>(`/advisor/sessions/${id}/message`, msg),
  abandon: (id: string) => post<{ status: string }>(`/advisor/sessions/${id}/abandon`),
  recommend: (profile: Record<string, unknown>) => post<Bundle>("/advisor/recommend", profile),

  createQuote: (session_id: string) => post<Quote>("/quotes", { session_id }),
  getQuote: (id: string) => request<Quote>(`/quotes/${id}`),
  patchQuote: (id: string, items: { product_id: string; enabled?: boolean; qty?: number }[]) =>
    request<Quote>(`/quotes/${id}`, { method: "PATCH", body: JSON.stringify({ items }) }),
  acceptQuote: (id: string) => post<Order>(`/quotes/${id}/accept`),

  giveConsent: (body: { order_id: string; kyc: boolean; marketing_whatsapp: boolean; language: string }) =>
    post<{ order_id: string; purposes: string[] }>("/consents", body),

  kyc: (orderId: string) => request<KycView>(`/kyc/${orderId}`),
  kycIdentifiers: (orderId: string, body: { gstin?: string; udyam?: string; no_udyam?: boolean }) =>
    post<KycIdentifiersResult>(`/kyc/${orderId}/identifiers`, body),
  kycUpload: (orderId: string, doc: DocType, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<KycView>(`/kyc/${orderId}/documents/${doc}`, { method: "POST", body: fd });
  },
  kycSample: (orderId: string, applicant: string) =>
    post<KycView>(`/kyc/${orderId}/load-sample/${applicant}`),
  kycVerify: (orderId: string) => post<KycView & { order: Order }>(`/kyc/${orderId}/verify`),
  kycEsign: (orderId: string, otp: string) => post<{ ok: boolean; esigned: boolean }>(`/kyc/${orderId}/esign`, { otp }),

  order: (id: string) => request<Order>(`/orders/${id}`),
  advance: (id: string) => post<Order>(`/orders/${id}/advance`),
  delay: (id: string) => post<Order>(`/orders/${id}/delay`),
  nps: (id: string, score: number) => post<{ ok: boolean; nps: number }>(`/orders/${id}/nps`, { score }),
  referral: (body: { order_id: string; business_name: string; phone: string }) =>
    post<{ ok: boolean; referral_id: string }>("/referrals", body),

  privacy: (order_id: string) => request<PrivacyView>(`/privacy/${order_id}`),
  withdraw: (order_id: string) => post<{ ok: boolean; documents_deleted: number; order_status: string }>("/privacy/withdraw", { order_id }),
  deleteData: (order_id: string) => request<{ ok: boolean; documents_deleted: number }>(`/privacy/data/${order_id}`, { method: "DELETE" }),

  bo: {
    sessions: (pin: string) => request<BackofficeSession[]>("/backoffice/sessions", pinHeader(pin)),
    leads: (pin: string, q: Record<string, string>) =>
      request<BackofficeLead[]>(`/backoffice/leads?${new URLSearchParams(q)}`, pinHeader(pin)),
    kycQueue: (pin: string) => request<KycQueueItem[]>("/backoffice/kyc-queue", pinHeader(pin)),
    rulesAudit: (pin: string) => request<RulesAudit>("/backoffice/rules-audit", pinHeader(pin)),
    decide: (orderId: string, decision: "approve" | "reject", pin: string) =>
      post<{ status: string }>(`/backoffice/kyc/${orderId}/decision`, { decision, pin }),
  },
};
