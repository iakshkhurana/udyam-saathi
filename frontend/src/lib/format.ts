const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

export const rupees = (n: number) => `₹${inr.format(n)}`;

export function shortDate(iso: string | null | undefined, lang: string) {
  if (!iso) return "";
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  return d.toLocaleDateString(lang === "hi" ? "hi-IN" : "en-IN", { weekday: "short", day: "numeric", month: "short" });
}

export function clockTime(iso: string, lang: string) {
  return new Date(iso).toLocaleTimeString(lang === "hi" ? "hi-IN" : "en-IN", { hour: "numeric", minute: "2-digit" });
}

/** Pick the _en / _hi variant of a field. Any non-Hindi UI language falls back to English. */
export function pick<T extends object>(obj: T, key: string, lang: string): string {
  const rec = obj as Record<string, unknown>;
  const v = rec[`${key}_${lang === "hi" ? "hi" : "en"}`] ?? rec[`${key}_en`];
  return typeof v === "string" ? v : "";
}

export function pickList<T extends object>(obj: T, key: string, lang: string): string[] {
  const rec = obj as Record<string, unknown>;
  const v = rec[`${key}_${lang === "hi" ? "hi" : "en"}`] ?? rec[`${key}_en`];
  return Array.isArray(v) ? (v as string[]) : [];
}

export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");
