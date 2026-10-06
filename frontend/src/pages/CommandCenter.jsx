import { useEffect, useRef, useState } from 'react'
import { useOutletContext, Link } from 'react-router-dom'

import EmergencyMap from '../components/map/EmergencyMap'
import IncidentRow from '../components/incidents/IncidentRow'
import SeverityBadge from '../components/incidents/SeverityBadge'
import {
  LoadingState,
  EmptyState,
  ErrorState,
} from '../components/common/States'

import {
  formatCoord,
  formatTime,
  shortId,
} from '../utils/incidents'

import { getNearbyResources } from '../services/api'

function Metric({ label, value, tone, note }) {
  return (
    <div className={`metric${tone ? ` metric--${tone}` : ''}`}>
      <span className="metric__value mono">
        {value}
      </span>

      <span className="metric__label">
        {label}
      </span>

      {note && (
        <span className="metric__note">
          {note}
        </span>
      )}
    </div>
  )
}

export default function CommandCenter() {
  const {
    incidents,
    loading,
    error,
    hasData,
    refresh,
  } = useOutletContext()

  const [selectedId, setSelectedId] = useState(null)
  const [alert, setAlert] = useState(null)
  const [freshIds, setFreshIds] = useState(
    () => new Set()
  )

  const [resources, setResources] = useState([])
  const [resourcesLoading, setResourcesLoading] =
    useState(false)
  const [resourcesError, setResourcesError] =
    useState(null)

  const known = useRef(null)

  /*
   * Detect newly arrived incidents after the first load.
   */
  useEffect(() => {
    if (!hasData) return

    const ids = new Set(
      incidents.map((i) => i.id)
    )

    if (known.current) {
      const added = incidents.filter(
        (i) => !known.current.has(i.id)
      )

      if (added.length) {
        setAlert(added[0])

        setFreshIds(
          (s) =>
            new Set([
              ...s,
              ...added.map((a) => a.id),
            ])
        )

        setTimeout(
          () => setFreshIds(new Set()),
          6000
        )
      }
    }

    known.current = ids
  }, [incidents, hasData])

  /*
   * Currently selected incident.
   * Falls back to the first incident when
   * nothing has been explicitly selected.
   */
  const selected =
    incidents.find(
      (i) => i.id === selectedId
    ) ?? incidents[0]

  const critical = incidents.filter(
    (i) => i.severity === 'CRITICAL'
  )

  const affected = incidents.reduce(
    (n, i) => n + i.affected,
    0
  )

  const injured = incidents.reduce(
    (n, i) => n + i.injuries,
    0
  )

  /*
   * Load nearby resources for the selected incident.
   *
   * The backend uses PostGIS to calculate:
   * - distance
   * - availability
   * - available units
   * - wait time
   */
  useEffect(() => {
    let cancelled = false

    const loadResources = async () => {
      if (!selected?.id) {
        setResources([])
        setResourcesError(null)
        return
      }

      setResourcesLoading(true)
      setResourcesError(null)

      try {
        const result = await getNearbyResources(
          selected.id,
          25
        )

        if (!cancelled) {
          setResources(result)
        }
      } catch (err) {
        console.error(
          'Failed to load nearby resources:',
          err
        )

        if (!cancelled) {
          setResources([])
          setResourcesError(err)
        }
      } finally {
        if (!cancelled) {
          setResourcesLoading(false)
        }
      }
    }

    loadResources()

    return () => {
      cancelled = true
    }
  }, [selected?.id])

  return (
    <section className="cc">
      {alert && (
        <div
          className={`alert alert--${alert.severity.toLowerCase()}`}
          role="alert"
        >
          <strong>
            New incident
          </strong>

          <span className="mono">
            {shortId(alert.id)}
          </span>

          <span>
            {alert.type}
          </span>

          <SeverityBadge
            severity={alert.severity}
          />

          <span className="alert__loc">
            {alert.location}
          </span>

          <Link
            to={`/incidents/${alert.id}`}
            className="btn"
          >
            Open
          </Link>

          <button
            className="btn"
            onClick={() => setAlert(null)}
          >
            Acknowledge
          </button>
        </div>
      )}

      <div
        className="metrics"
        aria-label="Operational summary"
      >
        <Metric
          label="Active incidents"
          value={incidents.length}
        />

        <Metric
          label="Critical"
          value={critical.length}
          tone={
            critical.length
              ? 'critical'
              : undefined
          }
          note={
            critical.length
              ? 'Needs attention'
              : 'None'
          }
        />

        <Metric
          label="People affected"
          value={affected}
        />

        <Metric
          label="Injured"
          value={injured}
          tone={
            injured
              ? 'high'
              : undefined
          }
        />

        <Metric
          label="Resources available"
          value={
            resourcesLoading
              ? '…'
              : resources.length
          }
          note={
            resourcesError
              ? 'Resource API unavailable'
              : selected
                ? `Within 25 km of ${shortId(selected.id)}`
                : 'No incident selected'
          }
        />

        <Metric
          label="Sensor alerts"
          value="—"
          note="Awaiting IoT API"
        />
      </div>

      <div className="cc__body">
        <div className="panel cc__map">
          <header className="panel__head">
            <h2>
              Situation map
            </h2>

            {selected && (
              <span className="mono panel__meta">
                {formatCoord(selected.lat)},{' '}
                {formatCoord(selected.lon)}
              </span>
            )}
          </header>

          <EmergencyMap
            incidents={incidents}
            selectedId={selected?.id}
            onSelect={setSelectedId}
            resources={resources}
          />

          {selected && (
            <div className="brief">
              <SeverityBadge
                severity={selected.severity}
              />

              <span className="mono">
                {shortId(selected.id)}
              </span>

              <span>
                {selected.type}
              </span>

              <span className="brief__desc">
                {selected.description ||
                  selected.location}
              </span>

              <span className="mono">
                {formatTime(selected.time)}
              </span>
            </div>
          )}
        </div>

        <div className="panel cc__queue">
          <header className="panel__head">
            <h2>
              Incident queue
            </h2>

            <span className="panel__meta">
              Sorted by severity, then priority
            </span>
          </header>

          {loading && !hasData && (
            <LoadingState
              steps={[
                'Contacting backend',
                'Loading incidents',
              ]}
            />
          )}

          {error && !hasData && (
            <ErrorState
              title="Incidents unavailable"
              onRetry={refresh}
            >
              The backend did not return the
              incident list. Check that the API
              is running.
            </ErrorState>
          )}

          {hasData &&
            incidents.length === 0 && (
              <EmptyState title="No active incidents">
                New reports appear here as they
                arrive.{' '}
                <Link to="/report">
                  Report an emergency
                </Link>
              </EmptyState>
            )}

          {error && hasData && (
            <p className="stale">
              Connection lost. Showing last known
              data.
            </p>
          )}

          <ul className="queue">
            {incidents.map((i) => (
              <IncidentRow
                key={i.id}
                incident={i}
                selected={
                  i.id === selected?.id
                }
                isNew={freshIds.has(i.id)}
                onSelect={setSelectedId}
              />
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}