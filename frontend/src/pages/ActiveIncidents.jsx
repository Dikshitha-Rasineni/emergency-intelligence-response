import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import usePolling from '../hooks/usePolling'
import { getIncidents } from '../services/api'
import SeverityBadge from '../components/incidents/SeverityBadge'
import PriorityScore from '../components/incidents/PriorityScore'
import { LoadingState, EmptyState, ErrorState } from '../components/common/States'
import { normalizeIncidentList, isOpen, shortId, formatTime, minutesAgo, relativeTime, SEVERITY } from '../utils/incidents'
import { apiErrorMessage } from '../utils/errors'
import './screens.css'

const timeOf = (i) => new Date(i.time).getTime() || 0
const RECENT_MIN = 15

export default function ActiveIncidents() {
  const { data, error, loading, updatedAt, refresh } = usePolling(getIncidents, 5000)
  const [status, setStatus] = useState('OPEN')
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState('newest')
  const [fresh, setFresh] = useState(() => new Set())
  const known = useRef(null)

  const all = useMemo(() => (data ? normalizeIncidentList(data) : []), [data])

  useEffect(() => {
    if (!data) return
    const ids = new Set(all.map((i) => i.id))
    if (known.current) {
      const added = all.filter((i) => !known.current.has(i.id)).map((i) => i.id)
      if (added.length) { setFresh(new Set(added)); setTimeout(() => setFresh(new Set()), 6000) }
    }
    known.current = ids
  }, [all, data])

  const statuses = useMemo(() => [...new Set(all.map((i) => i.status))], [all])
  const showSeverity = all.some((i) => i.severityKnown)

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase()
    const list = all.filter((i) =>
      (status === 'ALL' || (status === 'OPEN' ? isOpen(i) : i.status === status)) &&
      (!q || `${i.id} ${i.description} ${i.location}`.toLowerCase().includes(q)))
    return list.sort(sort === 'newest'
      ? (a, b) => timeOf(b) - timeOf(a)
      : (a, b) => SEVERITY[b.severity].rank - SEVERITY[a.severity].rank || b.priority - a.priority || timeOf(b) - timeOf(a))
  }, [all, status, query, sort])

  return (
    <section className="page">
      <div className="page__bar">
        <h1 className="page__title">Active incidents</h1>
        <span className="mono panel__meta">{data ? `${rows.length} of ${all.length} shown` : ''}{updatedAt ? ` · updated ${formatTime(updatedAt, true)}` : ''}</span>
      </div>

      <div className="filters" role="search">
        <input className="input" type="search" placeholder="Search ID, description, location" aria-label="Search incidents" value={query} onChange={(e) => setQuery(e.target.value)} />
        <label>Status
          <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="OPEN">Open</option>
            <option value="ALL">All</option>
            {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label>Sort
          <select className="input" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="newest">Newest first</option>
            <option value="urgency" disabled={!showSeverity}>Severity and priority{showSeverity ? '' : ' (not assessed yet)'}</option>
          </select>
        </label>
      </div>

      <div className="panel">
        {loading && !data && <LoadingState steps={['Contacting backend', 'Loading incidents']} />}
        {error && !data && <ErrorState title="Incidents unavailable" onRetry={refresh}>{apiErrorMessage(error)}</ErrorState>}
        {error && data && <p className="stale">Connection lost. Showing last known data.</p>}
        {data && all.length === 0 && <EmptyState title="No incidents recorded">Reports appear here as soon as they are submitted. <Link to="/report">Report an emergency</Link></EmptyState>}
        {data && all.length > 0 && rows.length === 0 && <EmptyState title="No incidents match these filters">Clear the search or change the status filter.</EmptyState>}

        {rows.length > 0 && (
          <>
            <div className="irow irow--head" aria-hidden="true">
              <span>Priority</span><span>Incident</span><span>Affected</span><span>Injured</span><span>Status</span><span>Reported</span>
            </div>
            <ul className="ilist">
              {rows.map((i, idx) => {
                const recent = minutesAgo(i.time) !== null && minutesAgo(i.time) <= RECENT_MIN
                return (
                  <li key={i.id}>
                    <Link to={`/incidents/${i.id}`} className={`irow irow--${i.severityKnown ? i.severity.toLowerCase() : 'unknown'}${fresh.has(i.id) ? ' is-new' : ''}`}>
                      <PriorityScore value={i.priority} severity={i.severity} known={i.priorityKnown} />
                      <span className="irow__main">
                        <span className="irow__ids">
                          <span className="mono irow__id">{shortId(i.id)}</span>
                          {i.typeKnown && <span className="inc__type">{i.type}</span>}
                          {showSeverity && <SeverityBadge severity={i.severity} known={i.severityKnown} />}
                          {sort === 'newest' && idx === 0 && recent && <span className="tag tag--new">NEWEST</span>}
                          {recent && idx !== 0 && <span className="tag">RECENT</span>}
                        </span>
                        <span className="irow__desc">{i.description || 'No description'}</span>
                        <span className="irow__loc">{i.location}</span>
                      </span>
                      <span className="irow__num mono"><span className="sr-only">Affected </span>{i.affected}</span>
                      <span className={`irow__num mono${i.injuries ? ' irow__num--hot' : ''}`}><span className="sr-only">Injured </span>{i.injuries}</span>
                      <span className="irow__status">{i.status}</span>
                      <span className="irow__time"><span className="mono">{formatTime(i.time)}</span><span className="irow__rel">{relativeTime(i.time)}</span></span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          </>
        )}
      </div>
    </section>
  )
}
