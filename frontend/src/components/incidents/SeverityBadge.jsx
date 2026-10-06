import { SEVERITY } from '../../utils/incidents'

export default function SeverityBadge({ severity, known = true }) {
  if (!known) return <span className="sev sev--unknown">UNASSESSED</span>
  const s = SEVERITY[severity]
  return (
    <span className={`sev sev--${s.cls}`}>
      <span className="sev__glyph" aria-hidden="true">{s.glyph}</span>
      {s.label}
    </span>
  )
}
