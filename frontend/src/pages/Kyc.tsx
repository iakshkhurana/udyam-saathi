import { AnimatePresence, motion } from "framer-motion";
import { useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { Check, Cross, Upload } from "../components/Icons";
import { ErrorState, Pill, Reveal, Spinner, StatusIcon } from "../components/ui";
import { api } from "../lib/api";
import { cx, pick } from "../lib/format";
import type { CheckStatus, DocType, GstinLookup, KycDocResult, KycVerifyResult, UdyamLookup } from "../lib/types";

const DOCS: DocType[] = ["gst_certificate", "udyam_certificate", "signatory_id", "address_proof"];
const SAMPLES = Array.from({ length: 12 }, (_, i) => `K${String(i + 1).padStart(2, "0")}`);

type DocState = { uploading: boolean; result?: KycDocResult; error?: string };

const TILE_BORDER: Record<CheckStatus, string> = { pass: "border-ok-line", warn: "border-warn-line", fail: "border-bad-line" };
const TILE_TEXT: Record<CheckStatus, string> = { pass: "text-ok-text", warn: "text-warn-text", fail: "text-bad-text" };

function DocTile({ type, state, onFile }: { type: DocType; state: DocState; onFile: (f: File) => void }) {
  const { t, i18n } = useTranslation();
  const input = useRef<HTMLInputElement>(null);
  const r = state.result;
  const failedChecks = r?.checks.filter((c) => c.status !== "pass") ?? [];
  return (
    <motion.button
      type="button"
      layout
      onClick={() => input.current?.click()}
      disabled={state.uploading}
      className={cx(
        "relative flex min-h-[132px] flex-col items-start gap-1.5 overflow-hidden rounded-[18px] border p-3 text-left transition",
        r ? cx("bg-white", TILE_BORDER[r.status]) : "border-[1.5px] border-dashed border-brand-300 bg-[#FBFAFF] hover:border-brand-500 hover:bg-white",
      )}
    >
      <input
        ref={input}
        type="file"
        accept="image/*,application/pdf"
        capture="environment"
        className="sr-only"
        tabIndex={-1}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />
      {state.uploading && <span aria-hidden className="absolute inset-x-2 h-0.5 animate-scan rounded bg-gradient-to-r from-transparent via-brand-500 to-transparent" />}
      {r ? (
        <StatusIcon status={r.status} />
      ) : (
        <span className="grid h-8 w-8 place-items-center rounded-[10px] bg-brand-50 text-brand-600">{state.uploading ? <Spinner className="h-4 w-4" /> : <Upload size={16} />}</span>
      )}
      <strong className="text-[13px]">{t(`kyc.docs.${type}`)}</strong>
      <span className={cx("text-xs leading-snug", r ? TILE_TEXT[r.status] : state.error ? "text-bad-text" : "text-brand-700")}>
        {state.uploading ? t("kyc.reading") : r ? pick(r, "message", i18n.language) : state.error ?? t("kyc.tapToUpload")}
      </span>
      {failedChecks.length > 1 && (
        <ul className="mt-0.5 flex flex-col gap-0.5 text-[11px] text-ink-muted">
          {failedChecks.slice(1).map((c) => (
            <li key={c.name}>• {pick(c, "message", i18n.language)}</li>
          ))}
        </ul>
      )}
    </motion.button>
  );
}

function BusinessCard({ g, confirmed, onConfirm }: { g: GstinLookup; confirmed: boolean; onConfirm: () => void }) {
  const { t } = useTranslation();
  if (g.status === "Invalid") return <p className="mt-2 text-[13px] text-bad-text">{t("kyc.invalidGstin")}</p>;
  if (g.status === "NotFound") return <p className="mt-2 text-[13px] text-bad-text">{t("kyc.notFoundGstin")}</p>;
  const active = g.status === "Active";
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-3 rounded-2xl border border-[#E6DFFF] bg-gradient-to-br from-brand-50 to-white p-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <strong className="text-[15px]">{g.trade_name || g.legal_name}</strong>
          {g.trade_name && g.legal_name && g.trade_name !== g.legal_name && <div className="text-xs text-ink-muted">{g.legal_name}</div>}
        </div>
        <Pill tone={active ? "ok" : "warn"}>{t(`kyc.status.${g.status}`)}</Pill>
      </div>
      {g.address && <p className="mt-1 text-xs leading-relaxed text-[#4A4766]">{g.address}</p>}
      {!active && <p className="mt-2 text-xs text-warn-text">{t("kyc.inactiveGstin", { status: t(`kyc.status.${g.status}`) })}</p>}
      <button
        type="button"
        onClick={onConfirm}
        disabled={confirmed}
        className={cx("mt-2.5 flex min-h-[40px] w-full items-center justify-center gap-1.5 rounded-[10px] text-[13px] font-semibold transition", confirmed ? "bg-ok-bg text-ok-text" : "border border-brand-300 bg-white text-brand-700 hover:bg-brand-50")}
      >
        <Check size={16} /> {confirmed ? t("kyc.confirmed") : t("kyc.thisIsMine")}
      </button>
    </motion.div>
  );
}

function OtpSheet({ onClose, onDone, orderId }: { onClose: () => void; onDone: () => void; orderId: string }) {
  const { t } = useTranslation();
  const [otp, setOtp] = useState("");
  const [busy, setBusy] = useState(false);
  const [wrong, setWrong] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setWrong(false);
    try {
      const r = await api.kycEsign(orderId, otp);
      if (r.ok) onDone();
      else setWrong(true);
    } catch {
      setWrong(true);
    } finally {
      setBusy(false);
    }
  };
  return (
    <motion.div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      <motion.form
        role="dialog"
        aria-modal="true"
        aria-labelledby="otp-title"
        onSubmit={submit}
        onClick={(e) => e.stopPropagation()}
        initial={{ y: 80 }}
        animate={{ y: 0 }}
        exit={{ y: 80 }}
        transition={{ type: "spring", stiffness: 380, damping: 34 }}
        className="w-full max-w-[430px] rounded-t-[28px] bg-white p-5 pb-8"
      >
        <div className="flex items-center justify-between">
          <h2 id="otp-title" className="text-lg font-bold">{t("kyc.otpTitle")}</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="grid h-11 w-11 place-items-center rounded-2xl text-ink-muted hover:bg-brand-50">
            <Cross />
          </button>
        </div>
        <p className="text-xs text-ink-muted">{t("kyc.otpHint")}</p>
        <label htmlFor="otp" className="sr-only">OTP</label>
        <input
          id="otp"
          autoFocus
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
          className="input mt-4 text-center font-mono text-2xl tracking-[.5em]"
        />
        {wrong && <p className="mt-2 text-[13px] text-bad-text">{t("kyc.otpWrong")}</p>}
        <button type="submit" disabled={otp.length !== 6 || busy} className="btn-primary mt-4 min-h-[52px] w-full">
          {busy ? <Spinner /> : t("kyc.confirm")}
        </button>
      </motion.form>
    </motion.div>
  );
}

export default function Kyc() {
  const { orderId = "" } = useParams();
  const { t, i18n } = useTranslation();
  const nav = useNavigate();
  const [gstin, setGstin] = useState("");
  const [udyam, setUdyam] = useState("");
  const [noUdyam, setNoUdyam] = useState(false);
  const [g, setG] = useState<GstinLookup | null>(null);
  const [u, setU] = useState<UdyamLookup | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [looking, setLooking] = useState(false);
  const [docs, setDocs] = useState<Record<DocType, DocState>>(() => Object.fromEntries(DOCS.map((d) => [d, { uploading: false }])) as Record<DocType, DocState>);
  const [sample, setSample] = useState("");
  const [sampleBusy, setSampleBusy] = useState(false);
  const [digi, setDigi] = useState<"idle" | "busy" | "done">("idle");
  const [verify, setVerify] = useState<KycVerifyResult | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [otpOpen, setOtpOpen] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const lookup = async (e?: FormEvent) => {
    e?.preventDefault();
    if (!gstin.trim()) return;
    setLooking(true);
    setError(null);
    setConfirmed(false);
    try {
      const r = await api.kycIdentifiers(orderId, { gstin: gstin.trim(), udyam: noUdyam ? undefined : udyam.trim() || undefined, no_udyam: noUdyam });
      setG(r.gstin);
      setU(r.udyam);
    } catch (err) {
      setError(err);
    } finally {
      setLooking(false);
    }
  };

  const upload = async (type: DocType, file: File) => {
    setVerify(null);
    setDocs((d) => ({ ...d, [type]: { uploading: true } }));
    try {
      const result = await api.kycUpload(orderId, type, file);
      setDocs((d) => ({ ...d, [type]: { uploading: false, result } }));
    } catch (err) {
      setDocs((d) => ({ ...d, [type]: { uploading: false, error: err instanceof Error ? err.message : String(err) } }));
    }
  };

  const loadSample = async (id: string) => {
    setSample(id);
    if (!id) return;
    setSampleBusy(true);
    setError(null);
    setVerify(null);
    setDocs(Object.fromEntries(DOCS.map((d) => [d, { uploading: true }])) as Record<DocType, DocState>);
    try {
      const r = await api.kycSample(orderId, id);
      setGstin(r.gstin?.gstin ?? "");
      setUdyam(r.udyam?.udyam ?? "");
      setNoUdyam(!r.udyam);
      setG(r.gstin);
      setU(r.udyam);
      setConfirmed(!!r.gstin?.found);
      setDocs(Object.fromEntries(DOCS.map((d) => [d, { uploading: false, result: r.documents.find((x) => x.doc_type === d) }])) as Record<DocType, DocState>);
    } catch (err) {
      setError(err);
      setDocs(Object.fromEntries(DOCS.map((d) => [d, { uploading: false }])) as Record<DocType, DocState>);
    } finally {
      setSampleBusy(false);
    }
  };

  const runVerify = async () => {
    setVerifying(true);
    setError(null);
    try {
      const r = await api.kycVerify(orderId);
      setVerify(r);
      setDocs((d) => {
        const next = { ...d };
        for (const doc of r.documents) next[doc.doc_type] = { uploading: false, result: doc };
        return next;
      });
    } catch (err) {
      setError(err);
    } finally {
      setVerifying(false);
    }
  };

  const fetchDigilocker = () => {
    setDigi("busy");
    window.setTimeout(() => setDigi("done"), 1200);
  };

  const allUploaded = DOCS.every((d) => docs[d].result);
  const canVerify = confirmed && allUploaded && (noUdyam || !!u?.found);
  const canSign = verify && verify.status !== "KYC_FAILED";
  const lang = i18n.language;

  const resultCard = verify && (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={cx(
        "rounded-[20px] p-4",
        verify.status === "KYC_VERIFIED" ? "bg-ok-bg text-ok-text" : verify.status === "KYC_REVIEW" ? "bg-warn-bg text-warn-text" : "bg-bad-bg text-bad-text",
      )}
    >
      <strong className="block font-display text-[15px]">
        {verify.status === "KYC_VERIFIED" ? t("kyc.resultVerified") : verify.status === "KYC_REVIEW" ? t("kyc.resultReview") : t("kyc.resultFailed")}
      </strong>
      {verify.status !== "KYC_VERIFIED" && (
        <p className="mt-1 text-[13px]">{verify.status === "KYC_REVIEW" ? t("kyc.resultReviewBody") : t("kyc.resultFailedBody")}</p>
      )}
      {verify.checks.filter((c) => c.status !== "pass").length > 0 && (
        <ul className="mt-2 flex flex-col gap-1 text-[12px]">
          {verify.checks.filter((c) => c.status !== "pass").map((c) => (
            <li key={c.name}>• {pick(c, "message", lang)}</li>
          ))}
        </ul>
      )}
    </motion.div>
  );

  return (
    <AppShell
      back
      title={t("kyc.title")}
      subtitle={t("kyc.step")}
      progress={canSign ? 2 : 1 + (DOCS.filter((d) => docs[d].result).length + (confirmed ? 1 : 0)) / 5}
      footer={
        <div className="flex flex-col gap-2">
          {canSign ? (
            <button type="button" onClick={() => setOtpOpen(true)} className="btn-primary min-h-[54px] w-full">
              {t("kyc.esign")}
            </button>
          ) : (
            <button type="button" onClick={runVerify} disabled={!canVerify || verifying} className="btn-primary min-h-[54px] w-full">
              {verifying ? <Spinner /> : t("kyc.verify")}
            </button>
          )}
          <span className="text-center text-xs text-ink-muted">{t("kyc.footer")}</span>
        </div>
      }
    >
      <div className="flex flex-col gap-3 px-4 pb-6 pt-2">
        <Reveal y={14} className="card p-3.5">
          <form onSubmit={lookup}>
            <label htmlFor="gstin" className="text-xs font-semibold text-ink-muted">{t("kyc.gstin")}</label>
            <div className="mt-1.5 flex gap-2">
              <input
                id="gstin"
                value={gstin}
                maxLength={15}
                autoCapitalize="characters"
                spellCheck={false}
                placeholder="27AAAAA0000A1Z5"
                onChange={(e) => setGstin(e.target.value.toUpperCase().replace(/\s/g, ""))}
                className="input font-mono tracking-[.04em]"
              />
              <button type="submit" disabled={looking || gstin.length < 15} className="btn-dark min-h-[46px] flex-none rounded-xl px-4 text-sm">
                {looking ? <Spinner className="h-4 w-4" /> : t("kyc.lookup")}
              </button>
            </div>
          </form>
          {g && <BusinessCard g={g} confirmed={confirmed} onConfirm={() => setConfirmed(true)} />}

          <div className="mt-4">
            <div className="flex items-center justify-between">
              <label htmlFor="udyam" className="text-xs font-semibold text-ink-muted">{t("kyc.udyam")}</label>
              <label className="flex cursor-pointer items-center gap-1.5 text-xs text-ink-muted">
                <input type="checkbox" checked={noUdyam} onChange={(e) => setNoUdyam(e.target.checked)} className="h-4 w-4 accent-brand-600" />
                {t("kyc.noUdyam")}
              </label>
            </div>
            {!noUdyam && (
              <input
                id="udyam"
                value={udyam}
                spellCheck={false}
                placeholder="UDYAM-MH-00-0000000"
                onChange={(e) => setUdyam(e.target.value.toUpperCase())}
                onBlur={() => gstin.length === 15 && udyam && void lookup()}
                className="input mt-1.5 font-mono tracking-[.02em]"
              />
            )}
            {u && !noUdyam && (
              <p className={cx("mt-2 text-[13px]", u.found ? "text-ok-text" : "text-bad-text")}>
                {u.found ? `✓ ${u.enterprise_name} · ${u.enterprise_type} · ${u.city}` : t("kyc.udyamNotFound")}
              </p>
            )}
          </div>
        </Reveal>

        <div className="flex items-center justify-between">
          <span className="eyebrow">{t("kyc.documents")}</span>
          <button type="button" onClick={fetchDigilocker} disabled={digi !== "idle"} className="btn-outline min-h-[36px] rounded-[10px] px-3 text-xs">
            {digi === "busy" ? <Spinner className="h-3.5 w-3.5" /> : digi === "done" ? <Check size={14} /> : null}
            {digi === "done" ? t("kyc.digilockerDone") : t("kyc.digilocker")}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          {DOCS.map((d, i) => (
            <Reveal key={d} y={14} delay={i * 0.06}>
              <DocTile type={d} state={docs[d]} onFile={(f) => upload(d, f)} />
            </Reveal>
          ))}
        </div>

        {resultCard}
        {error != null && <ErrorState error={error} />}

        <div className="mt-1 flex flex-col gap-1.5">
          <label htmlFor="sample" className="text-xs font-semibold text-ink-muted">{t("kyc.sample")}</label>
          <div className="relative">
            <select id="sample" value={sample} disabled={sampleBusy} onChange={(e) => loadSample(e.target.value)} className="input appearance-none pr-10">
              <option value="">{t("kyc.samplePick")}</option>
              {SAMPLES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            {sampleBusy && <Spinner className="absolute right-3 top-3.5 h-4 w-4 text-brand-600" />}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {otpOpen && <OtpSheet orderId={orderId} onClose={() => setOtpOpen(false)} onDone={() => nav(`/track/${orderId}`)} />}
      </AnimatePresence>
    </AppShell>
  );
}
