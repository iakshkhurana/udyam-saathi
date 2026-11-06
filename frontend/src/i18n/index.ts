import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import hi from "./hi.json";

export const CHAT_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "bn", label: "বাংলা" },
  { code: "mr", label: "मराठी" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "pa", label: "ਪੰਜਾਬੀ" },
  { code: "ml", label: "മലയാളം" },
] as const;

const CHAT_KEY = "saathi.chatLang";

function read(key: string) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

/** Language the advisor chats in (any of 10). The UI itself is EN or HI. */
export function getChatLang(): string {
  return read(CHAT_KEY) ?? "en";
}

export function setChatLang(code: string) {
  try {
    localStorage.setItem(CHAT_KEY, code);
  } catch {
    /* storage blocked: language lives for this page only */
  }
  setUiLang(code === "hi" ? "hi" : "en");
}

export function setUiLang(code: "en" | "hi") {
  void i18n.changeLanguage(code);
  document.documentElement.lang = code;
}

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, hi: { translation: hi } },
  lng: getChatLang() === "hi" ? "hi" : "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

document.documentElement.lang = i18n.language;

export default i18n;
