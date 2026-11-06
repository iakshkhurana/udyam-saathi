import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { setChatLang } from "../i18n";
import { cx } from "../lib/format";
import { ChevronLeft } from "./Icons";

export function LangToggle({ dark = false }: { dark?: boolean }) {
  const { i18n, t } = useTranslation();
  const opts = [
    { code: "en", label: "EN" },
    { code: "hi", label: "हिं" },
  ];
  return (
    <div role="group" aria-label={t("common.language")} className={cx("flex rounded-[10px] p-[3px] text-xs font-semibold", dark ? "bg-white/10" : "bg-white/80")}>
      {opts.map((o) => {
        const on = i18n.language === o.code;
        return (
          <button
            key={o.code}
            type="button"
            aria-pressed={on}
            onClick={() => setChatLang(o.code)}
            className={cx(
              "min-h-[32px] rounded-lg px-2.5 transition-colors",
              on ? "bg-brand-600 text-white shadow-sm" : dark ? "text-white/70 hover:text-white" : "text-ink-muted hover:text-ink",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

export function BackButton({ to }: { to?: string }) {
  const { t } = useTranslation();
  const nav = useNavigate();
  const cls = "grid h-11 w-11 flex-none place-items-center rounded-2xl bg-white/80 text-ink transition hover:bg-white";
  return to ? (
    <Link to={to} aria-label={t("common.back")} className={cls}>
      <ChevronLeft />
    </Link>
  ) : (
    <button type="button" aria-label={t("common.back")} className={cls} onClick={() => nav(-1)}>
      <ChevronLeft />
    </button>
  );
}

/** Mobile-first frame: max 430px wide, centred on desktop. */
export function AppShell({
  title,
  subtitle,
  back,
  right,
  progress,
  footer,
  children,
  className,
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  back?: string | true;
  right?: ReactNode;
  progress?: number;
  footer?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className="min-h-[100dvh] bg-[#ECE8FB] sm:py-6">
      <div className={cx("app-glow relative mx-auto flex min-h-[100dvh] max-w-[430px] flex-col sm:min-h-[calc(100dvh-48px)] sm:overflow-hidden sm:rounded-[32px] sm:shadow-[0_40px_80px_-40px_rgba(74,47,214,.45)]", className)}>
        {(title || back || right) && (
          <header className="no-print sticky top-0 z-20 px-4 pb-2 pt-4 backdrop-blur-md [background:linear-gradient(#f3efff_60%,transparent)]">
            <div className="flex items-center gap-2.5">
              {back && <BackButton to={back === true ? undefined : back} />}
              <div className="min-w-0 flex-1">
                {title && <div className="truncate font-display text-[17px] font-bold">{title}</div>}
                {subtitle && <div className="truncate text-xs text-ink-muted">{subtitle}</div>}
              </div>
              {right}
              <LangToggle />
            </div>
            {progress !== undefined && (
              <div aria-hidden className="mt-3.5 grid grid-cols-3 gap-1.5">
                {[0, 1, 2].map((i) => {
                  const fill = Math.max(0, Math.min(1, progress - i));
                  return (
                    <span key={i} className="h-[5px] overflow-hidden rounded-full bg-[#DCD6F2]">
                      <span className="block h-full rounded-full bg-brand-600 transition-[width] duration-700" style={{ width: `${fill * 100}%` }} />
                    </span>
                  );
                })}
              </div>
            )}
          </header>
        )}
        <main className="flex flex-1 flex-col">{children}</main>
        {footer && (
          <div className="no-print sticky bottom-0 z-20 border-t border-line bg-canvas/85 px-4 pb-[max(20px,env(safe-area-inset-bottom))] pt-3.5 backdrop-blur-xl">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
