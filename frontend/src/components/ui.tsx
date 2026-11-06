import { motion, type HTMLMotionProps } from "framer-motion";
import { useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "../lib/api";
import { cx } from "../lib/format";
import type { CheckStatus } from "../lib/types";
import { Alert, Check, Cross, Refresh } from "./Icons";

const ease = [0.2, 0.7, 0.2, 1] as const;

/** Fades and lifts children into place when they scroll into view. */
export function Reveal({ delay = 0, y = 28, className, ...rest }: HTMLMotionProps<"div"> & { delay?: number; y?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "0px 0px -80px 0px" }}
      transition={{ duration: 0.7, ease, delay }}
      className={className}
      {...rest}
    />
  );
}

/** Same as Reveal but plays on mount, for content above the fold. */
export function Rise({ delay = 0, className, ...rest }: HTMLMotionProps<"div"> & { delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease, delay }}
      className={className}
      {...rest}
    />
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cx("inline-block h-5 w-5 animate-spin rounded-full border-2 border-current border-r-transparent", className)}
    />
  );
}

export function Toggle({ checked, onChange, label, disabled }: { checked: boolean; onChange: (v: boolean) => void; label: string; disabled?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cx(
        "relative h-[30px] w-[50px] flex-none rounded-full transition-colors disabled:opacity-50",
        checked ? "bg-brand-600" : "bg-[#DCD6F2]",
      )}
    >
      <motion.span
        layout
        transition={{ type: "spring", stiffness: 600, damping: 34 }}
        className={cx("absolute top-1 h-[22px] w-[22px] rounded-full bg-white shadow", checked ? "right-1" : "left-1")}
      />
    </button>
  );
}

export function Stepper({ value, onChange, min = 1, max = 500, lessLabel, moreLabel, disabled }: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  lessLabel: string;
  moreLabel: string;
  disabled?: boolean;
}) {
  const btn = "grid h-9 w-9 place-items-center rounded-[10px] bg-white text-lg font-semibold text-brand-700 shadow-sm disabled:opacity-40";
  return (
    <div className="flex items-center gap-0.5 rounded-xl bg-brand-50 p-0.5">
      <button type="button" aria-label={lessLabel} className={btn} disabled={disabled || value <= min} onClick={() => onChange(value - 1)}>
        −
      </button>
      <span className="w-7 text-center text-sm font-semibold tabular-nums" aria-live="polite">
        {value}
      </span>
      <button type="button" aria-label={moreLabel} className={btn} disabled={disabled || value >= max} onClick={() => onChange(value + 1)}>
        +
      </button>
    </div>
  );
}

const STATUS_STYLE: Record<CheckStatus, { box: string; icon: ReactNode }> = {
  pass: { box: "bg-ok-bg text-ok-text", icon: <Check size={16} strokeWidth={2.6} /> },
  warn: { box: "bg-warn-bg text-warn-text", icon: <Alert size={16} /> },
  fail: { box: "bg-bad-bg text-bad-text", icon: <Cross size={16} strokeWidth={2.6} /> },
};

export function StatusIcon({ status }: { status: CheckStatus }) {
  const s = STATUS_STYLE[status];
  return <span className={cx("grid h-8 w-8 flex-none place-items-center rounded-[10px]", s.box)}>{s.icon}</span>;
}

export function Pill({ tone = "brand", children, className }: { tone?: "brand" | "ok" | "warn" | "bad" | "white"; children: ReactNode; className?: string }) {
  const tones = {
    brand: "bg-brand-100 text-brand-700",
    ok: "bg-ok-bg text-ok-text",
    warn: "bg-warn-bg text-warn-text",
    bad: "bg-bad-bg text-bad-text",
    white: "bg-white text-brand-700",
  };
  return <span className={cx("inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold", tones[tone], className)}>{children}</span>;
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { t } = useTranslation();
  const msg = error instanceof ApiError && (error.status === 404 || error.status === 405) ? t("common.notReady") : error instanceof Error ? error.message : String(error);
  return (
    <div role="alert" className="card flex flex-col items-start gap-3 p-5">
      <span className="grid h-10 w-10 place-items-center rounded-xl bg-bad-bg text-bad-text">
        <Alert />
      </span>
      <div>
        <p className="font-display text-base font-semibold">{t("common.errorTitle")}</p>
        <p className="mt-1 text-sm leading-relaxed text-ink-muted">{msg}</p>
      </div>
      {onRetry && (
        <button type="button" className="btn-outline min-h-[40px] text-sm" onClick={onRetry}>
          <Refresh size={16} /> {t("common.retry")}
        </button>
      )}
    </div>
  );
}

export function PageLoader() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-1 items-center justify-center gap-3 py-24 text-brand-600">
      <Spinner />
      <span className="text-sm text-ink-muted">{t("common.loading")}</span>
    </div>
  );
}

/** Loads data once per `deps` change. Keeps the last good value while reloading. */
export function useLoad<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [state, setState] = useState<{ data?: T; error?: unknown; loading: boolean }>({ loading: true });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let live = true;
    setState((s) => ({ ...s, loading: true, error: undefined }));
    fn().then(
      (data) => live && setState({ data, loading: false }),
      (error) => live && setState((s) => ({ ...s, error, loading: false })),
    );
    return () => {
      live = false;
    };
  }, [...deps, tick]);
  return { ...state, reload: () => setTick((n) => n + 1), set: (data: T) => setState({ data, loading: false }) };
}
