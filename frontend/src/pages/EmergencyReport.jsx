import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import EmergencyMap from '../components/map/EmergencyMap'

import { createIncident } from '../services/api'

import {
  normalizeIncident,
  shortId,
  formatCoord,
} from '../utils/incidents'

import { apiErrorMessage } from '../utils/errors'

import './screens.css'

const EMPTY = {
  description: '',
  location: '',
  latitude: '',
  longitude: '',
  affected_people: '0',
  injuries: '',
}

function validate(f) {
  const e = {}

  if (!f.description.trim()) {
    e.description = 'Describe what happened.'
  }

  if (!f.location.trim()) {
    e.location = 'Enter where it is happening.'
  }

  const lat = Number(f.latitude)
  const lon = Number(f.longitude)

  if (
    f.latitude.trim() === '' ||
    !Number.isFinite(lat) ||
    lat < -90 ||
    lat > 90
  ) {
    e.latitude =
      'Latitude must be between -90 and 90.'
  }

  if (
    f.longitude.trim() === '' ||
    !Number.isFinite(lon) ||
    lon < -180 ||
    lon > 180
  ) {
    e.longitude =
      'Longitude must be between -180 and 180.'
  }

  const aff = Number(f.affected_people)
  const inj = Number(f.injuries)

  if (
    !Number.isInteger(aff) ||
    aff < 0
  ) {
    e.affected_people =
      'Enter a whole number, 0 or more.'
  }

  if (
    !Number.isInteger(inj) ||
    inj < 0
  ) {
    e.injuries =
      'Enter a whole number, 0 or more.'
  } else if (
    Number.isInteger(aff) &&
    inj > aff
  ) {
    e.injuries =
      'Injuries cannot exceed people affected.'
  }

  return e
}

function Field({
  label,
  error,
  hint,
  children,
  id,
}) {
  return (
    <div
      className={`field${error ? ' has-error' : ''}`}
    >
      <label htmlFor={id}>
        {label}
      </label>

      {children}

      {error ? (
        <p
          className="field__msg"
          role="alert"
        >
          {error}
        </p>
      ) : (
        hint && (
          <p className="field__hint">
            {hint}
          </p>
        )
      )}
    </div>
  )
}

function Counter({
  id,
  value,
  onChange,
  invalid,
}) {
  const n = Number(value) || 0

  return (
    <div className="counter">
      <button
        type="button"
        className="btn"
        aria-label="Decrease"
        onClick={() =>
          onChange(
            String(Math.max(0, n - 1))
          )
        }
      >
        −
      </button>

      <input
        id={id}
        className="input mono"
        inputMode="numeric"
        value={value}
        aria-invalid={invalid}
        onChange={(e) =>
          onChange(
            e.target.value.replace(
              /[^\d]/g,
              ''
            )
          )
        }
      />

      <button
        type="button"
        className="btn"
        aria-label="Increase"
        onClick={() =>
          onChange(String(n + 1))
        }
      >
        +
      </button>
    </div>
  )
}

export default function EmergencyReport() {
  const [form, setForm] =
    useState(EMPTY)

  const [attempted, setAttempted] =
    useState(false)

  const [submitting, setSubmitting] =
    useState(false)

  const [apiError, setApiError] =
    useState(null)

  const [created, setCreated] =
    useState(null)

  const [geoMsg, setGeoMsg] =
    useState(null)

  const errors = useMemo(
    () => validate(form),
    [form]
  )

  const shown = attempted
    ? errors
    : {}

  const set = (key) => (value) =>
    setForm((current) => ({
      ...current,
      [key]:
        typeof value === 'string'
          ? value
          : value.target.value,
    }))

  /*
   * Preview incident for the real map.
   */
  const preview = useMemo(() => {
    if (
      errors.latitude ||
      errors.longitude
    ) {
      return []
    }

    return [
      {
        id: 'preview',
        type: 'REPORT',
        severity: 'CRITICAL',
        severityKnown: false,
        lat: Number(form.latitude),
        lon: Number(form.longitude),
      },
    ]
  }, [
    form.latitude,
    form.longitude,
    errors.latitude,
    errors.longitude,
  ])

  /*
   * Use the browser's current position.
   */
  function useMyPosition() {
    if (!navigator.geolocation) {
      setGeoMsg(
        'Location is not available in this browser.'
      )

      return
    }

    setGeoMsg(
      'Reading position…'
    )

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude =
          position.coords.latitude.toFixed(6)

        const longitude =
          position.coords.longitude.toFixed(6)

        setForm((current) => ({
          ...current,
          latitude,
          longitude,
        }))

        setGeoMsg(
          'Current position selected.'
        )
      },

      () => {
        setGeoMsg(
          'Position unavailable. Enter coordinates manually or select a point on the map.'
        )
      },

      {
        enableHighAccuracy: true,
        timeout: 8000,
      }
    )
  }

  /*
   * Select the emergency location
   * directly from the Leaflet map.
   */
  function handleMapLocationSelect({
    latitude,
    longitude,
  }) {
    setForm((current) => ({
      ...current,

      latitude:
        latitude.toFixed(6),

      longitude:
        longitude.toFixed(6),
    }))

    setGeoMsg(
      'Location selected from the map.'
    )

    /*
     * If the user hasn't entered a location
     * description yet, give them a useful
     * temporary label.
     */
    if (!form.location.trim()) {
      setForm((current) => ({
        ...current,

        latitude:
          latitude.toFixed(6),

        longitude:
          longitude.toFixed(6),

        location:
          'Selected map location',
      }))
    }
  }

  async function submit(e) {
    e.preventDefault()

    setAttempted(true)
    setApiError(null)

    if (
      Object.keys(errors).length
    ) {
      return
    }

    setSubmitting(true)

    try {
      const res =
        await createIncident({
          description:
            form.description.trim(),

          latitude:
            Number(form.latitude),

          longitude:
            Number(form.longitude),

          affected_people:
            Number(
              form.affected_people
            ),

          injuries:
            Number(form.injuries),

          location:
            form.location.trim(),
        })

      setCreated(
        normalizeIncident(
          res?.incident ??
            res ??
            {}
        )
      )
    } catch (err) {
      setApiError(
        apiErrorMessage(err)
      )
    } finally {
      setSubmitting(false)
    }
  }

  /*
   * Success screen.
   */
  if (created) {
    return (
      <section className="page report">
        <div
          className="success"
          role="status"
        >
          <p className="label">
            Report received
          </p>

          <h1 className="success__title">
            INCIDENT CREATED
          </h1>

          {created.id ? (
            <p className="success__id mono">
              {shortId(created.id)}
            </p>
          ) : (
            <p className="field__msg">
              The backend accepted the
              report but did not return an
              incident ID. Check the Active
              Incidents list.
            </p>
          )}

          <p className="success__desc">
            {form.description}
          </p>

          <p className="mono success__meta">
            {form.location} ·{' '}
            {form.latitude},{' '}
            {form.longitude} ·{' '}
            {form.affected_people}{' '}
            affected ·{' '}
            {form.injuries} injured
          </p>

          <div className="actions">
            {created.id && (
              <Link
                to={`/incidents/${created.id}`}
                className="btn btn--primary"
              >
                Open incident workspace
              </Link>
            )}

            <Link
              to="/incidents"
              className="btn"
            >
              View active incidents
            </Link>

            <button
              className="btn"
              onClick={() => {
                setCreated(null)
                setForm(EMPTY)
                setAttempted(false)
                setGeoMsg(null)
              }}
            >
              Report another
            </button>
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="page report">
      <h1 className="page__title">
        Report emergency
      </h1>

      <form
        className="report__grid"
        onSubmit={submit}
        noValidate
      >
        <div className="report__form">

          {/* =====================================
              WHAT HAPPENED
          ====================================== */}

          <div className="fsec">
            <h2 className="fsec__title">
              What happened?
            </h2>

            <Field
              id="description"
              label="Emergency description"
              error={shown.description}
              hint="Type, hazards, what you can see. Keep it short."
            >
              <textarea
                id="description"
                className="input"
                rows="4"
                autoFocus
                value={form.description}
                onChange={set(
                  'description'
                )}
                placeholder="Major accident near highway"
                aria-invalid={
                  !!shown.description
                }
              />
            </Field>
          </div>

          {/* =====================================
              WHERE
          ====================================== */}

          <div className="fsec">
            <h2 className="fsec__title">
              Where?
            </h2>

            <Field
              id="location"
              label="Location"
              error={shown.location}
              hint="Enter a recognizable place, road, landmark or address."
            >
              <input
                id="location"
                className="input"
                value={form.location}
                onChange={set('location')}
                placeholder="MG Road, Bengaluru"
                aria-invalid={
                  !!shown.location
                }
              />
            </Field>

            <div className="row2">
              <Field
                id="latitude"
                label="Latitude"
                error={shown.latitude}
              >
                <input
                  id="latitude"
                  className="input mono"
                  inputMode="decimal"
                  value={form.latitude}
                  onChange={set(
                    'latitude'
                  )}
                  placeholder="12.9716"
                  aria-invalid={
                    !!shown.latitude
                  }
                />
              </Field>

              <Field
                id="longitude"
                label="Longitude"
                error={shown.longitude}
              >
                <input
                  id="longitude"
                  className="input mono"
                  inputMode="decimal"
                  value={form.longitude}
                  onChange={set(
                    'longitude'
                  )}
                  placeholder="77.5946"
                  aria-invalid={
                    !!shown.longitude
                  }
                />
              </Field>
            </div>

            <div className="actions">
              <button
                type="button"
                className="btn"
                onClick={
                  useMyPosition
                }
              >
                Use my current position
              </button>

              <span className="field__hint">
                Or click directly on the
                map to select the incident
                location.
              </span>
            </div>

            {geoMsg && (
              <span className="field__hint geo">
                {geoMsg}
              </span>
            )}
          </div>

          {/* =====================================
              IMPACT
          ====================================== */}

          <div className="fsec">
            <h2 className="fsec__title">
              Impact
            </h2>

            <div className="row2">
              <Field
                id="affected_people"
                label="People affected"
                error={
                  shown.affected_people
                }
              >
                <Counter
                  id="affected_people"
                  value={
                    form.affected_people
                  }
                  onChange={set(
                    'affected_people'
                  )}
                  invalid={
                    !!shown.affected_people
                  }
                />
              </Field>

              <Field
                id="injuries"
                label="Injuries"
                error={shown.injuries}
              >
                <Counter
                  id="injuries"
                  value={form.injuries}
                  onChange={set(
                    'injuries'
                  )}
                  invalid={
                    !!shown.injuries
                  }
                />
              </Field>
            </div>
          </div>

          {/* =====================================
              ERRORS
          ====================================== */}

          {apiError && (
            <div
              className="state state--error"
              role="alert"
            >
              <p className="state__title">
                Report not sent
              </p>

              <p className="state__body">
                {apiError}
              </p>
            </div>
          )}

          {attempted &&
            Object.keys(errors).length >
              0 && (
              <p
                className="field__msg"
                role="alert"
              >
                Fix the highlighted
                fields to submit.
              </p>
            )}

          <button
            type="submit"
            className="submit"
            disabled={submitting}
          >
            {submitting
              ? 'TRANSMITTING REPORT…'
              : 'SUBMIT EMERGENCY'}
          </button>
        </div>

        {/* =====================================
            REAL MAP
        ====================================== */}

        <aside className="panel report__map">
          <header className="panel__head">
            <h2>
              Select incident location
            </h2>

            <span className="mono panel__meta">
              {preview.length
                ? `${formatCoord(
                    preview[0].lat
                  )}, ${formatCoord(
                    preview[0].lon
                  )}`
                : 'Click map to select'}
            </span>
          </header>

          <EmergencyMap
            incidents={preview}
            selectedId="preview"
            onSelect={() => {}}
            onLocationSelect={
              handleMapLocationSelect
            }
          />

          <p className="field__hint">
            Click anywhere on the map to
            place the emergency location.
          </p>
        </aside>
      </form>
    </section>
  )
}