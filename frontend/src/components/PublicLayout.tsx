import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Phone } from "lucide-react";
import { Brand } from "./Brand";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function PublicLayout() {
  const { t } = useTranslation();
  const home = useLocation().pathname === "/";
  const link = ({ isActive }: { isActive: boolean }) =>
    `rounded-lg px-3 py-2 text-sm font-bold transition ${isActive ? "bg-white/15 text-white" : "text-white/75 hover:bg-white/10 hover:text-white"}`;
  return (
    <div className="flex min-h-screen flex-col">
      <header className={`${home ? "absolute inset-x-0 top-0" : "sticky top-0 dark-band"} z-[1100] border-b border-white/10 backdrop-blur-md`} style={home ? { background: "rgba(11,26,46,.35)" } : undefined}>
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-6">
          <Brand dark />
          <nav className="order-3 flex w-full gap-1 sm:order-none sm:ml-4 sm:w-auto" aria-label="Main">
            <NavLink to="/report" className={link}>{t("nav.report")}</NavLink>
            <NavLink to="/track" className={link}>{t("nav.track")}</NavLink>
            <NavLink to="/login" className={link}>{t("nav.orgs")}</NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <a href="tel:112" className="btn-sos px-4 py-2"><Phone className="h-4 w-4" aria-hidden />112</a>
            <LanguageSwitcher />
          </div>
        </div>
      </header>
      <main className="flex-1"><Outlet /></main>
      <footer className="dark-band text-white/80">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-8 text-sm sm:px-6">
          <div className="flex items-center gap-3"><Brand dark /><p className="max-w-measure">{t("footer.disclaimer")}</p></div>
          <Link to="/login" className="font-bold text-white hover:text-teal-glow">{t("nav.signIn")}</Link>
        </div>
      </footer>
    </div>
  );
}
