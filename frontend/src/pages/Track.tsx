import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { Alert, ArrowRight, Check, Gift, Link as LinkIcon, Phone } from "../components/Icons";
import { ErrorState, PageLoader, Pill, Reveal, Spinner, useLoad } from "../components/ui";
import { api, ApiError } from "../lib/api";
import { clockTime, cx, pick, rupees, shortDate } from "../lib/format";
import type { Order } from "../lib/types";

function Stages({ order }: { order: Order }) {
  const { t, i18n } = useTranslation();
  const done = order.stages.filter((s) => s.state === "done").length;
  const pct = Math.round(((done + 0.5) / order.stages.length) * 100);
  return (
    <div className="card p-4">
      <div className="h-2 overflow-hidden rounded-full bg-[#EEEAFB]">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${order.status === "ACTIVATED" ? 100 : pct}%` }}
          transition={{ duration: 1, ease: [0.2, 0.7, 0.2, 1] }}
          className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600"
        />
      </div>
      <ol className="mt-4 flex flex-col">
        {order.stages.map((s, i) => (
          <motion.li
            key={s.status}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 + i * 0.06 }}
            className="relative flex gap-3 pb-4 last:pb-0"
            aria-current={s.state === "current" ? "step" : undefined}
          >
            {i < order.stages.length - 1 && (
              <span aria-hidden className={cx("absolute left-[10px] top-6 h-[calc(100%-20px)] w-0.5", s.state === "done" ? "bg-ok" : "bg-[#E6E1F7]")} />
            )}
            {s.state === "done" ? (
              <span className="relative grid h-[22px] w-[22px] flex-none place-items-center rounded-full bg-ok text-white"><Check size={13} strokeWidth={3} /></span>
            ) : s.state === "current" ? (
              <span className="relative h-[22px] w-[22px] flex-none animate-pulsering rounded-full bg-brand-600" />
            ) : (
              <span className="relative h-[22px] w-[22px] flex-none rounded-full border-2 border-brand-200 bg-white" />
            )}
            <div className={cx("flex flex-1 justify-between gap-2 text-sm", s.state === "current" && "font-semibold", s.state === "pending" && "text-ink-muted")}>
              <span>{t(`track.stages.${s.status}`)}</span>
              <span className={cx("text-xs", s.state === "current" ? "text-brand-700" : "text-ink-muted")}>{shortDate(s.date, i18n.language)}</span>
            </div>
          </motion.li>
        ))}
      </ol>
    </div>
  );
}

function Nps({ order, onDone }: { order: Order; onDone: (o: Order) => void }) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState<number | null>(null);
  if (order.nps !== null) return <div className="card p-4 text-sm font-medium text-ok-text">{t("track.npsThanks")}</div>;
  const send = async (score: number) => {
    setBusy(score);
    try {
      onDone(await api.nps(order.id, score));
    } finally {
      setBusy(null);
    }
  };
  return (
    <div className="card p-4">
      <p className="text-sm font-semibold">{t("track.npsTitle")}</p>
      <div className="mt-3 grid grid-cols-11 gap-1">
        {Array.from({ length: 11 }, (_, n) => (
          <button
            key={n}
            type="button"
            disabled={busy !== null}
            onClick={() => send(n)}
            className={cx("grid h-11 place-items-center rounded-lg text-xs font-semibold transition hover:-translate-y-0.5", n <= 6 ? "bg-[#F4F1FF] text-ink-soft" : n <= 8 ? "bg-brand-100 text-brand-700" : "bg-brand-600 text-white")}
          >
            {busy === n ? <Spinner className="h-3 w-3" /> : n}
          </button>
        ))}
      </div>
      <div className="mt-1.5 flex justify-between text-[11px] text-ink-muted">
        <span>{t("track.npsLow")}</span>
        <span>{t("track.npsHigh")}</span>
      </div>
    </div>
  );
}

function Referral({ orderId }: { orderId: string }) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [state, setState] = useState<"idle" | "busy" | "done">("idle");
  const [error, setError] = useState<unknown>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setState("busy");
    setError(null);
    try {
      await api.referral({ order_id: orderId, business_name: name.trim(), phone: phone.trim() });
      setState("done");
    } catch (err) {
      setError(err);
      setState("idle");
    }
  };
  return (
    <div className="relative overflow-hidden rounded-[22px] bg-gradient-to-br from-brand-600 to-brand-800 p-4 text-white">
      <div aria-hidden className="dots-soft absolute inset-0" />
      <div className="relative flex items-center gap-3">
        <span className="grid h-11 w-11 place-items-center rounded-2xl bg-white/20"><Gift /></span>
        <div>
          <p className="font-display font-bold">{t("track.referTitle")}</p>
          <p className="text-[13px] text-[#DCD3FF]">{t("track.referBody")}</p>
        </div>
      </div>
      {state === "done" ? (
        <p className="relative mt-3 rounded-xl bg-white/15 px-3 py-2.5 text-sm">{t("track.referDone")}</p>
      ) : (
        <form onSubmit={submit} className="relative mt-3 flex flex-col gap-2">
          <label className="sr-only" htmlFor="ref-name">{t("track.referName")}</label>
          <input id="ref-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder={t("track.referName")} className="min-h-[44px] rounded-xl border border-white/25 bg-white/10 px-3 text-sm text-white placeholder:text-white/60 focus:bg-white/15 focus:outline-none" />
          <label className="sr-only" htmlFor="ref-phone">{t("track.referPhone")}</label>
          <input id="ref-phone" required inputMode="tel" pattern="[6-9][0-9]{9}" maxLength={10} value={phone} onChange={(e) => setPhone(e.target.value.replace(/\D/g, ""))} placeholder={t("track.referPhone")} className="min-h-[44px] rounded-xl border border-white/25 bg-white/10 px-3 text-sm text-white placeholder:text-white/60 focus:bg-white/15 focus:outline-none" />
          {error != null && <p className="text-xs text-[#FFD0D6]">{error instanceof Error ? error.message : String(error)}</p>}
          <button type="submit" disabled={state === "busy"} className="btn min-h-[44px] bg-white text-brand-800 hover:bg-brand-50">
            {state === "busy" ? <Spinner className="h-4 w-4" /> : t("track.referSend")}
          </button>
        </form>
      )}
    </div>
  );
}

function FindOrder() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const [id, setId] = useState("");
  return (
    <AppShell back="/" title={t("nav.track")}>
      <form
        className="card m-4 flex flex-col gap-3 p-4"
        onSubmit={(e) => {
          e.preventDefault();
          if (id.trim()) nav(`/track/${id.trim()}`);
        }}
      >
        <label htmlFor="oid" className="text-xs font-semibold text-ink-muted">{t("privacy.orderId")}</label>
        <input id="oid" value={id} onChange={(e) => setId(e.target.value)} className="input font-mono" />
        <button type="submit" className="btn-primary">{t("common.continue")} <ArrowRight size={16} /></button>
      </form>
    </AppShell>
  );
}

export default function Track() {
  const { orderId } = useParams();
  if (!orderId) return <FindOrder />;
  return <TrackOrder orderId={orderId} />;
}

function TrackOrder({ orderId }: { orderId: string }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const [params] = useSearchParams();
  const demo = params.get("demo") === "1";
  const o = useLoad(() => api.order(orderId), [orderId]);
  const [demoBusy, setDemoBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") api.order(orderId).then(o.set, () => undefined);
    }, 15000);
    return () => window.clearInterval(timer);
  }, [orderId]);

  const order = o.data;
  if (!order) {
    const notFound = o.error instanceof ApiError && o.error.status === 404;
    return (
      <AppShell back="/" title={t("nav.track")}>
        <div className="p-4">
          {o.error ? notFound ? <div className="card p-5 text-sm text-ink-muted">{t("track.notFound")}</div> : <ErrorState error={o.error} onRetry={o.reload} /> : <PageLoader />}
        </div>
      </AppShell>
    );
  }

  const runDemo = async (fn: (id: string) => Promise<Order>) => {
    setDemoBusy(true);
    try {
      o.set(await fn(order.id));
    } finally {
      setDemoBusy(false);
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/track/${order.id}`);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard blocked */
    }
  };

  const activated = order.status === "ACTIVATED";

  return (
    <AppShell
      back="/"
      title={t("track.order", { code: order.short_code })}
      subtitle={[order.bundle_name, order.city].filter(Boolean).join(" · ")}
      right={
        <button type="button" onClick={copy} aria-label={t("track.copy")} className="grid h-11 w-11 place-items-center rounded-2xl bg-white/80 text-ink transition hover:bg-white">
          {copied ? <Check size={18} className="text-ok" /> : <LinkIcon size={18} />}
        </button>
      }
    >
      <div className="flex flex-col gap-3 px-4 pb-8 pt-2">
        <div className="flex flex-wrap items-center gap-2">
          {order.next_update_by && !activated && <Pill tone="white">{t("track.nextUpdate", { time: clockTime(order.next_update_by, lang) })}</Pill>}
          <Pill tone="brand">{rupees(order.monthly_total)}{t("common.perMonth")}</Pill>
          {copied && <Pill tone="ok">{t("track.copied")}</Pill>}
        </div>

        <AnimatePresence>
          {order.delay && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex gap-3 rounded-[18px] border border-warn-line bg-warn-bg p-3.5 text-[13px] leading-relaxed text-[#6B3A00]">
              <Alert size={20} className="mt-0.5 flex-none text-warn" />
              <div>
                <strong className="block text-warn-text">{t("track.delayTitle", { date: shortDate(order.delay.new_date, lang) })}</strong>
                {pick(order.delay, "reason", lang)} {t("track.credit", { amount: rupees(order.delay.credit_inr) })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <Stages order={order} />

        {order.technician && !activated && (
          <Reveal y={14} className="flex items-center gap-3 rounded-[22px] bg-gradient-to-br from-brand-600 to-brand-800 p-3.5 text-white">
            <span className="grid h-12 w-12 place-items-center rounded-full bg-white/20 font-display font-extrabold">{order.technician.name.charAt(0)}</span>
            <div className="min-w-0 flex-1">
              <div className="font-semibold">{order.technician.name} · {t("track.technician")}</div>
              <div className="text-xs text-[#DCD3FF]">{pick(order.technician, "visit", lang)}</div>
            </div>
            <a href="tel:198" aria-label={t("track.call")} className="grid h-11 w-11 place-items-center rounded-2xl bg-white text-brand-800">
              <Phone size={18} />
            </a>
          </Reveal>
        )}

        {activated && (
          <>
            <Nps order={order} onDone={o.set} />
            <Referral orderId={order.id} />
          </>
        )}

        {order.notifications.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="eyebrow">{t("track.updates")}</span>
            <AnimatePresence initial={false}>
              {order.notifications.map((n) => (
                <motion.div
                  key={n.id}
                  layout
                  initial={{ opacity: 0, y: 10, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  className="max-w-[88%] self-start rounded-[4px_16px_16px_16px] bg-white px-3 py-2.5 text-[13px] leading-relaxed shadow-[0_4px_14px_rgba(74,47,214,.08)]"
                >
                  {pick(n, "text", lang)}
                  <div className="mt-1 text-right text-[11px] text-ink-muted">{clockTime(n.created_at, lang)}</div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}

        {demo && (
          <div className="mt-2 rounded-[18px] border border-dashed border-brand-300 p-3">
            <span className="eyebrow">{t("track.demo")}</span>
            <div className="mt-2 grid grid-cols-2 gap-2">
              <button type="button" disabled={demoBusy || activated} onClick={() => runDemo(api.advance)} className="btn-outline min-h-[44px] text-[13px]">
                {t("track.advance")}
              </button>
              <button type="button" disabled={demoBusy || activated || !!order.delay} onClick={() => runDemo(api.delay)} className="btn-outline min-h-[44px] text-[13px]">
                {t("track.simulateDelay")}
              </button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
