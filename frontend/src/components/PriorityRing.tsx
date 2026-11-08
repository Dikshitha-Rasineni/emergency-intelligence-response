import { useEffect, useState } from "react";

const COLOR: Record<string, string> = { CRITICAL: "#C8102E", HIGH: "#D2561A", MODERATE: "#A07C00", LOW: "#2F7A55" };

/** Animated circular 0–100 gauge. */
export function PriorityRing({ score, severity, label, size = 190 }: { score: number | null; severity: string | null; label: string; size?: number }) {
  const [shown, setShown] = useState(0);
  const target = Math.max(0, Math.min(100, score ?? 0));
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setShown(target); return; }
    let raf = 0; const start = performance.now(); const from = shown;
    const tick = (t: number) => { const p = Math.min(1, (t - start) / 1100); const e = 1 - Math.pow(1 - p, 3); setShown(Math.round(from + (target - from) * e)); if (p < 1) raf = requestAnimationFrame(tick); };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]); // eslint-disable-line react-hooks/exhaustive-deps
  const r = 80, c = 2 * Math.PI * r, col = COLOR[severity || "LOW"];
  return (
    <div className="relative" style={{ width: size, height: size }} role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={target} aria-label={label}>
      <svg viewBox="0 0 200 200" className="h-full w-full -rotate-90">
        <circle cx="100" cy="100" r={r} fill="none" stroke="#E6ECEA" strokeWidth="16" />
        <circle cx="100" cy="100" r={r} fill="none" stroke={col} strokeWidth="16" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - shown / 100)} style={{ filter: `drop-shadow(0 0 8px ${col}88)` }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="tabular text-5xl font-black leading-none" style={{ color: col }}>{score == null ? "–" : shown}</span>
        <span className="mt-1 text-xs font-semibold text-muted">/ 100</span>
        <span className="mt-1.5 rounded-full px-3 py-0.5 text-sm font-bold text-white" style={{ background: col }}>{label}</span>
      </div>
    </div>
  );
}
