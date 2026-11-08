import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "../locales/en.json";
import te from "../locales/te.json";
import ta from "../locales/ta.json";
import hi from "../locales/hi.json";
import { store } from "./store";

export const LANGUAGES = [
  { code: "en", name: "English", speech: "en-IN" },
  { code: "te", name: "తెలుగు", speech: "te-IN" },
  { code: "ta", name: "தமிழ்", speech: "ta-IN" },
  { code: "hi", name: "हिन्दी", speech: "hi-IN" },
] as const;
export type Lang = (typeof LANGUAGES)[number]["code"];

const saved = store.get("resq.lang");
const browser = (navigator.language || "en").slice(0, 2);
const initial = saved || (LANGUAGES.some((l) => l.code === browser) ? browser : "en");

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, te: { translation: te }, ta: { translation: ta }, hi: { translation: hi } },
  lng: initial,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});
document.documentElement.lang = initial;
i18n.on("languageChanged", (l) => {
  document.documentElement.lang = l;
  store.set("resq.lang", l);
});
export default i18n;
