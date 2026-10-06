import { useEffect, useMemo } from 'react'
import {
  CircleMarker,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
  useMapEvents,
} from 'react-leaflet'
import L from 'leaflet'

import { SEVERITY, shortId } from '../../utils/incidents'

const RESOURCE_LABELS = {
  hospital: 'Hospital',
  ambulance: 'Ambulance',
  fire_station: 'Fire Station',
  police_station: 'Police Station',
  shelter: 'Shelter',
}

const RESOURCE_COLORS = {
  hospital: '#ef4444',
  ambulance: '#f97316',
  fire_station: '#eab308',
  police_station: '#3b82f6',
  shelter: '#22c55e',
}

const RESOURCE_GLYPHS = {
  hospital: 'H',
  ambulance: 'A',
  fire_station: 'F',
  police_station: 'P',
  shelter: 'S',
}

/*
 * Creates a custom resource marker.
 * Using divIcon avoids relying on Leaflet's
 * default marker image paths.
 */
function createResourceIcon(type) {
  const color =
    RESOURCE_COLORS[type] || '#06b6d4'

  const glyph =
    RESOURCE_GLYPHS[type] || 'R'

  return L.divIcon({
    className: 'resource-map-icon',
    html: `
      <div
        style="
          width: 34px;
          height: 34px;
          border-radius: 50%;
          background: ${color};
          border: 3px solid #ffffff;
          box-shadow:
            0 2px 8px rgba(0,0,0,0.45),
            0 0 0 3px rgba(255,255,255,0.15);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #061817;
          font-size: 15px;
          font-weight: 900;
          font-family: Arial, sans-serif;
        "
      >
        ${glyph}
      </div>
    `,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
    tooltipAnchor: [0, -18],
  })
}

/*
 * Handles clicks on the map.
 *
 * Used by EmergencyReport to allow the user
 * to select the incident location directly
 * from the real map.
 */
function MapClickHandler({
  onLocationSelect,
}) {
  useMapEvents({
    click(event) {
      if (!onLocationSelect) {
        return
      }

      onLocationSelect({
        latitude: event.latlng.lat,
        longitude: event.latlng.lng,
      })
    },
  })

  return null
}

/*
 * Automatically fits the map around all
 * incidents and nearby resources.
 */
function FitMapToData({
  incidents,
  resources,
}) {
  const map = useMap()

  useEffect(() => {
    const points = [
      ...incidents
        .filter(
          (incident) =>
            incident.lat != null &&
            incident.lon != null
        )
        .map((incident) => [
          Number(incident.lat),
          Number(incident.lon),
        ])
        .filter(
          ([lat, lon]) =>
            Number.isFinite(lat) &&
            Number.isFinite(lon)
        ),

      ...resources
        .filter(
          (resource) =>
            resource.latitude != null &&
            resource.longitude != null
        )
        .map((resource) => [
          Number(resource.latitude),
          Number(resource.longitude),
        ])
        .filter(
          ([lat, lon]) =>
            Number.isFinite(lat) &&
            Number.isFinite(lon)
        ),
    ]

    if (!points.length) {
      return
    }

    if (points.length === 1) {
      map.setView(points[0], 15)
      return
    }

    map.fitBounds(points, {
      padding: [50, 50],
      maxZoom: 16,
    })

    setTimeout(() => {
      map.invalidateSize()
    }, 100)
  }, [map, incidents, resources])

  return null
}

export default function EmergencyMap({
  incidents = [],
  selectedId,
  onSelect,
  resources = [],
  onLocationSelect,
}) {
  /*
   * Normalize incident coordinates.
   */
  const locatedIncidents = useMemo(
    () =>
      incidents
        .filter(
          (incident) =>
            incident.lat != null &&
            incident.lon != null
        )
        .map((incident) => ({
          ...incident,
          lat: Number(incident.lat),
          lon: Number(incident.lon),
        }))
        .filter(
          (incident) =>
            Number.isFinite(incident.lat) &&
            Number.isFinite(incident.lon)
        ),
    [incidents]
  )

  /*
   * Normalize resource coordinates.
   */
  const locatedResources = useMemo(
    () =>
      resources
        .filter(
          (resource) =>
            resource.latitude != null &&
            resource.longitude != null
        )
        .map((resource) => ({
          ...resource,
          latitude: Number(resource.latitude),
          longitude: Number(resource.longitude),
        }))
        .filter(
          (resource) =>
            Number.isFinite(
              resource.latitude
            ) &&
            Number.isFinite(
              resource.longitude
            )
        ),
    [resources]
  )

  /*
   * Default Bangalore coordinates are only
   * used when there is no incident coordinate.
   */
  const defaultCenter =
    locatedIncidents.length > 0
      ? [
          locatedIncidents[0].lat,
          locatedIncidents[0].lon,
        ]
      : [12.9716, 77.5946]

  return (
    <div
      className="map"
      role="group"
      aria-label={`Incident map, ${locatedIncidents.length} located incidents and ${locatedResources.length} nearby resources`}
    >
      <MapContainer
        center={defaultCenter}
        zoom={15}
        scrollWheelZoom
        className="map__leaflet"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Map click → incident location */}
        <MapClickHandler
          onLocationSelect={
            onLocationSelect
          }
        />

        {/* Automatically fit incident + resources */}
        <FitMapToData
          incidents={locatedIncidents}
          resources={locatedResources}
        />

        {/* ==================================================
            INCIDENT MARKERS
        ================================================== */}

        {locatedIncidents.map((incident) => {
          const selected =
            incident.id === selectedId

          const severity =
            SEVERITY[incident.severity] ||
            SEVERITY.MODERATE

          const severityColor =
            severity.cls === 'critical'
              ? '#ef4444'
              : severity.cls === 'high'
                ? '#f97316'
                : severity.cls ===
                    'moderate'
                  ? '#eab308'
                  : '#22c55e'

          return (
            <CircleMarker
              key={`incident-${incident.id}`}
              center={[
                incident.lat,
                incident.lon,
              ]}
              radius={
                selected ? 13 : 10
              }
              pathOptions={{
                color: '#ffffff',
                weight: selected ? 4 : 3,
                fillColor:
                  severityColor,
                fillOpacity: 1,
              }}
              eventHandlers={{
                click: () =>
                  onSelect?.(
                    incident.id
                  ),
              }}
            >
              <Tooltip
                direction="top"
                offset={[0, -10]}
              >
                {shortId(incident.id)}
              </Tooltip>

              <Popup>
                <strong>
                  {shortId(incident.id)}
                </strong>

                <br />

                {incident.type ||
                  'Emergency'}

                <br />

                Severity:{' '}
                {incident.severity}

                <br />

                Affected:{' '}
                {incident.affected ??
                  0}

                <br />

                Injuries:{' '}
                {incident.injuries ??
                  0}

                <br />

                Coordinates:{' '}
                {incident.lat.toFixed(
                  4
                )}
                ,{' '}
                {incident.lon.toFixed(
                  4
                )}
              </Popup>
            </CircleMarker>
          )
        })}

        {/* ==================================================
            RESOURCE MARKERS
        ================================================== */}

        {locatedResources.map(
          (resource) => {
            const type =
              resource.resource_type

            const label =
              RESOURCE_LABELS[type] ||
              'Resource'

            const icon =
              createResourceIcon(
                type
              )

            return (
              <Marker
                key={`resource-${resource.id}`}
                position={[
                  resource.latitude,
                  resource.longitude,
                ]}
                icon={icon}
              >
                <Tooltip
                  direction="top"
                  offset={[0, -18]}
                >
                  <strong>
                    {resource.name}
                  </strong>

                  <br />

                  {label} ·{' '}
                  {Number(
                    resource.distance_km
                  ).toFixed(2)}{' '}
                  km
                </Tooltip>

                <Popup>
                  <div
                    style={{
                      minWidth:
                        '190px',
                    }}
                  >
                    <strong>
                      {resource.name}
                    </strong>

                    <br />

                    <span>
                      Type: {label}
                    </span>

                    <br />

                    <span>
                      Distance:{' '}
                      {Number(
                        resource.distance_km
                      ).toFixed(2)}{' '}
                      km
                    </span>

                    <br />

                    <span>
                      Status:{' '}
                      {
                        resource.availability_status
                      }
                    </span>

                    <br />

                    <span>
                      Available units:{' '}
                      {
                        resource.available_units
                      }
                    </span>

                    <br />

                    <span>
                      Wait time:{' '}
                      {
                        resource.wait_time_minutes
                      }{' '}
                      min
                    </span>

                    {resource.address && (
                      <>
                        <br />

                        <span>
                          {
                            resource.address
                          }
                        </span>
                      </>
                    )}

                    {resource.contact_number && (
                      <>
                        <br />

                        <span>
                          Contact:{' '}
                          {
                            resource.contact_number
                          }
                        </span>
                      </>
                    )}
                  </div>
                </Popup>
              </Marker>
            )
          }
        )}
      </MapContainer>

      {!locatedIncidents.length &&
        !onLocationSelect && (
          <p className="map__empty">
            No incidents with
            coordinates to plot.
          </p>
        )}

      {/* ==================================================
          MAP LEGEND
      ================================================== */}

      <div className="map__legend">
        {Object.values(SEVERITY)
          .sort(
            (a, b) =>
              b.rank - a.rank
          )
          .map((severity) => (
            <span
              key={severity.label}
              className={`sev sev--${severity.cls}`}
            >
              <span className="sev__glyph">
                {severity.glyph}
              </span>

              {severity.label}
            </span>
          ))}

        <span className="map__layer">
          Resource layers:{' '}
          {locatedResources.length
            ? `${locatedResources.length} nearby resources`
            : 'none found'}
        </span>

        {onLocationSelect && (
          <span className="map__layer">
            Click map to select location
          </span>
        )}
      </div>
    </div>
  )
}