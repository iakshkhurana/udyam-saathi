import { motion } from "framer-motion";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { ArrowRight, Check, Clock, DocCheck, Lock, Shield, Lines } from "../components/Icons";
import { ErrorState, Reveal, Spinner } from "../components/ui";
import { api } from "../lib/api";
import { cx } from "../lib/format";

function Checkbox({ checked, onChange, label, hint }: { checked: boolean; onChange: (v: boolean) => void; label: string; hint: string }) {
  return (
    <label className={cx("flex min-h-[56px] cursor-pointer items-center gap-3 rounded-2xl border bg-white px-4 py-3 transition", checked ? "border-brand-400 shadow-[0_10px_24px_-16px_rgba(90,59,240,.6)]" : "border-line")}>
      <input type="checkbox" className="peer sr-only" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className={cx("grid h-6 w-6 flex-none place-items-center rounded-lg border-2 transition peer-focus-visible:ring-2 peer-focus-visible:ring-brand-500", checked ? "border-brand-600 bg-brand-600 text-white" : "border-[#CFC7EE] bg-white")}>
        {checked && (
          <motion.span initial={{ scale: 0.4 }} animate={{ scale: 1 }}>
            <Check size={16} strokeWidth={3} />
          </motion.span>
        )}
      </span>
      <span className="flex-1 text-sm font-medium">{label}</span>
      <span className="text-[11px] font-semibold text-ink-muted">{hint}</span>
    </label>
  );
}

export default function Consent() {
  const { orderId = "" } = useParams();
  const { t, i18n } = useTranslation();
  const nav = useNavigate();
  const [kyc, setKyc] = useState(false);
  const [marketing, setMarketing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const sections = [
    { icon: <DocCheck />, title: t("consent.whatT"), body: t("consent.what") },
    { icon: <Lines />, title: t("consent.whyT"), body: t("consent.why") },
    { icon: <Lock />, title: t("consent.whoT"), body: t("consent.who") },
    { icon: <Clock />, title: t("consent.howLongT"), body: t("consent.howLong") },
  ];

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.giveConsent({ order_id: orderId, kyc, marketing_whatsapp: marketing, language: i18n.language });
      nav(`/kyc/${orderId}`);
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  return (
    <AppShell
      back
      title={t("consent.title")}
      subtitle={t("consent.step")}
      progress={0.6}
      footer={
        <div className="flex flex-col gap-2">
          {error != null && <ErrorState error={error} />}
          <button type="button" disabled={!kyc || busy} onClick={submit} className="btn-primary min-h-[54px] w-full">
            {busy ? <Spinner /> : <>{t("consent.agree")} <ArrowRight size={18} /></>}
          </button>
        </div>
      }
    >
      <div className="flex flex-col gap-3 px-4 pb-6 pt-2">
        <Reveal className="flex items-start gap-3 rounded-[22px] bg-gradient-to-br from-brand-600 to-brand-800 p-4 text-white">
          <span className="grid h-10 w-10 flex-none place-items-center rounded-xl bg-white/20"><Shield /></span>
          <p className="text-sm leading-relaxed text-[#E9E4FF]">{t("consent.sub")}</p>
        </Reveal>

        {sections.map((s, i) => (
          <Reveal key={s.title} delay={i * 0.06} y={16} className="card flex gap-3 p-4">
            <span className="grid h-9 w-9 flex-none place-items-center rounded-xl bg-brand-50 text-brand-600">{s.icon}</span>
            <div>
              <h2 className="text-[15px] font-bold">{s.title}</h2>
              <p className="mt-1 text-[13px] leading-relaxed text-[#4A4766]">{s.body}</p>
            </div>
          </Reveal>
        ))}

        <Reveal delay={0.24} y={16} className="card p-4 text-[13px] leading-relaxed text-[#4A4766]">
          <h2 className="text-[15px] font-bold text-ink">{t("consent.rightsT")}</h2>
          <p className="mt-1">
            {t("consent.rights")}{" "}
            <Link to={`/privacy?order=${orderId}`} className="font-semibold text-brand-700 underline underline-offset-2">
              {t("consent.rightsLink")}
            </Link>
            .
          </p>
        </Reveal>

        <div className="mt-1 flex flex-col gap-2">
          <Checkbox checked={kyc} onChange={setKyc} label={t("consent.kyc")} hint={t("consent.kycReq")} />
          <Checkbox checked={marketing} onChange={setMarketing} label={t("consent.marketing")} hint={t("consent.marketingOpt")} />
        </div>
      </div>
    </AppShell>
  );
}
