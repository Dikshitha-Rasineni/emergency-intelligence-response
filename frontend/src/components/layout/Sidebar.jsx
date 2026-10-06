import { NavLink } from 'react-router-dom'

const NAV = [
  { group: null, items: [{ to: '/', label: 'Command Center', end: true }, { to: '/incidents', label: 'Active Incidents' }, { to: '/report', label: 'Report Emergency', action: true }] },
  { group: 'Resources', items: [{ to: '/resources', label: 'Resource Intelligence' }] },
  { group: 'Geospatial', items: [{ to: '/map', label: 'Emergency Map' }] },
  { group: 'Intelligence', items: [{ to: '/intelligence', label: 'Response Intelligence' }] },
  { group: 'Field data', items: [{ to: '/sensors', label: 'Sensor Monitoring' }] },
  { group: 'Review', items: [{ to: '/analytics', label: 'Analytics' }, { to: '/history', label: 'History' }] },
  { group: 'System', items: [{ to: '/admin', label: 'Users' }, { to: '/settings', label: 'Settings' }] },
]

export default function Sidebar({ open, onNavigate }) {
  return (
    <nav className={`sidebar${open ? ' is-open' : ''}`} aria-label="Primary">
      {NAV.map((sec) => (
        <div key={sec.group ?? 'main'} className="sidebar__group">
          {sec.group && <p className="label sidebar__heading">{sec.group}</p>}
          {sec.items.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} onClick={onNavigate}
              className={({ isActive }) => `sidebar__link${isActive ? ' is-active' : ''}${n.action ? ' sidebar__link--action' : ''}`}>
              {n.label}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  )
}
