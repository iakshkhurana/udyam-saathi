import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { ArrowRight, Check, Mic, Phone, Refresh } from "../components/Icons";
import { ErrorState, Pill, Spinner } from "../components/ui";
import { getChatLang } from "../i18n";
import { api } from "../lib/api";
import { cx, pick, rupees } from "../lib/format";
import type { AdvisorTurn, Bundle, Chip } from "../lib/types";

type Msg = { id: number; from: "bot" | "me"; text: string; bundle?: Bundle | null };

const SPEECH_LANG: Record<string, string> = {
  en: "en-IN", hi: "hi-IN", ta: "ta-IN", te: "te-IN", kn: "kn-IN", bn: "bn-IN", mr: "mr-IN", gu: "gu-IN", pa: "pa-IN", ml: "ml-IN",
};

type SpeechRec = {
  lang: string;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
};

function getRecognizer(): (new () => SpeechRec) | null {
  const w = window as unknown as Record<string, unknown>;
  return (w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null) as (new () => SpeechRec) | null;
}

function BundleCard({ bundle, noGst, onQuote, busy }: { bundle: Bundle; noGst: boolean; onQuote: () => void; busy: boolean }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const items = bundle.items.filter((i) => i.enabled);
  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.2, 0.7, 0.2, 1] }}
      className="mt-1 rounded-[22px] border border-[#E6DFFF] bg-white p-4 shadow-[0_18px_36px_-18px_rgba(74,47,214,.45)]"
    >
      <div className="flex items-center justify-between">
        <span className="eyebrow text-[11px]">{t("advisor.yourBundle")}</span>
        {noGst && <Pill tone="ok">{t("advisor.noGst")}</Pill>}
      </div>
      <div className="mt-1.5 font-display text-[19px] font-bold">{bundle.bundle_name}</div>
      <div className="font-display text-[28px] font-extrabold tracking-[-0.02em]">
        {rupees(bundle.monthly_total)}
        <span className="text-[13px] font-medium text-ink-muted"> {t("common.perMonth")} {t("common.plusGst")}</span>
      </div>
      <ul className="mt-2.5 flex flex-col gap-1.5 text-[13px] text-ink-soft">
        {items.map((i) => (
          <li key={i.product_id} className="flex gap-2">
            <Check size={16} className="mt-0.5 flex-none text-brand-600" />
            <span>
              {i.name}
              {i.qty > 1 && <span className="text-ink-muted"> × {i.qty}</span>}
              <span className="block text-xs text-ink-muted">{pick(i, "reason", lang)}</span>
            </span>
          </li>
        ))}
      </ul>
      {bundle.unlocks_with_gstin.length > 0 && (
        <p className="mt-2.5 rounded-xl bg-brand-50 px-3 py-2 text-xs text-brand-700">
          {t("advisor.unlocks", { items: bundle.unlocks_with_gstin.join(", ") })}
        </p>
      )}
      <button type="button" onClick={onQuote} disabled={busy} className="btn-dark mt-3 w-full min-h-[48px]">
        {busy ? <Spinner className="h-4 w-4" /> : <>{t("advisor.seeQuote")} <ArrowRight size={16} /></>}
      </button>
    </motion.div>
  );
}

export default function Advisor() {
  const { t, i18n } = useTranslation();
  const nav = useNavigate();
  const [turn, setTurn] = useState<AdvisorTurn | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const [quoting, setQuoting] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const nextId = useRef(0);
  const started = useRef(false);
  const quoted = useRef(false);
  const bottom = useRef<HTMLDivElement>(null);
  const rec = useRef<SpeechRec | null>(null);

  const push = (m: Omit<Msg, "id">) => setMsgs((list) => [...list, { ...m, id: nextId.current++ }]);

  const apply = (r: AdvisorTurn) => {
    setTurn(r);
    push({ from: "bot", text: r.reply, bundle: r.bundle && r.slot === "after" ? r.bundle : null });
  };

  const start = useCallback(async () => {
    setError(null);
    setMsgs([]);
    setBusy(true);
    try {
      apply(await api.startSession(getChatLang()));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void start();
  }, [start]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [msgs, busy]);

  useEffect(() => {
    const id = turn?.session_id;
    if (!id) return;
    const leave = () => {
      if (!quoted.current && turn?.status === "open") navigator.sendBeacon(`${import.meta.env.VITE_API_URL ?? ""}/api/advisor/sessions/${id}/abandon`);
    };
    window.addEventListener("pagehide", leave);
    return () => window.removeEventListener("pagehide", leave);
  }, [turn?.session_id, turn?.status]);

  const send = async (msg: { text?: string; chip?: string }, shown: string, silent = false) => {
    if (!turn || busy) return;
    if (!silent) push({ from: "me", text: shown });
    setBusy(true);
    setError(null);
    try {
      apply(await api.sendMessage(turn.session_id, msg));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  const goQuote = async () => {
    if (!turn) return;
    setQuoting(true);
    try {
      const q = await api.createQuote(turn.session_id);
      quoted.current = true;
      nav(`/quote/${q.id}`);
    } catch (e) {
      setError(e);
    } finally {
      setQuoting(false);
    }
  };

  const onChip = (c: Chip) => {
    if (c.value === "action:quote") return void goQuote();
    void send({ chip: c.value }, c.label);
  };

  useEffect(() => {
    const ui = i18n.language;
    if (turn && turn.language !== ui && (ui === "en" || ui === "hi") && (turn.language === "en" || turn.language === "hi")) {
      void send({ chip: `lang:${ui}` }, "", true);
    }
  }, [i18n.language]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const v = text.trim();
    if (!v) return;
    setText("");
    void send({ text: v }, v);
  };

  const Recognizer = getRecognizer();
  const toggleMic = () => {
    if (!Recognizer) return;
    if (listening) return rec.current?.stop();
    const r = new Recognizer();
    r.lang = SPEECH_LANG[turn?.language ?? "en"] ?? "en-IN";
    r.interimResults = false;
    r.onresult = (e) => {
      const said = e.results[0]?.[0]?.transcript ?? "";
      if (said) void send({ text: said }, said);
    };
    r.onend = () => setListening(false);
    r.onerror = () => setListening(false);
    rec.current = r;
    setListening(true);
    r.start();
  };

  const closed = turn?.status === "lead";
  const modeBadge = turn && (
    <span className={cx("flex items-center gap-1.5 text-xs", turn.mode === "ai" ? "text-brand-700" : "text-ok-text")}>
      <span className={cx("h-[7px] w-[7px] rounded-full", turn.mode === "ai" ? "bg-brand-500" : "bg-ok")} />
      {turn.mode === "ai" ? t("advisor.ai") : t("advisor.guided")}
    </span>
  );

  return (
    <AppShell
      back="/"
      title={
        <span className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-brand-400 to-brand-700 text-sm font-extrabold text-white">S</span>
          {t("advisor.title")}
        </span>
      }
      subtitle={modeBadge}
      footer={
        !closed && (
          <div className="flex flex-col gap-2.5">
            <AnimatePresence mode="popLayout">
              {turn && turn.chips.length > 0 && !busy && (
                <motion.div
                  key={msgs.length}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-0.5 [scrollbar-width:none]"
                >
                  {turn.chips.map((c) => (
                    <button
                      key={c.value}
                      type="button"
                      onClick={() => onChip(c)}
                      aria-pressed={c.selected}
                      className={cx(
                        "min-h-[40px] flex-none rounded-full border px-3.5 text-[13px] font-medium transition active:scale-95",
                        c.selected ? "border-brand-600 bg-brand-600 text-white" : "border-brand-200 bg-white text-brand-700 hover:border-brand-400",
                      )}
                    >
                      {c.selected && <Check size={14} className="-ml-0.5 mr-1 inline" />}
                      {c.label}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
            <form onSubmit={submit} className="flex items-center gap-2 rounded-[18px] bg-white py-1.5 pl-4 pr-1.5 shadow-[0_10px_30px_rgba(74,47,214,.14)]">
              <label htmlFor="msg" className="sr-only">{t("advisor.placeholder")}</label>
              <input
                id="msg"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder={listening ? t("advisor.listening") : t("advisor.placeholder")}
                maxLength={500}
                autoComplete="off"
                className="min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-ink-muted/70"
              />
              {Recognizer && (
                <button
                  type="button"
                  onClick={toggleMic}
                  aria-label={t("advisor.speak")}
                  aria-pressed={listening}
                  className={cx("grid h-11 w-11 place-items-center rounded-2xl transition", listening ? "animate-pulsering bg-brand-600 text-white" : "bg-brand-50 text-brand-600")}
                >
                  <Mic />
                </button>
              )}
              <button type="submit" aria-label={t("advisor.send")} disabled={!text.trim() || busy} className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-b from-brand-500 to-brand-600 text-white disabled:opacity-40">
                <ArrowRight size={18} />
              </button>
            </form>
          </div>
        )
      }
    >
      <div className="flex flex-col gap-2.5 px-4 pb-4 pt-1.5 text-sm leading-relaxed" aria-live="polite">
        <AnimatePresence initial={false}>
          {msgs.map((m) => (
            <motion.div
              key={m.id}
              layout
              initial={{ opacity: 0, y: 12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.35, ease: [0.2, 0.7, 0.2, 1] }}
              className={cx("flex flex-col", m.from === "me" ? "items-end" : "items-start")}
            >
              <div
                className={cx(
                  "max-w-[84%] whitespace-pre-line px-3.5 py-2.5",
                  m.from === "me"
                    ? "rounded-[18px_18px_6px_18px] bg-gradient-to-b from-brand-500 to-brand-600 text-white"
                    : "rounded-[18px_18px_18px_6px] bg-white shadow-[0_4px_14px_rgba(74,47,214,.08)]",
                )}
              >
                {m.text}
              </div>
              {m.bundle && (
                <div className="w-full">
                  <BundleCard bundle={m.bundle} noGst={turn?.profile.gstin_status !== "Active"} onQuote={goQuote} busy={quoting} />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {busy && (
          <div role="status" aria-label={t("advisor.typing")} className="flex gap-1 self-start rounded-[18px] bg-white/70 px-3.5 py-3">
            {[0, 1, 2].map((i) => (
              <span key={i} className="h-1.5 w-1.5 animate-dot rounded-full bg-brand-600" style={{ animationDelay: `${i * 0.2}s` }} />
            ))}
          </div>
        )}

        {closed && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card mt-2 flex flex-col items-start gap-3 p-5">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-50 text-brand-600"><Phone /></span>
            <div>
              <p className="font-display text-base font-bold">{t("advisor.callback")}</p>
              <p className="mt-1 text-sm text-ink-muted">{t("advisor.callbackBody")}</p>
            </div>
            <button type="button" onClick={start} className="btn-outline min-h-[40px] text-sm">
              <Refresh size={16} /> {t("advisor.restart")}
            </button>
          </motion.div>
        )}

        {error != null && <ErrorState error={error} onRetry={turn ? undefined : start} />}
        <div ref={bottom} />
      </div>
    </AppShell>
  );
}
