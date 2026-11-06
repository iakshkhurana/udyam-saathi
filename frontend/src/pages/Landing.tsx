import { animate, motion, useInView, useMotionValueEvent, useScroll, useSpring, useTransform } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { LangToggle } from "../components/AppShell";
import { ArrowRight, Chat, Clock, DocCheck, House, Lines } from "../components/Icons";
import { Reveal } from "../components/ui";
import { CHAT_LANGUAGES, setChatLang } from "../i18n";
import { cx } from "../lib/format";

type Stat = { value: string; label: string };
type Step = { t: string; d: string };

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2.5 font-display text-[19px] font-extrabold text-ink">
      <span className="grid h-[34px] w-[34px] place-items-center rounded-[10px] bg-gradient-to-br from-brand-400 to-brand-700 text-white shadow-[inset_0_1px_0_rgba(255,255,255,.4)]">
        <House size={18} strokeWidth={2.2} />
      </span>
      <span>
        Udyam Saathi<span className="text-brand-600">.</span>
      </span>
    </Link>
  );
}

function Nav() {
  const { t } = useTranslation();
  const { scrollY } = useScroll();
  const [stuck, setStuck] = useState(false);
  useMotionValueEvent(scrollY, "change", (y) => setStuck(y > 24));
  return (
    <div className="pointer-events-none fixed inset-x-0 top-0 z-50 px-4 pt-4">
      <motion.nav
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className={cx(
          "glass pointer-events-auto mx-auto flex max-w-[1160px] flex-wrap items-center gap-x-6 gap-y-2 rounded-[18px] py-2.5 pl-4 pr-2.5 transition-all duration-300",
          stuck ? "max-w-[980px] bg-white/85 shadow-[0_14px_40px_rgba(74,47,214,.14)]" : "shadow-glass",
        )}
      >
        <Logo />
        <div className="hidden flex-1 justify-center gap-6 text-sm font-medium text-ink-soft md:flex">
          <a href="#features" className="transition hover:text-brand-700">{t("nav.features")}</a>
          <a href="#how" className="transition hover:text-brand-700">{t("nav.how")}</a>
          <Link to="/track" className="transition hover:text-brand-700">{t("nav.track")}</Link>
          <Link to="/backoffice" className="transition hover:text-brand-700">{t("nav.sales")}</Link>
        </div>
        <div className="ml-auto flex items-center gap-2 md:ml-0">
          <LangToggle />
          <Link to="/advisor" className="btn-primary hidden min-h-[40px] rounded-xl px-4 text-sm sm:inline-flex">
            {t("nav.cta")} <ArrowRight size={16} />
          </Link>
        </div>
      </motion.nav>
    </div>
  );
}

/** The tilted app window under the hero. Flattens and lifts as it scrolls into view. */
function HeroWindow() {
  const { t } = useTranslation();
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "start 0.2"] });
  const p = useSpring(scrollYProgress, { stiffness: 120, damping: 24, mass: 0.4 });
  const rotateX = useTransform(p, [0, 1], [32, 0]);
  const scale = useTransform(p, [0, 1], [0.86, 1]);
  const y = useTransform(p, [0, 1], [80, 0]);
  const glow = useTransform(p, [0, 1], [0.25, 0.6]);

  const row = "flex justify-between border-b border-[#F0EDFA] py-2.5 last:border-0";
  return (
    <div ref={ref} className="relative mx-auto mt-10 max-w-[1080px] [perspective:1600px]">
      <motion.div aria-hidden style={{ opacity: glow }} className="absolute inset-x-10 -bottom-10 top-20 rounded-[40px] bg-brand-500 blur-[90px]" />
      <motion.div
        style={{ rotateX, scale, y, transformOrigin: "50% 0%" }}
        className="relative rounded-[26px] border border-white bg-white/55 p-3 shadow-[0_60px_120px_-40px_rgba(74,47,214,.45)] backdrop-blur"
      >
        <div className="flex min-h-[400px] flex-col overflow-hidden rounded-[18px] bg-white md:flex-row">
          <div className="flex flex-1 flex-col gap-3 border-[#EEEAFB] bg-[#FBFAFF] p-5 md:border-r">
            <div className="flex items-center justify-between">
              <strong className="font-display text-[15px]">Saathi</strong>
              <span className="rounded-full bg-brand-100 px-2 py-1 text-[11px] font-semibold text-brand-700">Guided mode</span>
            </div>
            {[
              ["l", "नमस्ते! आपका बिज़नेस क्या है?"],
              ["r", "किराना दुकान, 2 लोग"],
              ["l", "क्या आपके पास GSTIN है?"],
            ].map(([side, text], i) => (
              <motion.div
                key={text}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.3 + i * 0.35 }}
                className={cx(
                  "max-w-[85%] px-3.5 py-2.5 text-[13px] leading-relaxed",
                  side === "l" ? "self-start rounded-[14px_14px_14px_4px] bg-brand-50" : "self-end rounded-[14px_14px_4px_14px] bg-brand-600 text-white",
                )}
              >
                {text}
              </motion.div>
            ))}
            <div className="flex gap-1.5">
              {["हाँ, है", "नहीं"].map((c) => (
                <span key={c} className="rounded-full border border-brand-200 px-3 py-1.5 text-xs text-brand-700">{c}</span>
              ))}
            </div>
          </div>
          <div className="flex flex-1 flex-col gap-2 p-5">
            <span className="eyebrow">{t("landing.previewBundle")}</span>
            <strong className="font-display text-[22px]">Dukaan Digital</strong>
            <div className="font-display text-[34px] font-extrabold tracking-tight">
              ₹2,495<span className="text-sm font-medium text-ink-muted">/month + GST</span>
            </div>
            <div className="text-[13px]">
              <div className={row}><span>Biz Fibre 100</span><span className="text-ink-muted">₹999</span></div>
              <div className={row}><span>Business Postpaid 299 × 2</span><span className="text-ink-muted">₹598</span></div>
              <div className={row}><span>Cloud POS &amp; Billing</span><span className="text-ink-muted">₹599</span></div>
              <div className={row}><span>Website + Domain Starter</span><span className="text-ink-muted">₹299</span></div>
            </div>
          </div>
          <div className="hidden flex-col gap-3.5 border-l border-[#EEEAFB] bg-gradient-to-b from-[#F7F4FF] to-white p-5 md:flex md:w-[280px]">
            <span className="eyebrow">{t("landing.previewTracker")}</span>
            <div className="flex flex-col gap-3 text-[13px]">
              <div className="flex items-center gap-2.5"><span className="h-5 w-5 rounded-full bg-ok" />{t("landing.previewKyc")}</div>
              <div className="flex items-center gap-2.5 font-semibold"><span className="h-5 w-5 animate-pulsering rounded-full bg-brand-500" />{t("landing.previewInstall")}</div>
              <div className="flex items-center gap-2.5 text-ink-muted"><span className="h-5 w-5 rounded-full border-2 border-brand-200" />{t("landing.previewActivation")}</div>
            </div>
            <div className="mt-auto animate-floaty rounded-[14px] bg-white p-3 text-xs leading-relaxed shadow-float">
              <strong className="block text-ok">{t("landing.previewWa")}</strong>
              {t("landing.previewWaText")}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function Hero() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { scrollY } = useScroll();
  const beamY = useTransform(scrollY, [0, 600], [0, 120]);
  const start = (code: string) => {
    setChatLang(code);
    nav("/advisor");
  };
  const fade = (d: number) => ({
    initial: { opacity: 0, y: 24 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.8, ease: [0.2, 0.7, 0.2, 1] as const, delay: d },
  });

  return (
    <section className="relative overflow-hidden px-4 pb-10 pt-[120px] [background:radial-gradient(1200px_620px_at_50%_-120px,#C9B8FF_0%,#E4DBFF_38%,#F6F4FF_72%)]">
      <motion.div aria-hidden style={{ y: beamY }} className="dots pointer-events-none absolute inset-0 animate-beam opacity-60" />
      <motion.div
        aria-hidden
        style={{ y: beamY }}
        className="pointer-events-none absolute -top-10 left-1/2 h-[700px] w-[900px] -translate-x-1/2 animate-beam [background:conic-gradient(from_180deg_at_50%_0%,transparent_150deg,rgba(255,255,255,.55)_170deg,transparent_178deg,rgba(255,255,255,.45)_184deg,transparent_194deg,rgba(255,255,255,.5)_204deg,transparent_214deg)]"
      />
      <div className="relative mx-auto max-w-[900px] pt-6 text-center">
        <motion.div {...fade(0.05)} className="inline-flex items-center gap-2 rounded-full border border-white bg-white/70 py-1.5 pl-1.5 pr-3.5 text-[13px] font-medium text-ink-soft">
          <span className="rounded-full bg-ink px-2.5 py-0.5 text-xs font-semibold text-white">New</span>
          {t("landing.badge")}
        </motion.div>
        <motion.h1 {...fade(0.12)} className="mt-6 text-[clamp(40px,6.4vw,76px)] font-bold leading-[1.04] tracking-[-0.035em]">
          {t("landing.title1")}
          <br />
          <span className="bg-gradient-to-r from-brand-700 via-brand-500 to-brand-700 bg-clip-text text-transparent">{t("landing.title2")}</span>
        </motion.h1>
        <motion.p {...fade(0.2)} className="mx-auto mt-6 max-w-[620px] text-lg leading-relaxed text-[#4A4766]">
          {t("landing.sub")}
        </motion.p>
        <motion.div {...fade(0.28)} className="mt-8 flex flex-wrap justify-center gap-3">
          <button type="button" onClick={() => start("en")} className="btn-primary min-h-[52px] px-6 text-base">
            {t("landing.startEn")} <ArrowRight size={18} />
          </button>
          <button type="button" onClick={() => start("hi")} className="btn-white min-h-[52px] px-6 text-base">
            {t("landing.startHi")}
          </button>
        </motion.div>
        <motion.div {...fade(0.36)} className="mt-6">
          <p className="text-xs text-ink-muted">{t("landing.chatIn")}</p>
          <div className="mt-2.5 flex flex-wrap justify-center gap-2">
            {CHAT_LANGUAGES.filter((l) => l.code !== "en" && l.code !== "hi").map((l) => (
              <button
                key={l.code}
                type="button"
                onClick={() => start(l.code)}
                className="min-h-[36px] rounded-full bg-white/60 px-3.5 text-[13px] text-[#4A4766] transition hover:-translate-y-0.5 hover:bg-white hover:text-brand-700"
              >
                {l.label}
              </button>
            ))}
          </div>
        </motion.div>
      </div>
      <HeroWindow />
    </section>
  );
}

function CountUp({ value }: { value: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const m = value.match(/^([^\d]*)([\d.,]+)(.*)$/);
  const [shown, setShown] = useState(m ? `${m[1]}0${m[3]}` : value);

  useEffect(() => {
    if (!inView || !m) return;
    const target = parseFloat(m[2].replace(/,/g, ""));
    const decimals = m[2].includes(".") ? m[2].split(".")[1].length : 0;
    const controls = animate(0, target, {
      duration: 1.4,
      ease: [0.2, 0.7, 0.2, 1],
      onUpdate: (v) => setShown(`${m[1]}${v.toFixed(decimals)}${m[3]}`),
    });
    return () => controls.stop();
  }, [inView]);

  return <span ref={ref}>{m ? shown : value}</span>;
}

function Features() {
  const { t } = useTranslation();
  const bigRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: bigRef, offset: ["start end", "center center"] });
  const bigScale = useTransform(scrollYProgress, [0, 1], [0.92, 1]);
  const bigRadius = useTransform(scrollYProgress, [0, 1], [48, 28]);
  const tiles = t("landing.kycTiles", { returnObjects: true }) as string[];
  const tileTone = ["bg-ok-bg text-ok-text", "bg-ok-bg text-ok-text", "bg-warn-bg text-warn-text", "bg-brand-50 text-brand-700"];
  const [cctvOn, setCctvOn] = useState(true);

  const small = "card relative h-full overflow-hidden p-7 shadow-card transition duration-300 hover:-translate-y-1 hover:shadow-[0_30px_50px_-28px_rgba(74,47,214,.5)]";
  const iconBox = "grid h-10 w-10 place-items-center rounded-xl bg-brand-50 text-brand-600";

  return (
    <section id="features" className="scroll-mt-24 px-4 py-20">
      <div className="mx-auto max-w-[1120px]">
        <Reveal className="mx-auto max-w-[720px] text-center">
          <span className="inline-block rounded-full bg-brand-100 px-3 py-1.5 text-[13px] font-semibold text-brand-700">{t("landing.oldTag")}</span>
          <h2 className="mt-4 text-[clamp(30px,4.2vw,48px)] font-bold leading-[1.1] tracking-[-0.03em]">
            {t("landing.oldTitle1")}
            <br />
            {t("landing.oldTitle2")}
          </h2>
          <p className="mt-3.5 text-base leading-relaxed text-[#4A4766]">{t("landing.oldSub")}</p>
        </Reveal>

        <div className="mt-11 grid gap-5 md:grid-cols-3">
          <motion.div
            ref={bigRef}
            style={{ scale: bigScale, borderRadius: bigRadius }}
            className="relative flex flex-wrap items-center gap-7 overflow-hidden bg-gradient-to-br from-brand-500 via-brand-600 to-brand-800 p-9 text-white shadow-[0_30px_60px_-30px_rgba(74,47,214,.6)] md:col-span-3"
          >
            <div aria-hidden className="dots-soft absolute inset-0" />
            <div className="relative min-w-[280px] flex-1">
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-white/20">
                <Chat size={22} />
              </span>
              <h3 className="mt-4 text-[30px] font-bold leading-tight tracking-[-0.02em]">{t("landing.f1Title")}</h3>
              <p className="mt-3 max-w-[520px] text-base leading-relaxed text-[#E9E4FF]">{t("landing.f1Body")}</p>
              <Link to="/advisor" className="btn mt-6 bg-white text-brand-800 hover:bg-brand-50">
                {t("landing.f1Cta")} <ArrowRight size={16} />
              </Link>
            </div>
            <div className="relative flex w-full max-w-[420px] flex-1 flex-col gap-2.5 rounded-[20px] border border-white/30 bg-white/15 p-4 text-sm backdrop-blur-md">
              <Reveal y={12} className="self-end rounded-[14px_14px_4px_14px] bg-white px-3.5 py-2.5 text-ink">{t("landing.f1Q")}</Reveal>
              <Reveal y={12} delay={0.5} className="self-start rounded-[14px_14px_14px_4px] bg-ink/35 px-3.5 py-2.5 leading-relaxed">{t("landing.f1A")}</Reveal>
            </div>
          </motion.div>

          <Reveal delay={0}>
            <div className={small}>
              <span className={iconBox}><Lines /></span>
              <h3 className="mt-4 text-[21px] font-bold">{t("landing.f2Title")}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-[#4A4766]">{t("landing.f2Body")}</p>
              <div className="mt-5 flex items-center justify-between rounded-2xl border border-[#EEEAFB] bg-[#FBFAFF] p-3.5 text-sm">
                <span>Cloud CCTV × 2 <span className="text-ink-muted">{cctvOn ? "+₹398" : ""}</span></span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={cctvOn}
                  aria-label="Cloud CCTV"
                  onClick={() => setCctvOn(!cctvOn)}
                  className={cx("relative h-[26px] w-11 rounded-full transition-colors", cctvOn ? "bg-brand-600" : "bg-[#DCD6F2]")}
                >
                  <motion.span layout className={cx("absolute top-[3px] h-5 w-5 rounded-full bg-white", cctvOn ? "right-[3px]" : "left-[3px]")} />
                </button>
              </div>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <div className={small}>
              <span className={iconBox}><DocCheck /></span>
              <h3 className="mt-4 text-[21px] font-bold">{t("landing.f3Title")}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-[#4A4766]">{t("landing.f3Body")}</p>
              <div className="mt-5 grid grid-cols-2 gap-2 text-[13px]">
                {tiles.map((tile, i) => (
                  <motion.span
                    key={tile}
                    initial={{ opacity: 0, scale: 0.9 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 + i * 0.15 }}
                    className={cx("rounded-xl p-2.5", tileTone[i])}
                  >
                    {tile}
                  </motion.span>
                ))}
              </div>
            </div>
          </Reveal>

          <Reveal delay={0.2}>
            <div className={small}>
              <span className={iconBox}><Clock /></span>
              <h3 className="mt-4 text-[21px] font-bold">{t("landing.f4Title")}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-[#4A4766]">{t("landing.f4Body")}</p>
              <div className="mt-5 h-2 overflow-hidden rounded-full bg-[#EEEAFB]">
                <motion.div
                  initial={{ width: "8%" }}
                  whileInView={{ width: "64%" }}
                  viewport={{ once: true }}
                  transition={{ duration: 1.4, ease: [0.2, 0.7, 0.2, 1], delay: 0.3 }}
                  className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600"
                />
              </div>
              <p className="mt-2.5 text-[13px] text-ink-muted">{t("landing.f4Meta")}</p>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function Stats() {
  const { t } = useTranslation();
  const stats = t("landing.stats", { returnObjects: true }) as Stat[];
  return (
    <section className="px-4 pb-20 pt-4">
      <Reveal className="card mx-auto max-w-[1120px] px-7 py-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h2 className="max-w-[560px] text-[clamp(26px,3.4vw,38px)] font-bold leading-tight tracking-[-0.03em]">{t("landing.statsTitle")}</h2>
          <p className="text-sm text-ink-muted">{t("landing.statsSub")}</p>
        </div>
        <div className="mt-8 grid gap-px overflow-hidden rounded-[20px] bg-line sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((s) => (
            <div key={s.value} className="bg-white p-6">
              <div className="font-display text-[40px] font-extrabold tracking-[-0.03em] text-brand-700">
                <CountUp value={s.value} />
              </div>
              <p className="mt-1.5 text-sm leading-relaxed text-[#4A4766]">{s.label}</p>
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}

function How() {
  const { t } = useTranslation();
  const steps = t("landing.steps", { returnObjects: true }) as Step[];
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 0.85", "end 0.6"] });
  const width = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);
  return (
    <section id="how" className="scroll-mt-24 px-4 pb-20">
      <div className="mx-auto max-w-[1120px]">
        <Reveal>
          <h2 className="text-center text-[clamp(30px,4.2vw,48px)] font-bold tracking-[-0.03em]">{t("landing.howTitle")}</h2>
        </Reveal>
        <div ref={ref} className="relative mt-12">
          <div aria-hidden className="absolute left-0 right-0 top-[22px] hidden h-[3px] rounded-full bg-brand-100 lg:block">
            <motion.div style={{ width }} className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600" />
          </div>
          <ol className="relative grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((s, i) => (
              <Reveal key={s.t} delay={i * 0.12}>
                <li className="h-full list-none">
                  <span className="relative z-10 grid h-11 w-11 place-items-center rounded-full border-4 border-canvas bg-brand-600 font-display text-sm font-extrabold text-white">
                    {i + 1}
                  </span>
                  <div className="mt-4 rounded-[22px] border border-line bg-gradient-to-b from-white to-[#F7F4FF] p-6">
                    <h3 className="text-[19px] font-bold">{s.t}</h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-[#4A4766]">{s.d}</p>
                  </div>
                </li>
              </Reveal>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}

function Cta() {
  const { t } = useTranslation();
  return (
    <section className="px-4 pb-10">
      <Reveal className="relative mx-auto max-w-[1120px] overflow-hidden rounded-[32px] px-7 py-16 text-center text-white [background:radial-gradient(800px_400px_at_50%_0%,#3B2A8F_0%,#16132D_70%)]">
        <div aria-hidden className="dots-soft absolute inset-0 opacity-70" />
        <h2 className="relative text-[clamp(30px,4.4vw,52px)] font-bold leading-[1.08] tracking-[-0.03em]">{t("landing.ctaTitle")}</h2>
        <p className="relative mx-auto mt-3.5 max-w-[520px] leading-relaxed text-[#CFC8F0]">{t("landing.ctaSub")}</p>
        <Link to="/advisor" className="btn-primary relative mt-7 min-h-[52px] px-6">
          {t("landing.ctaBtn")} <ArrowRight size={18} />
        </Link>
      </Reveal>
      <footer className="mx-auto mt-7 flex max-w-[1120px] flex-wrap justify-between gap-3 text-[13px] text-ink-muted">
        <span>
          {t("brand")} {t("by")}
        </span>
        <span className="flex gap-5">
          <Link to="/privacy" className="hover:text-brand-700">{t("landing.privacy")}</Link>
          <Link to="/track" className="hover:text-brand-700">{t("nav.track")}</Link>
        </span>
      </footer>
    </section>
  );
}

function Strip() {
  const { t } = useTranslation();
  const items = t("landing.stripItems", { returnObjects: true }) as string[];
  return (
    <section className="px-4 pt-14 text-center">
      <p className="text-sm font-medium text-ink-muted">{t("landing.strip")}</p>
      <div className="mx-auto mt-5 flex max-w-[980px] flex-wrap justify-center gap-x-9 gap-y-3 font-display text-base font-bold text-[#8A86A6]">
        {items.map((s, i) => (
          <Reveal key={s} y={10} delay={i * 0.06}>
            <span>{s}</span>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

export default function Landing() {
  return (
    <div className="overflow-x-clip">
      <Nav />
      <Hero />
      <Strip />
      <Features />
      <Stats />
      <How />
      <Cta />
    </div>
  );
}
