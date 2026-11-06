import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { LangToggle } from "../components/AppShell";
import { House, Lock } from "../components/Icons";
import { PageLoader, Spinner, StatusIcon, useLoad } from "../components/ui";
import { api, ApiError } from "../lib/api";
import { cx, pick, rupees } from "../lib/format";
import type { BackofficeLead } from "../lib/types";

type Tab = "sessions" | "leads" | "kyc" | "audit";
const TABS: Tab[] = ["sessions", "leads", "kyc", "audit"];
const PIN_KEY = "saathi.boPin";

function readPin() {
  try {
    return sessionStorage.getItem(PIN_KEY) ?? "";
  } catch {
    return "";
  }
}

function savePin(pin: string) {
  try {
    if (pin) sessionStorage.setItem(PIN_KEY, pin);
    else sessionStorage.removeItem(PIN_KEY);
  } catch {
    /* storage blocked */
  }
}

const LABEL_TONE = { Hot: "bg-[rgba(255,120,140,.16)] text-[#FF9DB0]", Warm: "bg-[rgba(255,170,80,.16)] text-[#FFC27A]", Cold: "bg-[rgba(120,200,255,.14)] text-[#9DD8FF]" };

function Score({ score, label }: { score: number; label: "Hot" | "Warm" | "Cold" }) {
  return (
    <div className="flex min-w-[130px] items-center gap-2">
      <span className="w-7 text-right font-mono text-[13px] tabular-nums">{score}</span>
      <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
        <span className="block h-full rounded-full bg-brand-400" style={{ width: `${score}%` }} />
      </span>
      <span className={cx("rounded-full px-2 py-0.5 text-[11px] font-semibold", LABEL_TONE[label])}>{label}</span>
    </div>
  );
}

function Table({ head, children, minW = 820 }: { head: string[]; children: ReactNode; minW?: number }) {
  return (
    <div className="overflow-x-auto rounded-[20px] border border-white/10 bg-white/[.03]">
      <table className="w-full border-collapse text-[13px]" style={{ minWidth: minW }}>
        <thead>
          <tr className="text-left text-[#A39FC4]">
            {head.map((h) => (
              <th key={h} className="px-4 py-3.5 font-semibold">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="[&>tr]:border-t [&>tr]:border-white/[.06] [&>tr:hover]:bg-white/[.03] [&_td]:px-4 [&_td]:py-3.5">{children}</tbody>
      </table>
    </div>
  );
}

function Empty() {
  const { t } = useTranslation();
  return <p className="rounded-[20px] border border-white/10 bg-white/[.03] p-8 text-center text-sm text-[#A39FC4]">{t("bo.empty")}</p>;
}

function Failed({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const { t } = useTranslation();
  const msg = error instanceof ApiError && (error.status === 404 || error.status === 405) ? t("common.notReady") : error instanceof Error ? error.message : String(error);
  return (
    <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-[20px] border border-[rgba(255,120,140,.3)] bg-[rgba(255,120,140,.08)] p-5 text-sm text-[#FFC2CC]">
      {msg}
      <button type="button" onClick={onRetry} className="btn min-h-[40px] border border-white/15 text-sm text-white hover:bg-white/10">{t("common.retry")}</button>
    </div>
  );
}

const profileLine = (p: Record<string, unknown>) =>
  [p.business_type, p.employees && `${p.employees} staff`, p.sites && Number(p.sites) > 1 && `${p.sites} sites`, p.city].filter(Boolean).join(" · ");

function Sessions({ pin }: { pin: string }) {
  const { t } = useTranslation();
  const q = useLoad(() => api.bo.sessions(pin), [pin]);
  if (q.error) return <Failed error={q.error} onRetry={q.reload} />;
  if (!q.data) return <PageLoader />;
  if (!q.data.length) return <Empty />;
  return (
    <Table head={[t("bo.profile"), t("bo.reason"), t("bo.score"), t("bo.action")]}>
      {q.data.map((s) => (
        <tr key={s.id}>
          <td>
            <div className="font-medium text-white">{profileLine(s.profile) || "—"}</div>
            <div className="text-xs text-[#A39FC4]">{new Date(s.created_at).toLocaleString("en-IN")} · {s.channel} · {s.language.toUpperCase()}</div>
            {s.bundle_name && <div className="text-xs text-[#C9BCFF]">{s.bundle_name}{s.monthly_total != null && ` · ${rupees(s.monthly_total)}/mo`}</div>}
          </td>
          <td className="text-[#DCD8F5]">{s.reason}</td>
          <td><Score score={s.score} label={s.label} /></td>
          <td className="text-[#C9BCFF]">{s.action}</td>
        </tr>
      ))}
    </Table>
  );
}

function Leads({ pin }: { pin: string }) {
  const { t } = useTranslation();
  const [filter, setFilter] = useState({ segment: "", city: "", source: "" });
  const query = Object.fromEntries(Object.entries(filter).filter(([, v]) => v));
  const q = useLoad(() => api.bo.leads(pin, query), [pin, filter.segment, filter.city, filter.source]);
  const [options, setOptions] = useState<Record<"segment" | "city" | "source", string[]>>({ segment: [], city: [], source: [] });

  const rows = q.data;
  useEffect(() => {
    if (!rows || Object.values(filter).some(Boolean)) return;
    const uniq = (f: (l: BackofficeLead) => string) => [...new Set(rows.map(f))].sort();
    setOptions({ segment: uniq((l) => l.segment), city: uniq((l) => l.city), source: uniq((l) => l.lead_source) });
  }, [rows]);

  const select = (key: keyof typeof filter, label: string) => (
    <label className="flex flex-col gap-1 text-xs text-[#A39FC4]">
      {label}
      <select
        value={filter[key]}
        onChange={(e) => setFilter({ ...filter, [key]: e.target.value })}
        className="min-h-[40px] min-w-[150px] rounded-xl border border-white/10 bg-night-800 px-3 text-sm text-white focus:border-brand-400 focus:outline-none"
      >
        <option value="">{t("bo.all")}</option>
        {options[key].map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </label>
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3">
        {select("segment", t("bo.segment"))}
        {select("city", t("bo.cityCol"))}
        {select("source", t("bo.source"))}
        {q.loading && <Spinner className="mb-2.5 h-4 w-4 text-brand-300" />}
      </div>
      {q.error ? (
        <Failed error={q.error} onRetry={q.reload} />
      ) : !rows ? (
        <PageLoader />
      ) : !rows.length ? (
        <Empty />
      ) : (
        <Table head={[t("bo.lead"), t("bo.businessCol"), t("bo.cityCol"), t("bo.source"), t("bo.stage"), t("bo.score"), t("bo.action")]} minW={980}>
          {rows.map((l) => (
            <tr key={l.lead_id}>
              <td className="font-mono">{l.lead_id}</td>
              <td>
                <div className="text-white">{l.business_type}</div>
                <div className="text-xs text-[#A39FC4]">{l.segment} · {l.employees} staff · GSTIN {l.has_gstin}</div>
              </td>
              <td>{l.city}</td>
              <td className="text-[#DCD8F5]">{l.lead_source}</td>
              <td>
                <div className="text-[#DCD8F5]">{l.stage_reached ?? "—"}</div>
                {l.drop_reason && <div className="text-xs text-[#A39FC4]">{l.drop_reason}</div>}
              </td>
              <td><Score score={l.score} label={l.label} /></td>
              <td className="text-[#C9BCFF]">{l.action}</td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  );
}

function KycQueue({ pin }: { pin: string }) {
  const { t, i18n } = useTranslation();
  const q = useLoad(() => api.bo.kycQueue(pin), [pin]);
  const [deciding, setDeciding] = useState<string | null>(null);
  if (q.error) return <Failed error={q.error} onRetry={q.reload} />;
  if (!q.data) return <PageLoader />;
  if (!q.data.length) return <Empty />;

  const decide = async (orderId: string, decision: "approve" | "reject") => {
    setDeciding(orderId);
    try {
      await api.bo.decide(orderId, decision, pin);
      q.set(q.data!.filter((x) => x.order_id !== orderId));
    } finally {
      setDeciding(null);
    }
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <AnimatePresence>
        {q.data.map((item) => (
          <motion.div key={item.order_id} layout exit={{ opacity: 0, scale: 0.96 }} className="rounded-[20px] border border-white/10 bg-white/[.04] p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-display text-lg font-bold text-white">{item.business}</div>
                <div className="font-mono text-xs text-[#A39FC4]">{item.order_id} · {item.gstin ?? "no GSTIN"} · {item.status}</div>
              </div>
              <span className="text-xs text-[#A39FC4]">{new Date(item.updated_at).toLocaleString("en-IN")}</span>
            </div>
            <div className="eyebrow mt-4 text-[#A39FC4]">{t("bo.issues")}</div>
            <ul className="mt-2 flex flex-col gap-2">
              {item.warnings.map((c) => (
                <li key={c.id} className="flex gap-3 rounded-xl bg-white/[.04] p-2.5">
                  {c.status !== "skip" && <StatusIcon status={c.status} />}
                  <div className="text-[13px]">
                    <div className="font-semibold text-white">{c.doc ? t(`kyc.docs.${c.doc}`) : c.id}</div>
                    <div className="text-[#C8C3E6]">{pick(c, "message", i18n.language)}</div>
                  </div>
                </li>
              ))}
            </ul>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <button type="button" disabled={deciding === item.order_id} onClick={() => decide(item.order_id, "reject")} className="btn min-h-[44px] border border-white/15 text-sm text-white hover:bg-white/10">
                {t("bo.reject")}
              </button>
              <button type="button" disabled={deciding === item.order_id} onClick={() => decide(item.order_id, "approve")} className="btn-primary min-h-[44px] text-sm">
                {deciding === item.order_id ? <Spinner className="h-4 w-4" /> : t("bo.approve")}
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

const RULE_LABEL: Record<string, string> = { "city tier": "City tier", tier: "City tier", GSTIN: "GSTIN", gstin: "GSTIN", dependency: "Dependency", employees: "Employees", sites: "Sites" };

function Audit({ pin }: { pin: string }) {
  const { t } = useTranslation();
  const q = useLoad(() => api.bo.rulesAudit(pin), [pin]);
  if (q.error) return <Failed error={q.error} onRetry={q.reload} />;
  if (!q.data) return <PageLoader />;
  const a = q.data;
  const max = Math.max(...Object.values(a.by_type));
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-[clamp(24px,3vw,34px)] font-bold tracking-[-0.03em] text-white">{t("bo.auditTitle")}</h2>
        <p className="mt-1.5 text-sm text-[#A39FC4]">{t("bo.auditSub")}</p>
      </div>
      <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-5">
        <div className="rounded-[18px] border border-brand-400/40 bg-gradient-to-b from-brand-500/25 to-brand-500/5 p-4">
          <div className="text-xs text-[#C9BCFF]">{t("bo.flagged")}</div>
          <div className="mt-1.5 font-display text-[32px] font-extrabold text-white">
            {a.flagged} <span className="text-sm font-semibold text-[#A39FC4]">/ {a.activated} · {Math.round((a.flagged / a.activated) * 100)}%</span>
          </div>
        </div>
        {Object.entries(a.by_type).map(([k, v], i) => (
          <div key={k} className="rounded-[18px] border border-white/10 bg-white/[.04] p-4">
            <div className="text-xs text-[#A39FC4]">{RULE_LABEL[k] ?? k}</div>
            <div className="mt-1.5 font-display text-[32px] font-extrabold text-white">{v}</div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
              <motion.div initial={{ width: 0 }} animate={{ width: `${(v / max) * 100}%` }} transition={{ duration: 0.9, delay: 0.1 + i * 0.08 }} className="h-full rounded-full bg-brand-400" />
            </div>
          </div>
        ))}
      </div>
      <Table head={[t("bo.lead"), t("bo.businessCol"), t("bo.cityCol"), t("bo.staff"), t("bo.bundle"), t("bo.broken")]} minW={960}>
        {a.rows.map((r) => (
          <tr key={r.lead_id}>
            <td className="font-mono">{r.lead_id}</td>
            <td>
              <div className="text-white">{r.business_type}</div>
              <div className="text-xs text-[#A39FC4]">{rupees(r.monthly_value)}/mo · GSTIN {r.has_gstin}</div>
            </td>
            <td>{r.city} · T{r.city_tier}</td>
            <td className="tabular-nums">{r.employees}</td>
            <td className="max-w-[260px] break-all font-mono text-xs text-[#C9BCFF]">{r.bundle}</td>
            <td>
              <div className="flex flex-wrap gap-1.5">
                {r.violations.map((v) => (
                  <span key={v.product_id} className="rounded-full bg-[rgba(255,170,80,.14)] px-2.5 py-1 text-xs text-[#FFC27A]">
                    {v.product}: {v.rules.map((x) => RULE_LABEL[x] ?? x).join(", ")}
                  </span>
                ))}
              </div>
            </td>
          </tr>
        ))}
      </Table>
    </div>
  );
}

function PinGate({ onUnlock, wrong }: { onUnlock: (pin: string) => void; wrong: boolean }) {
  const { t } = useTranslation();
  const [pin, setPin] = useState("");
  const submit = (e: FormEvent) => {
    e.preventDefault();
    onUnlock(pin);
  };
  return (
    <motion.form initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} onSubmit={submit} className="mx-auto mt-20 flex w-full max-w-[360px] flex-col gap-4 rounded-[24px] border border-white/10 bg-white/[.05] p-6 backdrop-blur">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-brand-500/20 text-brand-300"><Lock /></span>
      <label htmlFor="pin" className="font-display text-xl font-bold text-white">{t("bo.pin")}</label>
      <input
        id="pin"
        type="password"
        inputMode="numeric"
        autoFocus
        value={pin}
        onChange={(e) => setPin(e.target.value)}
        className="min-h-[50px] rounded-xl border border-white/15 bg-night px-4 text-center font-mono text-xl tracking-[.4em] text-white focus:border-brand-400 focus:outline-none"
      />
      {wrong && <p className="text-sm text-[#FF9DB0]">{t("bo.wrongPin")}</p>}
      <button type="submit" disabled={!pin} className="btn-primary min-h-[50px]">{t("bo.unlock")}</button>
    </motion.form>
  );
}

export default function Backoffice() {
  const { t } = useTranslation();
  const [pin, setPin] = useState(readPin);
  const [tab, setTab] = useState<Tab>("sessions");
  const [checking, setChecking] = useState(false);
  const [wrong, setWrong] = useState(false);

  const unlock = async (p: string) => {
    setChecking(true);
    setWrong(false);
    try {
      await api.bo.rulesAudit(p);
      savePin(p);
      setPin(p);
    } catch (e) {
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) setWrong(true);
      else {
        savePin(p);
        setPin(p);
      }
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="min-h-[100dvh] px-4 pb-12 pt-6 text-[#ECE9FF] [background:radial-gradient(900px_420px_at_50%_-160px,#3A1F9E_0%,#160F38_45%,#0C0A1D_80%)] [color-scheme:dark]">
      <div className="mx-auto flex max-w-[1240px] flex-col gap-6">
        <header className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/[.08] bg-white/[.04] py-2.5 pl-4 pr-3">
          <Link to="/" className="flex items-center gap-2.5 font-display text-[17px] font-extrabold text-white">
            <span className="grid h-[30px] w-[30px] place-items-center rounded-[9px] bg-gradient-to-br from-brand-400 to-brand-700"><House size={16} /></span>
            Udyam Saathi <span className="font-semibold text-[#A39FC4]">· {t("bo.title")}</span>
          </Link>
          <div className="flex flex-wrap items-center gap-2">
            {pin && (
              <nav aria-label={t("bo.title")} className="flex flex-wrap gap-1 rounded-xl bg-white/5 p-1 text-[13px] font-semibold">
                {TABS.map((k) => (
                  <button key={k} type="button" onClick={() => setTab(k)} aria-current={tab === k ? "page" : undefined} className={cx("relative min-h-[36px] rounded-[9px] px-3.5 transition-colors", tab === k ? "text-white" : "text-[#A39FC4] hover:text-white")}>
                    {tab === k && <motion.span layoutId="bo-tab" className="absolute inset-0 rounded-[9px] bg-gradient-to-b from-brand-500 to-brand-600 shadow-[0_6px_16px_rgba(90,59,240,.4)]" transition={{ type: "spring", stiffness: 500, damping: 38 }} />}
                    <span className="relative">{t(`bo.tabs.${k}`)}</span>
                  </button>
                ))}
              </nav>
            )}
            <LangToggle dark />
          </div>
        </header>

        {!pin ? (
          checking ? <PageLoader /> : <PinGate onUnlock={unlock} wrong={wrong} />
        ) : (
          <AnimatePresence mode="wait">
            <motion.section key={tab} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
              {tab === "sessions" && <Sessions pin={pin} />}
              {tab === "leads" && <Leads pin={pin} />}
              {tab === "kyc" && <KycQueue pin={pin} />}
              {tab === "audit" && <Audit pin={pin} />}
            </motion.section>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
