import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { Check, Shield } from "../components/Icons";
import { ErrorState, Pill, Reveal, Spinner } from "../components/ui";
import { api } from "../lib/api";
import { pick, shortDate } from "../lib/format";
import type { PrivacyView } from "../lib/types";

export default function Privacy() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const [params] = useSearchParams();
  const [id, setId] = useState(params.get("order") ?? "");
  const [view, setView] = useState<PrivacyView | null>(null);
  const [busy, setBusy] = useState<"find" | "withdraw" | "delete" | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);

  const load = async (orderId: string) => {
    setBusy("find");
    setError(null);
    try {
      setView(await api.privacy(orderId));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  };

  useEffect(() => {
    const fromLink = params.get("order");
    if (fromLink) void load(fromLink);
  }, []);

  const find = (e: FormEvent) => {
    e.preventDefault();
    setDone(null);
    if (id.trim()) void load(id.trim());
  };

  const act = async (kind: "withdraw" | "delete") => {
    if (!view) return;
    setBusy(kind);
    setError(null);
    try {
      const r = kind === "withdraw" ? await api.withdraw(view.order_id) : await api.deleteData(view.order_id);
      setDone(t(kind === "withdraw" ? "privacy.doneWithdraw" : "privacy.doneDelete", { count: r.documents_deleted }));
      setConfirmDelete(false);
      setView(await api.privacy(view.order_id));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  };

  const activeConsent = view?.consents.some((c) => !c.withdrawn);
  const rows: [string, string][] = view
    ? [
        [t("privacy.status"), view.status],
        [t("privacy.gstin"), view.gstin ?? "—"],
        [t("privacy.udyam"), view.udyam ?? "—"],
        [t("privacy.kycResult"), view.kyc_result ?? "—"],
      ]
    : [];

  return (
    <AppShell back="/" title={t("privacy.title")}>
      <div className="flex flex-col gap-3 px-4 pb-8 pt-2">
        <Reveal y={14} className="flex items-start gap-3 rounded-[22px] bg-gradient-to-br from-brand-600 to-brand-800 p-4 text-white">
          <span className="grid h-10 w-10 flex-none place-items-center rounded-xl bg-white/20"><Shield /></span>
          <div>
            <p className="text-sm leading-relaxed text-[#E9E4FF]">{t("privacy.sub")}</p>
            <p className="mt-2 text-xs text-[#C9BCFF]">{t("privacy.never")}</p>
          </div>
        </Reveal>

        <form onSubmit={find} className="card flex flex-col gap-2 p-4">
          <label htmlFor="pid" className="text-xs font-semibold text-ink-muted">{t("privacy.orderId")}</label>
          <div className="flex gap-2">
            <input id="pid" value={id} onChange={(e) => setId(e.target.value.toUpperCase())} spellCheck={false} className="input font-mono" />
            <button type="submit" disabled={!id.trim() || busy !== null} className="btn-dark min-h-[46px] flex-none rounded-xl px-4 text-sm">
              {busy === "find" ? <Spinner className="h-4 w-4" /> : t("privacy.find")}
            </button>
          </div>
        </form>

        {error != null && <ErrorState error={error} />}
        {done && (
          <Pill tone="ok" className="self-start px-3 py-2 text-xs">
            <Check size={14} /> {done}
          </Pill>
        )}

        <AnimatePresence>
          {view && (
            <motion.div key={view.order_id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-3">
              <div className="card p-4">
                <span className="eyebrow">{t("privacy.holding")}</span>
                <dl className="mt-2 text-sm">
                  {rows.map(([k, v]) => (
                    <div key={k} className="flex justify-between gap-3 border-b border-[#F1EEFA] py-2.5 last:border-0">
                      <dt className="text-ink-muted">{k}</dt>
                      <dd className="text-right font-mono text-[13px] font-medium">{v}</dd>
                    </div>
                  ))}
                </dl>
                <div className="mt-3 text-xs font-semibold text-ink-muted">{t("privacy.documents")}</div>
                {view.documents.length ? (
                  <ul className="mt-1.5 flex flex-col gap-1 text-[13px]">
                    {view.documents.map((d) => (
                      <li key={d.type} className="flex justify-between">
                        <span>{t(`kyc.docs.${d.type}`)}</span>
                        <span className={d.stored ? "text-ink-soft" : "text-ink-muted line-through"}>
                          {shortDate(d.uploaded.slice(0, 10), lang)} · {d.stored ? t("privacy.stored") : t("privacy.deleted")}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-1 text-[13px] text-ink-muted">{t("privacy.noDocs")}</p>
                )}
                <div className="mt-3 text-xs font-semibold text-ink-muted">{t("privacy.consents")}</div>
                <ul className="mt-1.5 flex flex-col gap-1.5 text-[13px]">
                  {view.consents.map((c) => (
                    <li key={c.given} className="flex items-start justify-between gap-2">
                      <span className="text-ink-soft">{c.purposes.join(", ").replace(/_/g, " ")}</span>
                      <Pill tone={c.withdrawn ? "warn" : "ok"}>{c.withdrawn ? t("privacy.withdrawn") : t("privacy.active")}</Pill>
                    </li>
                  ))}
                </ul>
                <p className="mt-3 rounded-xl bg-brand-50 px-3 py-2 text-xs text-brand-700">{pick(view, "retention", lang)}</p>
              </div>

              <div className="card p-4">
                <p className="text-sm font-semibold">{t("privacy.withdraw")}</p>
                <p className="mt-1 text-[13px] text-ink-muted">{t("privacy.withdrawBody")}</p>
                <button type="button" disabled={busy !== null || !activeConsent} onClick={() => act("withdraw")} className="btn-outline mt-3 min-h-[44px] w-full text-sm">
                  {busy === "withdraw" ? <Spinner className="h-4 w-4" /> : t("privacy.withdraw")}
                </button>
              </div>

              <div className="card border-bad-line p-4">
                <p className="text-sm font-semibold text-bad-text">{t("privacy.delete")}</p>
                <p className="mt-1 text-[13px] text-ink-muted">{t("privacy.deleteBody")}</p>
                {confirmDelete ? (
                  <button type="button" disabled={busy !== null} onClick={() => act("delete")} className="btn mt-3 min-h-[44px] w-full bg-bad text-sm text-white hover:bg-bad-text">
                    {busy === "delete" ? <Spinner className="h-4 w-4" /> : t("privacy.confirmDelete")}
                  </button>
                ) : (
                  <button type="button" onClick={() => setConfirmDelete(true)} className="btn mt-3 min-h-[44px] w-full border border-bad-line bg-white text-sm text-bad-text hover:bg-bad-bg">
                    {t("privacy.delete")}
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AppShell>
  );
}
