import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { AlertTriangle, Loader2, LocateFixed, Navigation, Radio } from "lucide-react";
import { MapView, type MapMarker } from "../components/MapView";
import { UNIT_EMOJI } from "../components/DispatchPanel";
import { DEPT_LABEL } from "../lib/format";

const API = "/api/v1";
const ACTIONS: Record<string, { s: string; label: string; ambulanceOnly?: boolean; notAmbulance?: boolean }[]> = {
  ASSIGNED: [{ s: "EN_ROUTE", label: "Start: we are on the way" }],
  EN_ROUTE: [{ s: "ON_SCENE", label: "We have arrived on scene" }],
  ON_SCENE: [{ s: "TRANSPORTING", label: "Patient on board: going to hospital", ambulanceOnly: true },
             { s: "COMPLETED", label: "Job complete" }],
  TRANSPORTING: [{ s: "AT_HOSPITAL", label: "Arrived at hospital" }],
  AT_HOSPITAL: [{ s: "COMPLETED", label: "Patient handed over: job complete" }],
};
const STATUS_TEXT: Record<string, string> = { ASSIGNED: "New assignment", EN_ROUTE: "On the way", ON_SCENE: "On scene",
  TRANSPORTING: "Transporting patient", AT_HOSPITAL: "At hospital" };

/** Crew phone page: opened from a private link the control room generates for one unit. */
export default function Crew() {
  const { unitId = "" } = useParams();
  const [params] = useSearchParams();
  const key = `resq.crew.${unitId}`;
  const [token] = useState<string>(() => {
    const t = params.get("t");
    try { if (t) localStorage.setItem(key, t); return t || localStorage.getItem(key) || ""; } catch { return t || ""; }
  });
  const [v, setV] = useState<any>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState("");
  const [sharing, setSharing] = useState(false);
  const watch = useRef<number | null>(null);
  const last = useRef(0);

  const call = useCallback(async (path: string, body?: unknown) => {
    const r = await fetch(API + path, { method: body ? "POST" : "GET", headers: { "X-Crew-Token": token, ...(body ? { "Content-Type": "application/json" } : {}) },
      body: body ? JSON.stringify(body) : undefined });
    const d = await r.json().catch(() => null);
    if (!r.ok) throw new Error(d?.detail?.message || `HTTP ${r.status}`);
    return d;
  }, [token]);
  const load = useCallback(() => { call(`/crew/${unitId}`).then((d) => { setV(d); setErr(""); }).catch((e) => setErr(e.message)); }, [call, unitId]);
  useEffect(() => { load(); const t = setInterval(load, 4000); return () => clearInterval(t); }, [load]);

  useEffect(() => {
    if (!sharing || !navigator.geolocation) return;
    watch.current = navigator.geolocation.watchPosition((p) => {
      if (Date.now() - last.current < 5000) return;
      last.current = Date.now();
      call(`/crew/${unitId}/location`, { latitude: p.coords.latitude, longitude: p.coords.longitude, accuracy_m: p.coords.accuracy }).catch(() => undefined);
    }, () => setSharing(false), { enableHighAccuracy: true, maximumAge: 5000 });
    return () => { if (watch.current != null) navigator.geolocation.clearWatch(watch.current); };
  }, [sharing, call, unitId]);

  async function act(s: string) {
    setBusy(s);
    try { await call(`/crew/${unitId}/status`, { status: s }); load(); } catch (e) { setErr((e as Error).message); } finally { setBusy(""); }
  }

  if (!token) return <Shell><p className="p-6 text-center">Open this page from the crew link your control room sent.</p></Shell>;
  if (err && !v) return <Shell><div className="m-4 flex gap-2 rounded-2xl bg-sos/20 p-4"><AlertTriangle className="h-5 w-5 shrink-0" />{err}</div></Shell>;
  if (!v) return <Shell><p className="flex items-center justify-center gap-2 p-10"><Loader2 className="h-5 w-5 animate-spin" />Loading…</p></Shell>;

  const u = v.unit, job = v.job;
  const d = job?.dispatch, inc = job?.incident;
  const markers: MapMarker[] = [];
  if (inc?.location?.latitude != null) markers.push({ lat: inc.location.latitude, lng: inc.location.longitude, kind: "incident", label: inc.type });
  if (d?.live?.latitude != null) markers.push({ lat: d.live.latitude, lng: d.live.longitude, kind: u.department, unit: u.unit_type, label: u.call_sign });
  if (job?.destination && d?.status !== "ASSIGNED") markers.push({ lat: job.destination.latitude, lng: job.destination.longitude, kind: "HOSPITAL", label: job.destination.name });
  const target = d && ["TRANSPORTING", "AT_HOSPITAL"].includes(d.status) && job.destination ? job.destination : inc?.location;
  const nav = target ? `https://www.google.com/maps/dir/?api=1&destination=${target.latitude},${target.longitude}&travelmode=driving` : null;

  return (
    <Shell>
      <header className="flex items-center gap-3 px-4 py-4">
        <span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/10 text-2xl">{UNIT_EMOJI[u.unit_type] || "🚨"}</span>
        <div className="min-w-0">
          <p className="text-lg font-black">{u.call_sign}</p>
          <p className="text-sm text-white/70">{v.unit_label} · {DEPT_LABEL[u.department]}</p>
        </div>
        <button onClick={() => setSharing((x) => !x)} className={`ml-auto flex items-center gap-1.5 rounded-full px-3 py-2 text-xs font-bold ${sharing ? "bg-pri-low text-white" : "bg-white/10"}`}>
          <LocateFixed className="h-4 w-4" />{sharing ? "Sharing GPS" : "Share GPS"}</button>
      </header>

      {!job ? (
        <div className="mx-4 rounded-3xl bg-white/10 p-8 text-center">
          <Radio className="mx-auto h-10 w-10 animate-blink text-teal-glow" />
          <p className="mt-3 text-xl font-black">Available</p>
          <p className="mt-1 text-white/70">No active assignment. This page alerts you when the control room dispatches this unit.</p>
        </div>
      ) : (
        <div className="space-y-4 px-4 pb-10">
          <div className={`rounded-3xl p-5 ${d.status === "ASSIGNED" ? "bg-gradient-to-br from-[#FF4A64] to-[#C8102E] shadow-glowred" : "bg-white/10"}`}>
            <p className="text-xs font-bold uppercase tracking-wide text-white/80">{STATUS_TEXT[d.status]}{d.auto ? " · auto-dispatched" : ""}</p>
            <h1 className="mt-1 text-2xl font-black">{inc.type}</h1>
            <p className="mt-1 text-white/85">{inc.summary?.replace(" [Auto-summary from extracted facts, not a translation]", "")}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs font-bold">
              <span className="rounded-full bg-black/25 px-2.5 py-1">Priority {inc.priority_score} · {inc.severity?.toLowerCase()}</span>
              {inc.injuries > 0 && <span className="rounded-full bg-black/25 px-2.5 py-1">{inc.injuries} injured</span>}
              {inc.trapped && <span className="rounded-full bg-black/25 px-2.5 py-1">people trapped</span>}
              {(inc.hazards || []).map((h: string) => <span key={h} className="rounded-full bg-black/25 px-2.5 py-1">{h.replace("_", " ")}</span>)}
              {inc.sensor && <span className="rounded-full bg-black/25 px-2.5 py-1">sensor: {inc.sensor.reason?.replace(" (console demo trigger)", "")}</span>}
            </div>
          </div>

          <div className="overflow-hidden rounded-3xl bg-white text-ink">
            <MapView height={260} markers={markers} routes={d.route ? [{ coords: d.route, dashed: d.eta_source !== "ROAD_ROUTE" }] : []} fitKey={`${d.id}:${d.status}`} />
            <div className="flex items-center gap-3 p-4">
              <div className="min-w-0 flex-1">
                <p className="font-bold">{target === inc.location ? inc.location?.label : job.destination?.name}</p>
                {d.live?.eta_remaining_min != null && <p className="text-sm text-muted">About {d.live.eta_remaining_min} min · {d.distance_km} km</p>}
              </div>
              {nav && <a href={nav} target="_blank" rel="noreferrer" className="btn-primary px-4 py-2.5"><Navigation className="h-4 w-4" />Navigate</a>}
            </div>
          </div>

          <div className="space-y-2">
            {(ACTIONS[d.status] || []).filter((a) => !a.ambulanceOnly || u.unit_type === "AMBULANCE").map((a) => (
              <button key={a.s} onClick={() => act(a.s)} disabled={!!busy}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-white py-4 text-lg font-black text-navy shadow-lift active:scale-[.99] disabled:opacity-60">
                {busy === a.s && <Loader2 className="h-5 w-5 animate-spin" />}{a.label}</button>
            ))}
          </div>
          {err && <p className="rounded-xl bg-sos/25 p-3 text-sm">{err}</p>}

          {inc.other_units?.length > 0 && (
            <div className="rounded-3xl bg-white/10 p-4">
              <p className="text-sm font-bold">Also responding</p>
              <ul className="mt-2 space-y-1.5 text-sm">
                {inc.other_units.map((o: any) => <li key={o.id}>{UNIT_EMOJI[o.unit.unit_type]} {o.unit.call_sign} · {o.status.replace("_", " ").toLowerCase()}{o.live?.eta_remaining_min != null ? `, ${o.live.eta_remaining_min} min` : ""}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return <div lang="en" className="dark-band min-h-screen text-white"><div className="mx-auto max-w-md">{children}</div></div>;
}
