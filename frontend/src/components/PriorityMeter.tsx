import { SEVERITY_TEXT } from "../lib/format";

/** 0–100 bar with the configured band boundaries (25 / 50 / 75) marked, so the score reads in context. */
export function PriorityMeter({ score, severity, label }: { score: number | null; severity: string | null; label: string }) {
  const s = Math.max(0, Math.min(100, score ?? 0));
  return (
    <div>
      <div className="flex items-baseline gap-3">
        <span className={`tabular text-5xl font-extrabold leading-none ${SEVERITY_TEXT[severity || "LOW"]}`}>{score ?? "–"}</span>
        <span className="text-sm text-muted">/ 100</span>
        <span className={`ml-auto text-lg font-bold ${SEVERITY_TEXT[severity || "LOW"]}`}>{label}</span>
      </div>
      <div className="relative mt-3 h-2.5 overflow-hidden rounded-full bg-line" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={s} aria-label={label}>
        <div className="absolute inset-y-0 left-0 flex w-full">
          <span className="w-1/4 bg-pri-low/25" /><span className="w-1/4 bg-pri-moderate/25" /><span className="w-1/4 bg-pri-high/25" /><span className="w-1/4 bg-pri-critical/25" />
        </div>
        <div className={`absolute inset-y-0 left-0 rounded-full ${{ CRITICAL: "bg-pri-critical", HIGH: "bg-pri-high", MODERATE: "bg-pri-moderate", LOW: "bg-pri-low" }[severity || "LOW"]}`} style={{ width: `${s}%` }} />
      </div>
    </div>
  );
}

export function SeverityTag({ severity, score }: { severity?: string | null; score?: number | null }) {
  if (!severity) return <span className="rounded bg-line px-2 py-0.5 text-xs font-semibold text-muted">Pending</span>;
  const cls = { CRITICAL: "bg-pri-critical text-white", HIGH: "bg-pri-high text-white", MODERATE: "bg-pri-moderate text-white", LOW: "bg-pri-low text-white" }[severity];
  return <span className={`tabular inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-bold ${cls}`}>{score ?? ""} {severity.charAt(0) + severity.slice(1).toLowerCase()}</span>;
}
