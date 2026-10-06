export default function PriorityScore({ value, severity, known = true }) {
  if (!known) return <span className="prio prio--unknown mono" title="Priority not yet assessed">—</span>
  return (
    <span className={`prio prio--${severity.toLowerCase()} mono`} title="Priority score">
      <span className="sr-only">Priority </span>{Math.round(value)}
    </span>
  )
}
