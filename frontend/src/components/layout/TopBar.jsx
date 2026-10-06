import { Link } from 'react-router-dom'
import useClock from '../../hooks/useClock'
import { formatTime } from '../../utils/incidents'

function Stat({ label, value, tone }) {
  return (
    <div className={`topbar__stat${tone ? ` topbar__stat--${tone}` : ''}`}>
      <span className="label">{label}</span>
      <span className="topbar__value mono">{value}</span>
    </div>
  )
}

export default function TopBar({ health, active, critical, updatedAt, onMenu }) {
  const now = useClock()
  const state = health === 'ok' ? { text: 'OPERATIONAL', cls: 'ok' } : health === 'down' ? { text: 'BACKEND OFFLINE', cls: 'down' } : { text: 'CONNECTING', cls: 'wait' }
  return (
    <header className="topbar">
      <button className="topbar__menu btn" onClick={onMenu} aria-label="Toggle navigation">Menu</button>
      <div className="topbar__brand">EIR<span> Emergency Intelligence</span></div>
      <div className={`topbar__status topbar__status--${state.cls}`} role="status">
        <span className="dot" aria-hidden="true" />{state.text}
      </div>
      <Stat label="Active" value={active ?? '—'} />
      <Stat label="Critical" value={critical ?? '—'} tone={critical > 0 ? 'critical' : undefined} />
      <Stat label="Last update" value={updatedAt ? formatTime(updatedAt, true) : '—'} />
      <div className="topbar__spacer" />
      <div className="topbar__clock mono" aria-label="Current time">{formatTime(now, true)}</div>
      <Link to="/report" className="btn btn--danger topbar__report">Report</Link>
    </header>
  )
}
