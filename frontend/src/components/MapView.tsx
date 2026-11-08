import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Marker, Polyline, Tooltip, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export type MapMarker = { lat: number; lng: number; kind: string; label: string; unit?: string };
export type MapRoute = { coords: [number, number][]; color?: string; dashed?: boolean };
const UNIT_EMOJI: Record<string, string> = { AMBULANCE: "🚑", FIRE_TENDER: "🚒", RESCUE_TENDER: "🚒", POLICE_PATROL: "🚓",
  HIGHWAY_PATROL: "🚓", DISASTER_TEAM: "🛟", RESCUE_BOAT: "🚤" };
const UNIT_COLOR: Record<string, string> = { HOSPITAL: "#0E8C8F", FIRE: "#E0602A", POLICE: "#2F5DB8", DISASTER: "#7A55C7" };
const unitIcon = (type: string, dept: string) => L.divIcon({
  className: "", iconSize: [38, 38], iconAnchor: [19, 19],
  html: `<div style="width:38px;height:38px;border-radius:12px;background:${UNIT_COLOR[dept] || "#0B1A2E"};border:3px solid #fff;box-shadow:0 6px 16px rgba(11,26,46,.35);display:grid;place-items:center;font-size:20px">${UNIT_EMOJI[type] || "🚨"}</div>`,
});
const COLORS: Record<string, string> = {
  incident: "#C8102E", you: "#C8102E", HOSPITAL: "#0E5F63", AMBULANCE: "#0E5F63", POLICE: "#1F3A93",
  FIRE: "#C2571A", DISASTER: "#6B4E9B", SHELTER: "#6B4E9B",
};

// Map tiles. OpenStreetMap's tile servers need no key but do need the page's Referer
// (the backend sends Referrer-Policy: strict-origin-when-cross-origin for this).
// Set VITE_MAP_TILES=esri in frontend/.env to use Esri's keyless street map instead.
const PROVIDERS = {
  osm: {
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },
  esri: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    attribution: "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors",
  },
};
const TILES = PROVIDERS[(import.meta.env.VITE_MAP_TILES as keyof typeof PROVIDERS) || "osm"] || PROVIDERS.osm;

function Fit({ points, fitKey }: { points: [number, number][]; fitKey?: string }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 1) map.setView(points[0], 15, { animate: false });
    else if (points.length > 1) map.fitBounds(points, { padding: [32, 32], maxZoom: 16, animate: false });
  }, [fitKey ?? JSON.stringify(points)]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}
function Picker({ onPick }: { onPick?: (lat: number, lng: number) => void }) {
  useMapEvents({ click: (e) => onPick?.(e.latlng.lat, e.latlng.lng) });
  return null;
}

export function MapView({ markers, route, routes, onPick, height = 320, center, fitKey }: {
  markers: MapMarker[]; route?: [number, number][]; routes?: MapRoute[]; onPick?: (lat: number, lng: number) => void;
  height?: number; center?: [number, number]; fitKey?: string;
}) {
  const pts = [...markers.map((m) => [m.lat, m.lng] as [number, number]), ...(route || []), ...(routes || []).flatMap((r) => r.coords)];
  return (
    <div style={{ height }} className="overflow-hidden rounded-2xl border border-white shadow-card">
      <MapContainer center={center || pts[0] || [13.0827, 80.2707]} zoom={13} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false} zoomAnimation={false} markerZoomAnimation={false} fadeAnimation={false}>
        <TileLayer attribution={TILES.attribution} url={TILES.url} maxZoom={19}
          referrerPolicy="strict-origin-when-cross-origin" />
        {route && route.length > 1 && <Polyline positions={route} pathOptions={{ color: "#0E5F63", weight: 5, opacity: 0.85 }} />}
        {(routes || []).filter((r) => r.coords.length > 1).map((r, i) => (
          <Polyline key={`r${i}`} positions={r.coords} pathOptions={{ color: r.color || "#0E5F63", weight: 5, opacity: 0.8, dashArray: r.dashed ? "8 10" : undefined }} />
        ))}
        {markers.map((m, i) => m.unit ? (
          <Marker key={`u${m.label}`} position={[m.lat, m.lng]} icon={unitIcon(m.unit, m.kind)} zIndexOffset={1000}>
            <Tooltip direction="top" offset={[0, -18]}>{m.label}</Tooltip>
          </Marker>
        ) : (
          <CircleMarker key={i} center={[m.lat, m.lng]} radius={m.kind === "incident" || m.kind === "you" ? 10 : 7}
            pathOptions={{ color: "#fff", weight: 2, fillColor: COLORS[m.kind] || "#0B1A2E", fillOpacity: 1 }}>
            <Tooltip>{m.label}</Tooltip>
          </CircleMarker>
        ))}
        <Fit points={pts} fitKey={fitKey} />
        <Picker onPick={onPick} />
      </MapContainer>
    </div>
  );
}
