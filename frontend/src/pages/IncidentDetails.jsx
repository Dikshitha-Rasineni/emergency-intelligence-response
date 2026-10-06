import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import usePolling from '../hooks/usePolling'

import {
  getIncident,
  getNearbyResources,
  extractEmergencyInformation,
  detectMissingInformation,
  getSafetyPrecautions,
  getReporterGuidance,
  generateResponseRecommendation,
  generateIncidentReport,
} from '../services/api'

import EmergencyMap from '../components/map/EmergencyMap'
import SeverityBadge from '../components/incidents/SeverityBadge'
import ModulePanel from '../components/common/ModulePanel'
import { LoadingState, ErrorState } from '../components/common/States'

import {
  normalizeIncident,
  shortId,
  formatCoord,
  formatDateTime,
  relativeTime,
} from '../utils/incidents'

import { apiErrorMessage } from '../utils/errors'

import './screens.css'


function Fact({ label, children, mono }) {
  return (
    <div className="fact">
      <dt className="label">{label}</dt>
      <dd className={mono ? 'mono' : undefined}>{children}</dd>
    </div>
  )
}


function ResourceList({ resources, loading, error }) {
  if (loading) {
    return <p className="state">Loading nearby resources...</p>
  }

  if (error) {
    return (
      <p className="state">
        Unable to load nearby resources.
      </p>
    )
  }

  if (!resources.length) {
    return (
      <p className="state">
        No emergency resources found within the selected radius.
      </p>
    )
  }

  return (
    <div className="resource-list">
      {resources.map((resource) => (
        <article className="resource-card" key={resource.id}>
          <div className="resource-card__head">
            <div>
              <p className="label">
                {resource.resource_type.replaceAll('_', ' ')}
              </p>

              <h3>{resource.name}</h3>
            </div>

            <span className="mono resource-card__distance">
              {resource.distance_km.toFixed(2)} km
            </span>
          </div>

          <div className="resource-card__facts">
            <div>
              <span className="label">Availability</span>
              <strong>{resource.availability_status}</strong>
            </div>

            <div>
              <span className="label">Units</span>
              <strong className="mono">
                {resource.available_units}
              </strong>
            </div>

            <div>
              <span className="label">Wait</span>
              <strong className="mono">
                {resource.wait_time_minutes} min
              </strong>
            </div>
          </div>

          {resource.address && (
            <p className="resource-card__address">
              {resource.address}
            </p>
          )}
        </article>
      ))}
    </div>
  )
}


function ListBlock({ items, emptyText = 'None available.' }) {
  if (!Array.isArray(items) || items.length === 0) {
    return <p className="state">{emptyText}</p>
  }

  return (
    <ul>
      {items.map((item, index) => (
        <li key={index}>{item}</li>
      ))}
    </ul>
  )
}


/* =========================================================
   MULTILINGUAL RESPONSE HELPERS
   Localized text is additive: the English fields are always
   present on the payload, `localized.fields` holds the
   reporter-language version of the free-text fields only.
   ========================================================= */

function hasLocalized(data) {
  return (
    data?.localized?.translation_status === 'ok' &&
    data.localized.fields != null &&
    typeof data.localized.fields === 'object'
  )
}

function pickText(data, field, showLocal) {
  if (showLocal && hasLocalized(data)) {
    const value = data.localized.fields[field]

    if (value !== undefined && value !== null) {
      return value
    }
  }

  return data?.[field]
}

function LanguageToggle({ data, showLocal, onToggle }) {
  if (!data?.localized) {
    return null
  }

  const language =
    data.response_language ||
    data.localized.language ||
    'original language'

  if (!hasLocalized(data)) {
    return (
      <p className="state">
        Translation to {language} is unavailable.
        {' '}
        Showing English.
      </p>
    )
  }

  return (
    <div>
      <button
        type="button"
        className="btn"
        onClick={onToggle}
      >
        {showLocal
          ? 'Show English'
          : `Show ${language}`}
      </button>
    </div>
  )
}


function ModuleHeader({ label, title, status }) {
  return (
    <header className="panel__head">
      <div>
        <p className="label">{label}</p>
        <h2>{title}</h2>
      </div>

      <span className="module__tag">
        {status}
      </span>
    </header>
  )
}


export default function IncidentDetails() {
  const { id } = useParams()

  const {
    data,
    error,
    loading,
    refresh,
  } = usePolling(() => getIncident(id), 10000, id)

  const [copied, setCopied] = useState(false)

  /* =========================================================
     RESOURCE INTELLIGENCE
     ========================================================= */

  const [resources, setResources] = useState([])
  const [resourcesLoading, setResourcesLoading] = useState(true)
  const [resourcesError, setResourcesError] = useState(null)

  /* =========================================================
     3.1 — EMERGENCY UNDERSTANDING
     ========================================================= */

  const [aiData, setAiData] = useState(null)
  const [aiLoading, setAiLoading] = useState(true)
  const [aiError, setAiError] = useState(null)

  /* =========================================================
     3.3 — MISSING INFORMATION
     ========================================================= */

  const [missingData, setMissingData] = useState(null)
  const [missingLoading, setMissingLoading] = useState(true)
  const [missingError, setMissingError] = useState(null)

  /* =========================================================
     3.4 — SAFETY PRECAUTIONS
     ========================================================= */

  const [safetyData, setSafetyData] = useState(null)
  const [safetyLoading, setSafetyLoading] = useState(true)
  const [safetyError, setSafetyError] = useState(null)

  /* =========================================================
     3.5 — REPORTER GUIDANCE
     ========================================================= */

  const [guidanceData, setGuidanceData] = useState(null)
  const [guidanceLoading, setGuidanceLoading] = useState(true)
  const [guidanceError, setGuidanceError] = useState(null)

  /* =========================================================
     3.6 — RESPONSE GENERATION
     ========================================================= */

  const [responseData, setResponseData] = useState(null)
  const [responseLoading, setResponseLoading] = useState(true)
  const [responseError, setResponseError] = useState(null)

  /* =========================================================
     3.7 — INCIDENT REPORT
     ========================================================= */

  const [reportData, setReportData] = useState(null)
  const [reportLoading, setReportLoading] = useState(true)
  const [reportError, setReportError] = useState(null)

  /* Multilingual: true = show the reporter's language when available */
  const [showLocalResponse, setShowLocalResponse] = useState(true)
  const [showLocalReport, setShowLocalReport] = useState(true)


  /* =========================================================
     LOAD NEARBY RESOURCES
     ========================================================= */

  useEffect(() => {
    let cancelled = false

    const loadResources = async () => {
      setResourcesLoading(true)
      setResourcesError(null)

      try {
        const result = await getNearbyResources(id, 25)

        if (!cancelled) {
          setResources(Array.isArray(result) ? result : [])
        }
      } catch (err) {
        if (!cancelled) {
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
  }, [id])


  /* =========================================================
     3.1 — EMERGENCY UNDERSTANDING
     ========================================================= */

  useEffect(() => {
    let cancelled = false

    const loadAI = async () => {
      setAiLoading(true)
      setAiError(null)

      try {
        const result = await extractEmergencyInformation(id)

        if (!cancelled) {
          setAiData(result)
        }
      } catch (err) {
        console.error(
          'Failed to load AI understanding:',
          err
        )

        if (!cancelled) {
          setAiError(err)
        }
      } finally {
        if (!cancelled) {
          setAiLoading(false)
        }
      }
    }

    loadAI()

    return () => {
      cancelled = true
    }
  }, [id])


  /* =========================================================
     3.3 — MISSING INFORMATION
     ========================================================= */

  useEffect(() => {
    let cancelled = false

    const loadMissingInformation = async () => {
      setMissingLoading(true)
      setMissingError(null)

      try {
        const result = await detectMissingInformation(id)

        if (!cancelled) {
          setMissingData(result)
        }
      } catch (err) {
        console.error(
          'Failed to load missing information:',
          err
        )

        if (!cancelled) {
          setMissingError(err)
        }
      } finally {
        if (!cancelled) {
          setMissingLoading(false)
        }
      }
    }

    loadMissingInformation()

    return () => {
      cancelled = true
    }
  }, [id])


  /* =========================================================
     3.4 — SAFETY PRECAUTIONS
     ========================================================= */

  useEffect(() => {
    let cancelled = false

    const loadSafety = async () => {
      setSafetyLoading(true)
      setSafetyError(null)

      try {
        const result = await getSafetyPrecautions(id)

        if (!cancelled) {
          setSafetyData(result)
        }
      } catch (err) {
        console.error(
          'Failed to load safety precautions:',
          err
        )

        if (!cancelled) {
          setSafetyError(err)
        }
      } finally {
        if (!cancelled) {
          setSafetyLoading(false)
        }
      }
    }

    loadSafety()

    return () => {
      cancelled = true
    }
  }, [id])


  /* =========================================================
     3.5 — REPORTER GUIDANCE
     ========================================================= */

  useEffect(() => {
    let cancelled = false

    const loadGuidance = async () => {
      setGuidanceLoading(true)
      setGuidanceError(null)

      try {
        const result = await getReporterGuidance(id)

        if (!cancelled) {
          setGuidanceData(result)
        }
      } catch (err) {
        console.error(
          'Failed to load reporter guidance:',
          err
        )

        if (!cancelled) {
          setGuidanceError(err)
        }
      } finally {
        if (!cancelled) {
          setGuidanceLoading(false)
        }
      }
    }

    loadGuidance()

    return () => {
      cancelled = true
    }
  }, [id])


  /* =========================================================
     3.6 — RESPONSE GENERATION
     ========================================================= */

  useEffect(() => {
    let cancelled = false

    const loadResponse = async () => {
      setResponseLoading(true)
      setResponseError(null)

      try {
        const result = await generateResponseRecommendation(id)

        if (!cancelled) {
          setResponseData(result)
        }
      } catch (err) {
        console.error(
          'Failed to generate response recommendation:',
          err
        )

        if (!cancelled) {
          setResponseError(err)
        }
      } finally {
        if (!cancelled) {
          setResponseLoading(false)
        }
      }
    }

    loadResponse()

    return () => {
      cancelled = true
    }
  }, [id])


  /* =========================================================
     3.7 — INCIDENT REPORT
     ========================================================= */

  useEffect(() => {
    let cancelled = false

    const loadIncidentReport = async () => {
      setReportLoading(true)
      setReportError(null)

      try {
        const result = await generateIncidentReport(id)

        if (!cancelled) {
          setReportData(result)
        }
      } catch (err) {
        console.error(
          'Failed to generate incident report:',
          err
        )

        if (!cancelled) {
          setReportError(err)
        }
      } finally {
        if (!cancelled) {
          setReportLoading(false)
        }
      }
    }

    loadIncidentReport()

    return () => {
      cancelled = true
    }
  }, [id])


  /* =========================================================
     INCIDENT LOADING STATE
     ========================================================= */

  if (loading && !data) {
    return (
      <section className="page">
        <LoadingState
          steps={[
            'Contacting backend',
            `Loading ${id}`,
          ]}
        />
      </section>
    )
  }


  /* =========================================================
     INCIDENT ERROR STATE
     ========================================================= */

  if (error && !data) {
    const missing = error.response?.status === 404

    return (
      <section className="page">
        <ErrorState
          title={
            missing
              ? 'Incident not found'
              : 'Incident unavailable'
          }
          onRetry={missing ? undefined : refresh}
        >
          {missing
            ? `No incident with ID ${id} exists.`
            : apiErrorMessage(error)}

          {' '}

          <Link to="/incidents">
            Back to active incidents
          </Link>
        </ErrorState>
      </section>
    )
  }


  const i = normalizeIncident(
    data?.incident ?? data ?? {}
  )

  const hasCoords =
    i.lat !== null &&
    i.lon !== null


  /* =========================================================
     COPY COORDINATES
     ========================================================= */

  const copy = () =>
    navigator.clipboard
      ?.writeText(`${i.lat}, ${i.lon}`)
      .then(() => {
        setCopied(true)

        setTimeout(
          () => setCopied(false),
          1500
        )
      })


  return (
    <section className="page ws">

      {/* =====================================================
          INCIDENT HEADER
      ====================================================== */}

      <header
        className={`ws__head ws__head--${
          i.severityKnown
            ? i.severity.toLowerCase()
            : 'unknown'
        }`}
      >
        <div>
          <p className="label">Incident</p>

          <h1 className="ws__id mono">
            {shortId(i.id || id)}
          </h1>
        </div>

        {i.typeKnown && (
          <span className="inc__type">
            {i.type}
          </span>
        )}

        <SeverityBadge
          severity={i.severity}
          known={i.severityKnown}
        />

        <span className="ws__status">
          {i.status}
        </span>

        <span className="ws__created">
          <span className="mono">
            {formatDateTime(i.time)}
          </span>

          <span className="irow__rel">
            {relativeTime(i.time)}
          </span>
        </span>

        <Link
          to="/incidents"
          className="btn"
        >
          All incidents
        </Link>
      </header>


      {error && (
        <p className="stale">
          Connection lost. Showing last loaded record.
        </p>
      )}


      {/* =====================================================
          LOCATION + SITUATION
      ====================================================== */}

      <div className="ws__grid">

        <section className="panel ws__map">

          <header className="panel__head">
            <h2>Location</h2>

            <span className="mono panel__meta">
              {formatCoord(i.lat)}, {formatCoord(i.lon)}
            </span>
          </header>

          {hasCoords ? (
            <EmergencyMap
              incidents={[i]}
              selectedId={i.id}
              onSelect={() => {}}
              resources={resources}
            />
          ) : (
            <p className="state">
              This record has no coordinates.
            </p>
          )}

          <dl className="facts facts--row">

            <Fact label="Place">
              {i.location}
            </Fact>

            <Fact
              label="Latitude"
              mono
            >
              {formatCoord(i.lat)}
            </Fact>

            <Fact
              label="Longitude"
              mono
            >
              {formatCoord(i.lon)}
            </Fact>

            {hasCoords && (
              <div className="fact">
                <button
                  className="btn"
                  onClick={copy}
                >
                  {copied
                    ? 'Copied'
                    : 'Copy coordinates'}
                </button>
              </div>
            )}

          </dl>

        </section>


        <div className="ws__side">

          {/* Situation */}

          <section className="panel">

            <header className="panel__head">
              <h2>Situation</h2>
            </header>

            <p className="situation">
              {i.description ||
                'No description recorded.'}
            </p>

          </section>


          {/* Impact */}

          <section className="panel">

            <header className="panel__head">
              <h2>Impact</h2>
            </header>

            <div className="impact">

              <div>
                <span className="impact__n mono">
                  {i.affected}
                </span>

                <span className="label">
                  People affected
                </span>
              </div>

              <div
                className={
                  i.injuries
                    ? 'impact--hot'
                    : undefined
                }
              >
                <span className="impact__n mono">
                  {i.injuries}
                </span>

                <span className="label">
                  Injuries
                </span>
              </div>

            </div>

          </section>


          {/* Record */}

          <section className="panel">

            <header className="panel__head">
              <h2>Record</h2>
            </header>

            <dl className="facts">

              <Fact
                label="Incident ID"
                mono
              >
                {i.id || id}
              </Fact>

              <Fact label="Status">
                {i.status}
              </Fact>

              <Fact
                label="Created"
                mono
              >
                {formatDateTime(i.time)}
              </Fact>

            </dl>

          </section>

        </div>

      </div>


      {/* =====================================================
          INTELLIGENCE MODULES
      ====================================================== */}

      <div className="ws__modules">


        {/* ===================================================
            3.1 — EMERGENCY UNDERSTANDING
        ==================================================== */}

        <section className="panel module">

          <ModuleHeader
            label="GenAI"
            title="AI understanding"
            status={
              aiLoading
                ? 'PROCESSING'
                : aiError
                  ? 'ERROR'
                  : 'CONNECTED'
            }
          />

          <div className="module__body">

            {aiLoading && (
              <p className="state">
                Analyzing emergency report...
              </p>
            )}

            {aiError && (
              <p
                className="state state--error"
                role="alert"
              >
                Unable to load AI understanding.
                {' '}
                {apiErrorMessage(aiError)}
              </p>
            )}

            {aiData && (
              <>
                <dl className="facts">

                  <Fact label="Emergency type">
                    {aiData.emergency_type ||
                      'Not available'}
                  </Fact>

                  <Fact
                    label="Affected people"
                    mono
                  >
                    {aiData.affected_people ??
                      'Not available'}
                  </Fact>

                  <Fact
                    label="Injuries"
                    mono
                  >
                    {aiData.injuries ??
                      'Not available'}
                  </Fact>

                  <Fact label="Location">
                    {aiData.location_information ||
                      'Not available'}
                  </Fact>

                </dl>

                {Array.isArray(
                  aiData.critical_indicators
                ) &&
                  aiData.critical_indicators.length >
                    0 && (
                    <div>
                      <p className="label">
                        Critical indicators
                      </p>

                      <ul>
                        {aiData.critical_indicators.map(
                          (item, index) => (
                            <li key={index}>
                              {item}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}
              </>
            )}

            <p className="mono module__endpoint">
              POST /api/ai/extract
            </p>

          </div>

        </section>


        {/* ===================================================
            3.3 — MISSING INFORMATION
        ==================================================== */}

        <section className="panel module">

          <ModuleHeader
            label="GenAI"
            title="Missing information"
            status={
              missingLoading
                ? 'PROCESSING'
                : missingError
                  ? 'ERROR'
                  : 'CONNECTED'
            }
          />

          <div className="module__body">

            {missingLoading && (
              <p className="state">
                Checking for missing information...
              </p>
            )}

            {missingError && (
              <p
                className="state state--error"
                role="alert"
              >
                Unable to check missing information.
                {' '}
                {apiErrorMessage(missingError)}
              </p>
            )}

            {missingData && (
              <>

                <div>
                  <p className="label">
                    Known information
                  </p>

                  <ListBlock
                    items={missingData.known_information}
                    emptyText="No known information returned."
                  />
                </div>

                <div>
                  <p className="label">
                    Information gaps
                  </p>

                  <ListBlock
                    items={missingData.missing_information}
                    emptyText="No missing information detected."
                  />
                </div>

                {missingData.urgency && (
                  <p>
                    <span className="label">
                      Urgency
                    </span>
                    {' '}
                    <strong>
                      {missingData.urgency}
                    </strong>
                  </p>
                )}

              </>
            )}

            <p className="mono module__endpoint">
              POST /api/ai/missing-info
            </p>

          </div>

        </section>


        {/* ===================================================
            3.4 — SAFETY PRECAUTIONS
        ==================================================== */}

        <section className="panel module">

          <ModuleHeader
            label="GenAI"
            title="Safety precautions"
            status={
              safetyLoading
                ? 'PROCESSING'
                : safetyError
                  ? 'ERROR'
                  : 'CONNECTED'
            }
          />

          <div className="module__body">

            {safetyLoading && (
              <p className="state">
                Generating safety precautions...
              </p>
            )}

            {safetyError && (
              <p
                className="state state--error"
                role="alert"
              >
                Unable to load safety precautions.
                {' '}
                {apiErrorMessage(safetyError)}
              </p>
            )}

            {safetyData && (
              <>

                <div>
                  <p className="label">
                    Precautions
                  </p>

                  <ListBlock
                    items={safetyData.precautions}
                    emptyText="No precautions returned."
                  />
                </div>

                <div>
                  <p className="label">
                    Avoid actions
                  </p>

                  <ListBlock
                    items={safetyData.avoid_actions}
                    emptyText="No avoid-actions returned."
                  />
                </div>

              </>
            )}

            <p className="mono module__endpoint">
              POST /api/ai/safety
            </p>

          </div>

        </section>


        {/* ===================================================
            3.5 — REPORTER GUIDANCE
        ==================================================== */}

        <section className="panel module">

          <ModuleHeader
            label="GenAI"
            title="Reporter guidance"
            status={
              guidanceLoading
                ? 'PROCESSING'
                : guidanceError
                  ? 'ERROR'
                  : 'CONNECTED'
            }
          />

          <div className="module__body">

            {guidanceLoading && (
              <p className="state">
                Generating reporter guidance...
              </p>
            )}

            {guidanceError && (
              <p
                className="state state--error"
                role="alert"
              >
                Unable to load reporter guidance.
                {' '}
                {apiErrorMessage(guidanceError)}
              </p>
            )}

            {guidanceData && (
              <>

                <div>
                  <p className="label">
                    Guidance
                  </p>

                  <ListBlock
                    items={guidanceData.guidance}
                    emptyText="No guidance returned."
                  />
                </div>

                {guidanceData.emergency_contact && (
                  <div>
                    <p className="label">
                      Emergency contact
                    </p>

                    <p>
                      {guidanceData.emergency_contact}
                    </p>
                  </div>
                )}

              </>
            )}

            <p className="mono module__endpoint">
              POST /api/ai/reporter-guidance
            </p>

          </div>

        </section>


        {/* ===================================================
            SEVERITY & PRIORITY
            Reserved for Himesh's ML module
        ==================================================== */}

        <ModulePanel
          title="Severity & priority"
          endpoint="POST /api/assessment"
        >
          Severity, priority score and contributing
          factors are not assessed for this incident yet.
        </ModulePanel>


        {/* ===================================================
            RESOURCE INTELLIGENCE
        ==================================================== */}

        <section className="module-panel">

          <header className="module-panel__head">

            <div>
              <p className="label">
                Resource intelligence
              </p>

              <h2>
                Nearby emergency resources
              </h2>
            </div>

            <span className="module-panel__endpoint mono">
              GET /api/resources/nearby
            </span>

          </header>

          <div className="module-panel__body">

            <ResourceList
              resources={resources}
              loading={resourcesLoading}
              error={resourcesError}
            />

          </div>

        </section>


        {/* ===================================================
            3.6 — RESPONSE INTELLIGENCE
        ==================================================== */}

        <section className="panel module">

          <ModuleHeader
            label="GenAI"
            title="Response intelligence"
            status={
              responseLoading
                ? 'PROCESSING'
                : responseError
                  ? 'ERROR'
                  : 'CONNECTED'
            }
          />

          <div className="module__body">

            {responseLoading && (
              <p className="state">
                Generating response recommendation...
              </p>
            )}

            {responseError && (
              <p
                className="state state--error"
                role="alert"
              >
                Unable to generate response recommendation.
                {' '}
                {apiErrorMessage(responseError)}
              </p>
            )}

            <LanguageToggle
              data={responseData}
              showLocal={showLocalResponse}
              onToggle={() =>
                setShowLocalResponse((v) => !v)
              }
            />

            {responseData && (
              <>

                <div>
                  <p className="label">
                    Situation summary
                  </p>

                  <p>
                    {pickText(responseData, 'situation_summary', showLocalResponse) ||
                      'Not available'}
                  </p>
                </div>

                <div>
                  <p className="label">
                    Recommended response
                  </p>

                  <ListBlock
                    items={pickText(responseData, 'recommended_response', showLocalResponse)}
                    emptyText="No response recommendation returned."
                  />
                </div>

                <div>
                  <p className="label">
                    Resource recommendation
                  </p>

                  <ListBlock
                    items={pickText(responseData, 'resource_recommendation', showLocalResponse)}
                    emptyText="No resource recommendation returned."
                  />
                </div>

                <div>
                  <p className="label">
                    Severity
                  </p>

                  <p>
                    {responseData.severity ||
                      'Not available'}
                  </p>
                </div>

                <div>
                  <p className="label">
                    Priority
                  </p>

                  <p>
                    {responseData.priority ||
                      'Not available'}
                  </p>
                </div>

                <div>
                  <p className="label">
                    Reasoning
                  </p>

                  <p>
                    {pickText(responseData, 'reasoning', showLocalResponse) ||
                      'Not available'}
                  </p>
                </div>

                <div>
                  <p className="label">
                    Information gaps
                  </p>

                  <ListBlock
                    items={pickText(responseData, 'information_gaps', showLocalResponse)}
                    emptyText="No information gaps returned."
                  />
                </div>

              </>
            )}

            <p className="mono module__endpoint">
              POST /api/ai/response
            </p>

          </div>

        </section>


        {/* ===================================================
            3.7 — INCIDENT REPORT
        ==================================================== */}

        <section className="panel module">

          <ModuleHeader
            label="GenAI"
            title="Incident report"
            status={
              reportLoading
                ? 'PROCESSING'
                : reportError
                  ? 'ERROR'
                  : 'CONNECTED'
            }
          />

          <div className="module__body">

            {reportLoading && (
              <p className="state">
                Generating incident report...
              </p>
            )}

            {reportError && (
              <p
                className="state state--error"
                role="alert"
              >
                Unable to generate incident report.
                {' '}
                {apiErrorMessage(reportError)}
              </p>
            )}

            <LanguageToggle
              data={reportData}
              showLocal={showLocalReport}
              onToggle={() =>
                setShowLocalReport((v) => !v)
              }
            />

            {reportData && (
              <>

                <dl className="facts">

                  <Fact label="Incident ID" mono>
                    {reportData.incident_id ||
                      id}
                  </Fact>

                  <Fact label="Emergency type">
                    {reportData.emergency_type ||
                      'Not available'}
                  </Fact>

                  <Fact label="Location">
                    {reportData.location ||
                      'Not available'}
                  </Fact>

                  <Fact
                    label="Affected people"
                    mono
                  >
                    {reportData.affected_people ??
                      'Not available'}
                  </Fact>

                  <Fact
                    label="Injuries"
                    mono
                  >
                    {reportData.injuries ??
                      'Not available'}
                  </Fact>

                  <Fact label="Severity">
                    {reportData.severity ||
                      'Not available'}
                  </Fact>

                  <Fact label="Priority">
                    {reportData.priority ||
                      'Not available'}
                  </Fact>

                </dl>


                <div>
                  <p className="label">
                    Incident summary
                  </p>

                  <p>
                    {pickText(reportData, 'incident_summary', showLocalReport) ||
                      'Not available'}
                  </p>
                </div>


                {Array.isArray(
                  reportData.critical_indicators
                ) &&
                  reportData.critical_indicators.length >
                    0 && (
                    <div>
                      <p className="label">
                        Critical indicators
                      </p>

                      <ListBlock
                        items={
                          reportData.critical_indicators
                        }
                      />
                    </div>
                  )}


                {Array.isArray(
                  reportData.resources
                ) &&
                  reportData.resources.length >
                    0 && (
                    <div>
                      <p className="label">
                        Resources
                      </p>

                      <ul>
                        {reportData.resources.map(
                          (resource, index) => (
                            <li key={index}>
                              {typeof resource ===
                              'string'
                                ? resource
                                : resource?.name ||
                                  resource?.resource_type ||
                                  JSON.stringify(
                                    resource
                                  )}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}


                <div>
                  <p className="label">
                    Response recommendation
                  </p>

                  <ListBlock
                    items={
                      pickText(reportData, 'response_recommendation', showLocalReport)
                    }
                    emptyText="No response recommendation returned."
                  />
                </div>


                <div>
                  <p className="label">
                    Information gaps
                  </p>

                  <ListBlock
                    items={
                      pickText(reportData, 'information_gaps', showLocalReport)
                    }
                    emptyText="No information gaps returned."
                  />
                </div>


                <div>
                  <p className="label">
                    Report summary
                  </p>

                  <p>
                    {pickText(reportData, 'report_summary', showLocalReport) ||
                      'Not available'}
                  </p>
                </div>

              </>
            )}

            <p className="mono module__endpoint">
              POST /api/ai/incident-report
            </p>

          </div>

        </section>


      </div>

    </section>
  )
}