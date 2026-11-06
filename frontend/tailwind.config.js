/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#16132D", soft: "#3A3657", muted: "#5B5876" },
        canvas: "#F6F4FF",
        line: "#ECE7FD",
        brand: {
          50: "#F4F0FF",
          100: "#EAE4FF",
          200: "#D9D0FF",
          300: "#B9A8FF",
          400: "#8B6CFF",
          500: "#7A5CFF",
          600: "#5A3BF0",
          700: "#4B2FD6",
          800: "#3F23C9",
          900: "#2E1A9E",
        },
        night: { DEFAULT: "#0C0A1D", 800: "#160F38", 600: "#3A1F9E" },
        ok: { DEFAULT: "#12805C", text: "#0D6B4C", bg: "#E8F6EF", line: "#CDEBDD" },
        warn: { DEFAULT: "#B25E00", text: "#8A4800", bg: "#FFF3E0", line: "#F3D9B5" },
        bad: { DEFAULT: "#C4271D", text: "#A3201A", bg: "#FDECEA", line: "#F5C7C2" },
      },
      fontFamily: {
        sans: ["Inter", "Noto Sans Devanagari", "system-ui", "sans-serif"],
        display: ["Manrope", "Noto Sans Devanagari", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 20px 40px -28px rgba(74,47,214,.35)",
        float: "0 12px 30px rgba(74,47,214,.16)",
        cta: "0 12px 26px rgba(90,59,240,.35), inset 0 1px 0 rgba(255,255,255,.3)",
        glass: "0 10px 30px rgba(74,47,214,.08)",
      },
      keyframes: {
        floaty: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-8px)" } },
        beam: { "0%,100%": { opacity: ".55" }, "50%": { opacity: ".9" } },
        dot: { "0%,80%,100%": { opacity: ".25" }, "40%": { opacity: "1" } },
        scan: { "0%": { top: "8%" }, "100%": { top: "84%" } },
        pulsering: {
          "0%": { boxShadow: "0 0 0 0 rgba(90,59,240,.45)" },
          "100%": { boxShadow: "0 0 0 12px rgba(90,59,240,0)" },
        },
      },
      animation: {
        floaty: "floaty 6s ease-in-out infinite",
        beam: "beam 7s ease-in-out infinite",
        dot: "dot 1.2s infinite",
        scan: "scan 1.6s ease-in-out infinite alternate",
        pulsering: "pulsering 1.6s ease-out infinite",
      },
    },
  },
  plugins: [],
};
