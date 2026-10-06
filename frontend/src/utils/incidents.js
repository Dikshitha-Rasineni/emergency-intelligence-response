/* Severity semantics: colour + glyph + text, never colour alone. */
export const SEVERITY = {
  CRITICAL: { rank: 4, label: 'CRITICAL', glyph: '◆', cls: 'critical' },
  HIGH: { rank: 3, label: 'HIGH', glyph: '▲', cls: 'high' },
  MODERATE: { rank: 2, label: 'MODERATE', glyph: '●', cls: 'moderate' },
  LOW: { rank: 1, label: 'LOW', glyph: '○', cls: 'low' },
}

const pick = (o, ...keys) => keys.map((k) => o?.[k]).find((v) => v !== undefined && v !== null)

export function normalizeSeverity(value) {
  const v = String(value ?? '').toUpperCase()
  if (v === 'MEDIUM') return 'MODERATE'
  return SEVERITY[v] ? v : 'LOW'
}

/* Tolerant of field-name variants until the backend schema is final. */
export function normalizeIncident(raw) {
  const lat = Number(pick(raw, 'latitude', 'lat'))
  const lon = Number(pick(raw, 'longitude', 'lon', 'lng'))
  return {
    id: String(pick(raw, 'id', 'incident_id') ?? ''),
    type: String(pick(raw, 'emergency_type', 'type', 'category') ?? 'UNCLASSIFIED').toUpperCase(),
    severity: normalizeSeverity(pick(raw, 'severity')),
    priority: Number(pick(raw, 'priority_score', 'priority') ?? 0),
    affected: Number(pick(raw, 'affected_people', 'affected') ?? 0),
    injuries: Number(pick(raw, 'injuries', 'injured') ?? 0),
    location: pick(raw, 'location', 'location_text', 'address') ?? '—',
    description: pick(raw, 'description', 'text', 'summary') ?? '',
    status: String(pick(raw, 'status') ?? 'ACTIVE').toUpperCase(),
    time: pick(raw, 'created_at', 'timestamp', 'time'),
    // Fields the backend has not provided yet are flagged, never invented.
    severityKnown: pick(raw, 'severity') !== undefined,
    priorityKnown: pick(raw, 'priority_score', 'priority') !== undefined,
    typeKnown: pick(raw, 'emergency_type', 'type', 'category') !== undefined,
    lat: Number.isFinite(lat) ? lat : null,
    lon: Number.isFinite(lon) ? lon : null,
  }
}

export function normalizeIncidentList(data) {
  const list = Array.isArray(data) ? data : data?.incidents ?? data?.items ?? []
  return list.map(normalizeIncident)
}

/* Critical first, then by priority score. */
export const byUrgency = (a, b) =>
  SEVERITY[b.severity].rank - SEVERITY[a.severity].rank || b.priority - a.priority

export const isOpen = (i) => !['CLOSED', 'RESOLVED', 'CANCELLED'].includes(i.status)

export function formatTime(value, withSeconds = false) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', ...(withSeconds && { second: '2-digit' }), hour12: false })
}

export const formatCoord = (n) => (n === null ? '—' : n.toFixed(5))
export const shortId = (id) => (id.startsWith('INC-') ? id : `INC-${id.slice(0, 8).toUpperCase()}`)

export function formatDateTime(value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString([], { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

export function minutesAgo(value) {
  const t = new Date(value).getTime()
  return Number.isNaN(t) ? null : Math.max(0, Math.floor((Date.now() - t) / 60000))
}

export function relativeTime(value) {
  const m = minutesAgo(value)
  if (m === null) return ''
  if (m < 1) return 'just now'
  if (m < 60) return `${m} min ago`
  if (m < 1440) return `${Math.floor(m / 60)} h ago`
  return `${Math.floor(m / 1440)} d ago`
}