import { useCallback, useEffect, useState } from "react";
import { Check, Copy, Link2, Loader2, Navigation, Send, X, Zap } from "lucide-react";
import { api } from "../lib/api";
import { DEPT_LABEL, clock } from "../lib/format";

export const UNIT_EMOJI: Record<string, string> = { AMBULANCE: "🚑", FIRE_TENDER: "🚒", RESCUE_TENDER: "🚒", POLICE_PATROL: "🚓",
  HIGHWAY_PATROL: "🚓", DISASTER_TEAM: "🛟", RESCUE_BOAT: "🚤" };
const STATUS: Record<string, { label: string; tone: string }> = {
  ASSIGNED: { label: "Assigned", tone: "bg-sun/25 text-[#8A6100]" },
  EN_ROUTE: { label: "En route", tone: "bg-teal-mid/15 text-teal" },
  ON_SCENE: { label: "On scene", tone: "bg-pri-low/15 text-pri-low" },
  TRANSPORTING: { label: "Transporting patient", tone: "bg-[#2F5DB8]/15 text-[#2F5DB8]" },
  AT_HOSPITAL: { label: "At hospital", tone: "bg-[#2F5DB8]/15 text-[#2F5DB8]" },
  COMPLETED: { label: "Completed", tone: "bg-paper text-muted" },
};
const NEXT: Record<string, [string, string][]> = {
  ASSIGNED: [["EN_ROUTE", "Mark en route"], ["ON_SCENE", "Mark on scene"]],
  EN_ROUTE: [["ON_SCENE", "Mark on scene"]],
  ON_SCENE: [["TRANSPORTING", "Transporting patient"], ["COMPLETED", "Complete"]],
  TRANSPORTING: [["AT_HOSPITAL", "Arrived at hospital"]],
  AT_HOSPITAL: [["COMPLETED", "Complete"]],
};
const etaText = (d: any) => d.eta_source === "ROAD_ROUTE" ? "road route" : "straight-line estimate";

/** Units on this incident (all services, for coordination) + "send a unit" for your own service. */
export function DispatchPanel({ v, dept, onChanged }: { v: any; dept: string; onChanged: () => void }) {
  const isAdmin = dept === "ADMIN";
  const [asDept, setAsDept] = useState<string>(isAdmin ? (v.dispatched_to?.[0]?.department || "HOSPITAL") : dept);
  const [cands, setCands] = useState<any[] | null>(null);
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");
  const [link, setLink] = useState<{ unit: string; url: string; copied?: boolean } | null>(null);
  const ds: any[] = v.dispatches || [];
  const mine = (d: any) => isAdmin || d.department === dept;
  const routedTo = (v.dispatched_to || []).map((x: any) => x.department);

  const loadCands = useCallback(() => {
    if (!routedTo.includes(asDept)) { setCands([]); return; }
    api<any[]>(`/control-room/incidents/${v.incident_id}/units${isAdmin ? `?as_department=${asDept}` : ""}`)
      .then(setCands).catch(() => setCands([]));
  }, [v.incident_id, asDept, isAdmin, routedTo.join()]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { setCands(null); loadCands(); }, [loadCands, ds.length]);

  async function run(key: string, fn: () => Promise<unknown>) {
    setBusy(key); setErr("");
    try { await fn(); onChanged(); loadCands(); } catch (e) { setErr((e as Error).message); } finally { setBusy(""); }
  }
  const send = (unitId: string) => run(unitId, () => api(`/control-room/incidents/${v.incident_id}/dispatch`, { method: "POST", json: { unit_id: unitId } }));
  const move = (d: any, status: string) => run(d.id + status, () => api(`/control-room/dispatches/${d.id}/status`, { method: "POST", json: { status } }));
  async function crew(unitId: string) {
    setBusy("link" + unitId);
    try {
      const r = await api<{ path: string }>(`/control-room/units/${unitId}/crew-link`, { method: "POST" });
      setLink({ unit: unitId, url: `${window.location.origin}${r.path}` });
    } catch (e) { setErr((e as Error).message); } finally { setBusy(""); }
  }
  const activeHere = new Set(ds.filter((d) => !["COMPLETED", "CANCELLED"].includes(d.status)).map((d) => d.department));

  return (
    <section className="mt-6">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-sm font-bold">Units responding</h2>
        <span className="text-xs text-muted">{ds.length ? `${ds.length} unit(s) across ${new Set(ds.map((d) => d.department)).size} service(s)` : "No units assigned yet"}</span>
      </div>
      {err && <p className="mt-2 rounded-xl bg-sos/10 px-3 py-2 text-sm font-semibold text-sos" role="alert">{err}</p>}

      <ul className="mt-2 grid gap-3 lg:grid-cols-2">
        {ds.map((d) => {
          const st = STATUS[d.status] || STATUS.ASSIGNED;
          const live = d.live || {};
          return (
            <li key={d.id} className={`panel relative overflow-hidden p-4 ${d.status === "EN_ROUTE" ? "ring-2 ring-teal-mid/40" : ""}`}>
              <div className="flex items-start gap-3">
                <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-paper text-2xl">{UNIT_EMOJI[d.unit.unit_type] || "🚨"}</span>
                <div className="min-w-0 flex-1">
                  <p className="font-black">{d.unit.call_sign} <span className="text-xs font-semibold text-muted">· {DEPT_LABEL[d.department]}</span></p>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs">
                    <span className={`rounded-full px-2 py-0.5 font-bold ${st.tone}`}>{st.label}</span>
                    {d.auto && <span className="flex items-center gap-1 rounded-full bg-navy px-2 py-0.5 font-bold text-white"><Zap className="h-3 w-3" />Auto-dispatched</span>}
                    {live.position_source === "CREW_GPS" && <span className="rounded-full bg-pri-low/15 px-2 py-0.5 font-bold text-pri-low">Live crew GPS</span>}
                    {live.position_source === "SIMULATED" && <span className="rounded-full bg-paper px-2 py-0.5 text-muted">simulated position ({live.simulation_speed}× speed)</span>}
                  </div>
                </div>
                {live.eta_remaining_min != null && (
                  <span className="shrink-0 rounded-xl bg-navy px-3 py-1.5 text-center text-white">
                    <span className="block text-xl font-black leading-none">{live.eta_remaining_min}</span><span className="text-[10px] text-white/70">min</span>
                  </span>
                )}
              </div>
              {["ASSIGNED", "EN_ROUTE"].includes(d.status) && (
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-line"><div className="h-full rounded-full bg-gradient-to-r from-teal-mid to-teal-glow transition-all duration-1000" style={{ width: `${Math.max(3, (live.progress || 0) * 100)}%` }} /></div>
              )}
              <p className="mt-2 text-xs text-muted">
                {d.distance_km} km, {Math.round(d.eta_min)} min ({etaText(d)}) · assigned {clock(d.assigned_at)} by {d.auto ? "rules" : "control room"}
                {d.on_scene_at && <> · on scene {clock(d.on_scene_at)}</>}
              </p>
              {d.destination && d.unit.unit_type === "AMBULANCE" && (
                <p className="mt-1 flex items-center gap-1.5 text-xs font-semibold text-teal"><Navigation className="h-3.5 w-3.5" />Receiving hospital: {d.destination.name}</p>
              )}
              {mine(d) && (NEXT[d.status] || []).length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {NEXT[d.status].map(([s, label]) => (
                    <button key={s} className="btn-quiet px-3 py-1.5 text-sm" disabled={!!busy} onClick={() => move(d, s)}>
                      {busy === d.id + s ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}{label}</button>
                  ))}
                  {["ASSIGNED", "EN_ROUTE"].includes(d.status) && (
                    <button className="btn-text text-sm text-sos" disabled={!!busy} onClick={() => move(d, "CANCELLED")}><X className="h-4 w-4" />Cancel</button>
                  )}
                  <button className="btn-text text-sm" disabled={!!busy} onClick={() => crew(d.unit.id)}><Link2 className="h-4 w-4" />Crew phone link</button>
                </div>
              )}
              {link && link.unit === d.unit.id && (
                <div className="mt-2 rounded-xl bg-paper p-2 text-xs">
                  <p className="font-semibold">Open this on the crew's phone (works once per new link):</p>
                  <div className="mt-1 flex items-center gap-2">
                    <code className="min-w-0 flex-1 truncate">{link.url}</code>
                    <button className="btn-text text-xs" onClick={() => { navigator.clipboard?.writeText(link.url); setLink({ unit: link.unit, url: link.url, copied: true }); }}>
                      {link.copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}{link.copied ? "Copied" : "Copy"}</button>
                    <a className="btn-text text-xs" href={link.url} target="_blank" rel="noreferrer">Open</a>
                  </div>
                </div>
              )}
            </li>
          );
        })}
      </ul>

      {/* Send a unit */}
      <div className="panel mt-3 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-bold">Send a unit</h3>
          {isAdmin && (
            <div className="flex flex-wrap gap-1">
              {routedTo.map((dpt: string) => (
                <button key={dpt} onClick={() => setAsDept(dpt)} className={`rounded-full px-2.5 py-1 text-xs font-bold ${asDept === dpt ? "bg-navy text-white" : "bg-paper text-muted"}`}>{DEPT_LABEL[dpt]}</button>
              ))}
            </div>
          )}
          {activeHere.has(asDept) && <span className="text-xs text-muted">A {DEPT_LABEL[asDept]} unit is already assigned; you can send another.</span>}
        </div>
        {cands === null ? <p className="mt-2 flex items-center gap-2 text-sm text-muted"><Loader2 className="h-4 w-4 animate-spin" />Finding the nearest units…</p>
          : cands.length === 0 ? <p className="mt-2 text-sm text-muted">No available {DEPT_LABEL[asDept] || ""} units nearby.</p> : (
          <ul className="mt-2 divide-y divide-line">
            {cands.map((c) => (
              <li key={c.id} className="flex flex-wrap items-center gap-3 py-2.5">
                <span className="text-xl">{UNIT_EMOJI[c.unit_type] || "🚨"}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold">{c.call_sign} <span className="font-normal text-muted">{c.unit_label}</span>
                    {c.preferred_type && <span className="ml-1.5 rounded bg-teal-soft px-1.5 py-0.5 text-[11px] font-bold text-teal">best fit</span>}</p>
                  <p className="text-xs text-muted">{c.distance_km} km · about {Math.round(c.eta_min)} min ({etaText(c)}){c.base_name ? ` · from ${c.base_name}` : ""}{c.base_source === "OSM" ? " (OpenStreetMap)" : ""}{c.demo ? " · demo unit" : ""}</p>
                </div>
                <button className="btn-primary px-3 py-1.5 text-sm" disabled={!!busy} onClick={() => send(c.id)}>
                  {busy === c.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}Dispatch</button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
