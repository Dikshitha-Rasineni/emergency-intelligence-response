import { useEffect, useMemo, useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import usePolling from '../../hooks/usePolling'
import { getHealth, listIncidents } from '../../services/api'
import { normalizeIncidentList, byUrgency, isOpen } from '../../utils/incidents'

/* Owns shared operational data; pages receive it through Outlet context. */
export default function AppShell() {
  const [navOpen, setNavOpen] = useState(false)
  const [health, setHealth] = useState('wait')
  const inc = usePolling(listIncidents, 5000)

  useEffect(() => {
    let alive = true
    const check = () => getHealth().then(() => alive && setHealth('ok')).catch(() => alive && setHealth('down'))
    check()
    const t = setInterval(check, 10000)
    return () => { alive = false; clearInterval(t) }
  }, [])

  const incidents = useMemo(() => (inc.data ? normalizeIncidentList(inc.data).filter(isOpen).sort(byUrgency) : []), [inc.data])
  const critical = incidents.filter((i) => i.severity === 'CRITICAL').length

  return (
    <div className="shell">
      <TopBar health={health} active={inc.data ? incidents.length : null} critical={inc.data ? critical : null}
        updatedAt={inc.updatedAt} onMenu={() => setNavOpen((o) => !o)} />
      <Sidebar open={navOpen} onNavigate={() => setNavOpen(false)} />
      <main className="shell__main">
        <Outlet context={{ incidents, loading: inc.loading, error: inc.error, hasData: !!inc.data, refresh: inc.refresh }} />
      </main>
    </div>
  )
}
