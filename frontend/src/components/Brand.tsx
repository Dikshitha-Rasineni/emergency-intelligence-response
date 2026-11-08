import { Link } from "react-router-dom";

export function Mark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <defs><linearGradient id="bm" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#FF4A64"/><stop offset="1" stopColor="#9E0C24"/></linearGradient></defs><rect width="32" height="32" rx="9" fill="url(#bm)" />
      <path d="M14 7h4v7h7v4h-7v7h-4v-7H7v-4h7z" fill="#fff" />
    </svg>
  );
}

export function Brand({ to = "/", sub, dark = false }: { to?: string; sub?: string; dark?: boolean }) {
  return (
    <Link to={to} className="flex items-center gap-2.5" aria-label="RESQ.AI home">
      <Mark />
      <span className="leading-none">
        <span className={`block text-[18px] font-black tracking-tight ${dark ? "text-white" : ""}`}>RESQ<span className="text-sos-glow">.</span>AI</span>
        {sub && <span className={`mt-0.5 block text-xs ${dark ? "text-white/70" : "text-muted"}`}>{sub}</span>}
      </span>
    </Link>
  );
}
