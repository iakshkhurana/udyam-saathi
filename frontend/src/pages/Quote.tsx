import { animate, AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { Alert, ArrowRight, Printer, Share } from "../components/Icons";
import { ErrorState, PageLoader, Rise, Spinner, Stepper, Toggle, useLoad } from "../components/ui";
import { api } from "../lib/api";
import { pick, pickList, rupees } from "../lib/format";
import type { BundleItem } from "../lib/types";

const FIXED_QTY_UNITS = new Set(["per account", "per pack", "per number"]);

function AnimatedRupees({ value }: { value: number }) {
  const [shown, setShown] = useState(value);
  const from = useRef(value);
  useEffect(() => {
    const c = animate(from.current, value, { duration: 0.6, ease: [0.2, 0.7, 0.2, 1], onUpdate: (v) => setShown(Math.round(v)) });
    from.current = value;
    return () => c.stop();
  }, [value]);
  return <>{rupees(shown)}</>;
}

function ItemRow({ item, busy, onPatch }: { item: BundleItem; busy: boolean; onPatch: (p: { enabled?: boolean; qty?: number }) => void }) {
  const { t, i18n } = useTranslation();
  const qtyEditable = !FIXED_QTY_UNITS.has(item.unit);
  return (
    <motion.div layout className="flex items-center gap-3 border-b border-[#F1EEFA] px-3.5 py-3 last:border-0">
      <div className={item.enabled ? "min-w-0 flex-1" : "min-w-0 flex-1 opacity-50"}>
        <div className="text-sm font-semibold">{item.name}</div>
        <div className="text-xs leading-snug text-ink-muted">{pick(item, "reason", i18n.language)}</div>
        <div className="mt-1 text-xs font-medium text-ink-soft">
          {item.qty > 1 ? `${rupees(item.unit_price)} × ${item.qty} = ` : ""}
          {rupees(item.monthly)}
          {t("common.perMonth")}
          {item.setup > 0 && <span className="text-ink-muted"> · {t("quote.setup")} {rupees(item.setup)}</span>}
        </div>
      </div>
      <div className="flex flex-none flex-col items-end gap-2">
        <Toggle checked={item.enabled} disabled={busy} label={item.name} onChange={(enabled) => onPatch({ enabled })} />
        {qtyEditable && item.enabled && (
          <Stepper value={item.qty} disabled={busy} lessLabel={t("quote.fewer")} moreLabel={t("quote.more")} onChange={(qty) => onPatch({ qty })} />
        )}
      </div>
    </motion.div>
  );
}

export default function QuotePage() {
  const { id = "" } = useParams();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const nav = useNavigate();
  const q = useLoad(() => api.getQuote(id), [id]);
  const [busy, setBusy] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const quote = q.data;

  const patch = async (product_id: string, p: { enabled?: boolean; qty?: number }) => {
    setBusy(true);
    setError(null);
    try {
      q.set(await api.patchQuote(id, [{ product_id, ...p }]));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  const accept = async () => {
    setAccepting(true);
    setError(null);
    try {
      const order = await api.acceptQuote(id);
      nav(`/consent/${order.id}`);
    } catch (e) {
      setError(e);
      setAccepting(false);
    }
  };

  if (!quote) {
    return (
      <AppShell back="/advisor" title={t("quote.title")}>
        <div className="p-4">{q.error ? <ErrorState error={q.error} onRetry={q.reload} /> : <PageLoader />}</div>
      </AppShell>
    );
  }

  const recommended = quote.items.filter((i) => !i.optional);
  const addons = quote.items.filter((i) => i.optional);
  const warnings = pickList(quote, "warnings", lang);
  const savings = pick(quote, "savings_line", lang);

  return (
    <AppShell
      className="[background:#F6F4FF]"
      footer={
        <div className="flex flex-col gap-2">
          {error != null && <ErrorState error={error} />}
          <button type="button" onClick={accept} disabled={accepting || busy} className="btn-primary min-h-[54px] w-full">
            {accepting ? <Spinner /> : <>{t("quote.accept")} <ArrowRight size={18} /></>}
          </button>
          <span className="text-center text-xs text-ink-muted">
            {t("quote.payLater")} · {pick(quote, "gst_note", lang)}
          </span>
        </div>
      }
    >
      <div className="relative overflow-hidden rounded-b-[30px] px-4 pb-6 pt-4 text-white [background:radial-gradient(420px_260px_at_80%_-40px,#9C82FF_0%,#5A3BF0_55%,#3F23C9_100%)]">
        <div aria-hidden className="dots-soft absolute inset-0" />
        <div className="no-print relative flex items-center justify-between">
          <button type="button" onClick={() => nav(-1)} aria-label={t("common.back")} className="grid h-11 w-11 place-items-center rounded-2xl bg-white/15 transition hover:bg-white/25">
            <ArrowRight size={20} className="rotate-180" />
          </button>
          <span className="font-display font-bold">{t("quote.title")}</span>
          <div className="flex gap-1.5">
            <a href={quote.whatsapp_url} target="_blank" rel="noreferrer" aria-label={t("quote.share")} className="grid h-11 w-11 place-items-center rounded-2xl bg-white/15 transition hover:bg-white/25">
              <Share />
            </a>
            <button type="button" onClick={() => window.print()} aria-label={t("quote.pdf")} className="grid h-11 w-11 place-items-center rounded-2xl bg-white/15 transition hover:bg-white/25">
              <Printer />
            </button>
          </div>
        </div>
        <Rise className="relative mt-5 text-[13px] text-[#DCD3FF]">{quote.bundle_name}</Rise>
        <Rise delay={0.06} className="relative flex items-baseline gap-2 font-display text-[46px] font-extrabold leading-tight tracking-[-0.03em]">
          <AnimatedRupees value={quote.monthly_total} />
          <span className="text-[15px] font-medium text-[#DCD3FF]">{t("common.perMonth")} {t("common.plusGst")}</span>
          {busy && <Spinner className="h-4 w-4 self-center text-white/70" />}
        </Rise>
        <Rise delay={0.12} className="relative mt-3.5 grid grid-cols-3 gap-2">
          {[
            [t("quote.setup"), rupees(quote.setup_total)],
            [t("quote.contract"), t("common.months", { count: quote.contract_months })],
            [t("quote.install"), t("common.days", { count: quote.install_days })],
          ].map(([k, v]) => (
            <div key={k} className="rounded-2xl border border-white/20 bg-white/15 px-3 py-2.5">
              <div className="text-[11px] text-[#DCD3FF]">{k}</div>
              <div className="font-semibold">{v}</div>
            </div>
          ))}
        </Rise>
      </div>

      <div className="flex flex-col gap-2.5 px-4 pb-6 pt-3.5">
        {savings && <Rise delay={0.16} className="rounded-2xl bg-ok-bg px-3.5 py-3 text-[13px] font-medium text-ok-text">{savings}</Rise>}
        <AnimatePresence>
          {warnings.map((w) => (
            <motion.div key={w} initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="flex gap-2 rounded-2xl bg-warn-bg px-3.5 py-3 text-[13px] text-warn-text">
              <Alert size={18} className="flex-none" /> {w}
            </motion.div>
          ))}
        </AnimatePresence>

        <div className="eyebrow mt-1">{t("quote.recommended")}</div>
        <Rise delay={0.2} className="card">
          {recommended.map((i) => (
            <ItemRow key={i.product_id} item={i} busy={busy} onPatch={(p) => patch(i.product_id, p)} />
          ))}
        </Rise>

        {addons.length > 0 && (
          <>
            <div className="eyebrow mt-1">{t("quote.addons")}</div>
            <Rise delay={0.26} className="flex flex-col gap-2.5">
              {addons.map((i) => (
                <div key={i.product_id} className={i.enabled ? "card border-[1.5px] border-brand-400 shadow-[0_10px_24px_-14px_rgba(90,59,240,.5)]" : "card"}>
                  <ItemRow item={i} busy={busy} onPatch={(p) => patch(i.product_id, p)} />
                </div>
              ))}
            </Rise>
          </>
        )}
      </div>
    </AppShell>
  );
}
