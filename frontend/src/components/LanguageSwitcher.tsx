import { useTranslation } from "react-i18next";
import { Languages } from "lucide-react";
import { LANGUAGES } from "../lib/i18n";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  return (
    <label className="relative inline-flex items-center">
      <span className="sr-only">{t("nav.language")}</span>
      <Languages className="pointer-events-none absolute left-2.5 h-4 w-4 text-white/80" aria-hidden />
      <select
        value={i18n.language}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
        className="appearance-none rounded-xl border border-white/25 bg-white/10 py-2 pl-8 pr-3 text-sm font-bold text-white backdrop-blur hover:bg-white/20 focus:outline-none [&>option]:text-ink"
      >
        {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
      </select>
    </label>
  );
}
