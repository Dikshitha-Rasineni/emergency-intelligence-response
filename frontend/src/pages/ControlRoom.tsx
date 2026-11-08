import { useCallback, useEffect, useRef, useState } from "react";
import { Link, Navigate, useParams, useNavigate } from "react-router-dom";
import { AlertTriangle, Check, CircleDot, Cpu, ImageOff, Loader2, LogOut, Radio, Users } from "lucide-react";
import { api, wsUrl, ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Brand } from "../components/Brand";
import { SeverityTag } from "../components/PriorityMeter";
import { MapView, type MapMarker } from "../components/MapView";
import { Empty, ErrorBox, Loading } from "../components/States";
import { SensorBanner, SensorConsole } from "../components/SensorPanels";
import { DispatchPanel } from "../components/DispatchPanel";
import { GenAIBrief, AskResq } from "../components/GenAIPanel";
import { Component, type ReactNode } from "react";

const LANG_NAME: Record<string, string> = { te: "Telugu", ta: "Tamil", hi: "Hindi", en: "English", kn: "Kannada", ml: "Malayalam" };

class DetailBoundary extends Component<{ children: ReactNode; id: string }, { error: string | null }> {
  state = { error: null as string | null };
  static getDerivedStateFromError(e: Error) { return { error: e.message }; }
  componentDidUpdate(prev: { id: string }) { if (prev.id !== this.props.id && this.state.error) this.setState({ error: null }); }
  render() {
    return this.state.error ? (
      <div className="p-6"><ErrorBox onRetry={() => this.setState({ error: null })}>This incident could not be displayed ({this.state.error}). Try again, or open it from the queue.</ErrorBox></div>
    ) : this.props.children;
  }
}
import { CATEGORY_LABEL, DEPT_LABEL, clock, timeAgo } from "../lib/format";

const STATUS_FLOW = ["ACKNOWLEDGED", "RESPONDING", "ON_SCENE", "RESOLVED", "FALSE_ALARM"];
const STATUS_LABEL: Record<string, string> = { REPORTED: "New", ACKNOWLEDGED: "Acknowledged", RESPONDING: "Responding", ON_SCENE: "On scene",
  RESOLVED: "Resolved", CLOSED: "Closed", FALSE_ALARM: "False alarm" };
const NOTIF_STYLE: Record<string, string> = { PENDING: "text-pri-high", SENT: "text-pri-high", DELIVERED: "text-pri-high",
  ESCALATED: "text-pri-critical font-bold", ACKNOWLEDGED: "text-pri-low", CANCELLED: "text-muted" };

function Header({ live }: { live: "connecting" | "live" | "offline" }) {
  const { user, logout } = useAuth();
  return (
    <header className="dark-band border-b border-white/10 text-white">
      <div className="flex flex-wrap items-center gap-4 px-4 py-3">
        <Brand dark to="/ops" sub={user?.organization_name || DEPT_LABEL[user?.role || ""]} />
        <span className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold ${live === "live" ? "bg-pri-low/25 text-[#9CF5D0]" : "bg-white/10 text-white/70"}`}>
          <span className={`h-2 w-2 rounded-full ${live === "live" ? "animate-blink bg-[#9CF5D0]" : "bg-white/50"}`} /><Radio className="h-3.5 w-3.5" />{live === "live" ? "Live updates connected" : live === "connecting" ? "Connecting…" : "Live updates offline, refreshing every 20 s"}
        </span>
        <div className="ml-auto flex items-center gap-3 text-sm">
          <Link to="/ops" className="flex items-center gap-1.5 font-bold text-white/85 hover:text-white"><Cpu className="h-4 w-4" />Sensor network</Link>
          {user?.role === "ADMIN" && <Link to="/admin" className="font-bold text-teal-glow">Admin</Link>}
          <span className="hidden text-white/70 sm:inline">{user?.email}</span>
          <button onClick={logout} className="btn-ghost-dark px-3 py-1.5"><LogOut className="h-4 w-4" />Sign out</button>
        </div>
      </div>
    </header>
  );
}

function Queue({ items, selected, onSelect, filter, setFilter, total }: any) {
  return (
    <aside className="flex min-h-0 flex-col border-r border-line bg-surface">
      <div className="flex items-center gap-2 border-b border-line bg-paper/60 p-3">
        {[["open", "Open"], ["RESOLVED", "Resolved"], ["", "All"]].map(([v, l]) => (
          <button key={v} onClick={() => setFilter(v)} aria-pressed={filter === v}
            className={`rounded-full px-3 py-1 text-sm font-bold transition ${filter === v ? "bg-navy text-white shadow" : "text-muted hover:text-ink"}`}>{l}</button>
        ))}
        <span className="tabular ml-auto text-xs text-muted">{total} incidents</span>
      </div>
      <ul className="min-h-0 flex-1 overflow-y-auto">
        {items.length === 0 && <Empty title="No incidents routed to you">New incidents appear here as soon as the routing policy includes your service.</Empty>}
        {items.map((i: any) => {
          const n = i.notification?.status;
          return (
            <li key={i.incident_id}>
              <button onClick={() => onSelect(i.incident_id)} aria-current={selected === i.incident_id}
                className={`w-full border-b border-line border-l-4 px-3 py-3 text-left transition hover:bg-paper ${selected === i.incident_id ? "bg-teal-soft" : ""} ${n === "ESCALATED" ? "border-l-pri-critical bg-sos-soft/60" : i.severity === "CRITICAL" ? "border-l-pri-critical" : i.severity === "HIGH" ? "border-l-pri-high" : "border-l-transparent"}`}>
                <div className="flex items-center gap-2">
                  <SeverityTag severity={i.severity} score={i.priority_score} />
                  <span className="truncate font-semibold">{CATEGORY_LABEL[i.category]}</span>
                  <span className="ml-auto shrink-0 text-xs text-muted">{timeAgo(i.created_at)}</span>
                </div>
                <p className="mt-1 line-clamp-2 text-sm text-muted">{i.english_summary || "Summary unavailable"}</p>
                <div className="mt-1.5 flex flex-wrap gap-x-3 text-xs">
                  <span className="tabular text-muted">{i.incident_id}</span>
                  <span className="font-semibold">{STATUS_LABEL[i.status] || i.status}</span>
                  {n && n !== "ACKNOWLEDGED" && <span className={NOTIF_STYLE[n]}>{n === "ESCALATED" ? "Escalated: not acknowledged" : "Awaiting acknowledgement"}</span>}
                  {i.routing?.role && <span className="text-muted">{i.routing.role.toLowerCase()}</span>}
                  {(i.source === "IOT" || i.evidence_sources?.includes("iot_sensor")) && <span className="flex items-center gap-1 rounded-full bg-navy px-2 py-0.5 font-bold text-white"><Cpu className="h-3 w-3" />Sensor alert</span>}
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}

function Detail({ id, onChanged }: { id: string; onChanged: () => void }) {
  const { user } = useAuth();
  const [v, setV] = useState<any>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [shareNote, setShareNote] = useState(true);
  const [override, setOverride] = useState({ open: false, score: "", reason: "" });
  const [images, setImages] = useState<Record<string, string>>({});

  const load = useCallback(() => {
    api(`/control-room/incidents/${id}`).then((d) => { setV(d); setErr(""); }).catch((e: ApiError) => setErr(e.message));
  }, [id]);
  useEffect(() => { setV(null); load(); }, [load]);
  const moving = (v?.dispatches || []).some((d: any) => d.status === "ASSIGNED" || d.status === "EN_ROUTE");
  useEffect(() => { if (!moving) return; const t = setInterval(load, 4000); return () => clearInterval(t); }, [moving, load]);
  const navigate = useNavigate();
  useEffect(() => { if (v && v.incident_id !== id) navigate(`/ops/${v.incident_id}`, { replace: true }); }, [v, id, navigate]);
  useEffect(() => {
    const h = (e: Event) => (e as CustomEvent).detail === id && load();
    window.addEventListener("resq:incident", h);
    return () => window.removeEventListener("resq:incident", h);
  }, [id, load]);
  useEffect(() => {  // authorized image fetch (Authorization header), shown as blob URLs
    const urls: string[] = [];
    (v?.image_evidence || []).forEach(async (m: any) => {
      if (images[m.id]) return;
      try {
        const r = await fetch(`/api/v1/incidents/${id}/media/${m.id}/file`, { headers: { Authorization: `Bearer ${localStorage.getItem("resq.session.token")}` } });
        if (r.ok) { const u = URL.createObjectURL(await r.blob()); urls.push(u); setImages((s) => ({ ...s, [m.id]: u })); }
      } catch { /* image unavailable */ }
    });
    return () => urls.forEach(URL.revokeObjectURL);
  }, [v?.image_evidence?.length]); // eslint-disable-line react-hooks/exhaustive-deps

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    try { await fn(); load(); onChanged(); } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  if (err && !v) return <div className="p-6"><ErrorBox onRetry={load}>{err}</ErrorBox></div>;
  if (!v) return <Loading />;

  const isAdmin = user?.role === "ADMIN";
  const n = v.notification;
  const loc = v.location;
  const markers: MapMarker[] = [];
  if (loc.latitude != null) markers.push({ lat: loc.latitude, lng: loc.longitude, kind: "incident", label: `${v.incident_id}: ${loc.label}` });
  (v.resources || []).forEach((r: any) => markers.push({ lat: r.latitude, lng: r.longitude, kind: r.type, label: `${r.name} (${r.straight_line_km} km)` }));
  const activeDs = (v.dispatches || []).filter((d: any) => !["COMPLETED", "CANCELLED"].includes(d.status));
  activeDs.forEach((d: any) => d.live?.latitude != null && markers.push({ lat: d.live.latitude, lng: d.live.longitude, kind: d.department, unit: d.unit.unit_type,
    label: `${d.unit.call_sign}: ${d.status.replace("_", " ").toLowerCase()}${d.live.eta_remaining_min != null ? `, ${d.live.eta_remaining_min} min` : ""}` }));
  const unitRoutes = activeDs.filter((d: any) => d.route?.length > 1).map((d: any) => ({ coords: d.route, color: { HOSPITAL: "#0E8C8F", FIRE: "#E0602A", POLICE: "#2F5DB8", DISASTER: "#7A55C7" }[d.department as string], dashed: d.eta_source !== "ROAD_ROUTE" }));
  const route = v.route?.available && unitRoutes.length === 0 ? v.route.coordinates : undefined;

  return (
    <div className="grid min-h-0 gap-0 xl:grid-cols-[1fr_420px]">
      <div className="min-h-0 overflow-y-auto p-5">
        <div className="flex flex-wrap items-start gap-3">
          <div>
            <p className="tabular text-sm text-muted">{v.incident_id} · reported {clock(v.created_at)} · {v.source === "IOT" ? "hardware sensor alert" : v.sensor_evidence?.length ? "citizen report + sensor" : "citizen report"}</p>
            <h1 className="mt-0.5 text-2xl font-extrabold">{v.emergency_type}</h1>
          </div>
          <div className="ml-auto text-right"><SeverityTag severity={v.severity} score={v.priority_score} />
            <p className="mt-1 text-sm font-semibold">{STATUS_LABEL[v.status] || v.status}</p></div>
        </div>

        {!isAdmin && (
          <div className="panel mt-4 flex flex-wrap items-center gap-2 p-3">
            {n?.status !== "ACKNOWLEDGED" ? (
              <button className="btn-sos" disabled={busy} onClick={() => act(() => api(`/control-room/incidents/${id}/acknowledge`, { method: "POST" }))}>
                <Check className="h-4 w-4" />Acknowledge</button>
            ) : <span className="flex items-center gap-1.5 text-sm font-semibold text-pri-low"><Check className="h-4 w-4" />Acknowledged {clock(n.acknowledged_at)}</span>}
            {n && n.status !== "ACKNOWLEDGED" && <span className={`text-sm ${NOTIF_STYLE[n.status]}`}>
              {n.status === "ESCALATED" ? "Escalated to supervisor" : `Acknowledge by ${clock(n.ack_deadline)}`}</span>}
            <span className="mx-1 hidden h-6 w-px bg-line sm:block" />
            <label className="text-sm"><span className="sr-only">Update status</span>
              <select className="rounded-xl border border-line bg-white px-3 py-2.5 text-sm font-semibold" value="" disabled={busy}
                onChange={(e) => e.target.value && act(() => api(`/control-room/incidents/${id}/status`, { method: "POST",
                  json: { status: e.target.value, note: note || undefined, public: shareNote } }).then(() => setNote("")))}>
                <option value="">Update status…</option>
                {STATUS_FLOW.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
              </select></label>
            <input className="field min-w-[14rem] flex-1 py-2.5" placeholder="Optional note (English)" value={note} onChange={(e) => setNote(e.target.value)} maxLength={1000} />
            <label className="flex items-center gap-1.5 text-sm text-muted"><input type="checkbox" checked={shareNote} onChange={(e) => setShareNote(e.target.checked)} />Show to citizen</label>
          </div>
        )}
        {err && <div className="mt-3"><ErrorBox>{err}</ErrorBox></div>}
        <SensorBanner v={v} />
        <GenAIBrief v={v} />

        <section className="mt-5">
          <h2 className="flex flex-wrap items-center gap-2 text-sm font-bold">Report (English)
            {v.translation && <span className="rounded-full bg-teal-soft px-2 py-0.5 text-xs font-bold text-teal">Translated from {LANG_NAME[v.translation.from_language] || v.translation.from_language} · {v.translation.provider}</span>}
            {!v.translation && v.original_language && v.original_language !== "en" && v.source !== "IOT" && <span className="flex items-center gap-1 rounded-full bg-sun/20 px-2 py-0.5 text-xs font-bold text-[#8A6100]"><Loader2 className="h-3 w-3 animate-spin" />Translating from {LANG_NAME[v.original_language] || v.original_language}…</span>}
          </h2>
          <p className="mt-1 max-w-measure text-[15px] leading-relaxed">{(v.english_summary || "No English summary available.").replace(" [Auto-summary from extracted facts, not a translation]", "")}</p>
          {!v.translation && v.english_summary?.includes("Auto-summary") && <p className="mt-1 text-xs text-muted">Built from the extracted facts while the translation is pending.</p>}
          {isAdmin && v.original_text && v.original_language !== "en" && (
            <details className="mt-1 text-sm"><summary className="cursor-pointer text-xs font-semibold text-muted">Original ({LANG_NAME[v.original_language] || v.original_language})</summary><p lang={v.original_language} className="mt-1">{v.original_text}</p></details>
          )}
          {v.reports?.length > 1 && (
            <div className="mt-4">
              <p className="flex items-center gap-1.5 text-xs font-bold text-teal"><Users className="h-3.5 w-3.5" />{v.reports.length} reports of this event, merged into one incident</p>
              <ul className="mt-2 space-y-2">
                {v.reports.map((r: any) => (
                  <li key={r.id} className="rounded-xl border border-line bg-surface px-3 py-2 text-sm">
                    <p className="text-xs text-muted"><span className="tabular font-semibold text-ink">{r.id}</span> · {clock(r.created_at)} · {r.source === "IOT" ? "hardware sensor" : `citizen, ${LANG_NAME[r.language] || r.language}`}
                      {r.english_kind === "machine_translation" && " · machine-translated"}{r.english_kind === "fact_summary" && " · fact summary"}</p>
                    <p className="mt-0.5">{(r.english_text || "Translation pending…").replace(" [Auto-summary from extracted facts, not a translation]", "")}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <section className="mt-5 grid gap-4 sm:grid-cols-3">
          <div className="panel p-4"><p className="text-xs font-bold uppercase tracking-wide text-muted">Location</p>
            <p className="mt-0.5 font-semibold">{loc.label}</p>
            <p className={`text-xs ${loc.verified ? "text-pri-low" : "text-pri-high"}`}>{loc.verified ? "Verified" : "Not verified"} ({loc.source?.toLowerCase().replace("_", " ")}{loc.accuracy_m ? `, ±${Math.round(loc.accuracy_m)} m` : ""})</p>
            {loc.latitude != null && <p className="tabular text-xs text-muted">{loc.latitude.toFixed(5)}, {loc.longitude.toFixed(5)}</p>}</div>
          {"injuries" in v && <div className="panel p-3"><p className="text-xs text-muted">People</p>
            <p className="mt-0.5 font-semibold">{v.injuries} injured <span className="font-normal text-muted">({v.injury_certainty?.replace("_", " ")})</span></p>
            <p className="text-sm">{v.affected_people} involved{v.trapped ? ", some trapped" : ""}{v.unconscious ? ", unconscious reported" : ""}</p></div>}
          <div className="panel p-3"><p className="text-xs text-muted">Evidence from</p>
            <p className="mt-0.5 font-semibold">{(v.evidence_sources || []).map((s: string) => s.replace("_", " ")).join(", ")}</p>
            <p className="text-xs text-muted">Correlated sources, not independent confirmations</p></div>
        </section>

        <DispatchPanel v={v} dept={user?.role || ""} onChanged={() => { load(); onChanged(); }} />
        <AskResq v={v} dept={user?.role || ""} />

        {v.brief && (
          <section className="mt-6 grid gap-5 lg:grid-cols-2">
            <div>
              <h2 className="text-sm font-bold">Verified facts</h2>
              <dl className="mt-2 divide-y divide-line rounded-panel border border-line bg-surface">
                {v.brief.facts.map((f: any, i: number) => (
                  <div key={i} className="px-3 py-2"><dt className="text-xs text-muted">{f.label} <span className="opacity-70">({f.source})</span></dt><dd className="text-[15px]">{f.value}</dd></div>
                ))}
              </dl>
            </div>
            <div>
              <h2 className="text-sm font-bold">Rule-based checklist <span className="font-normal text-muted">(backup if GenAI is offline)</span></h2>
              <ul className="mt-2 space-y-1.5 rounded-panel border border-dashed border-line bg-paper p-3 text-[15px]">
                {v.brief.suggestions.map((s: string) => <li key={s} className="flex gap-2"><CircleDot className="mt-1 h-3.5 w-3.5 shrink-0 text-muted" />{s}</li>)}
              </ul>
              <p className="mt-1.5 text-xs text-muted">{v.brief.notice}</p>
              {v.uncertainties?.length > 0 && (<>
                <h2 className="mt-4 text-sm font-bold">Uncertain or missing</h2>
                <ul className="mt-1 list-disc pl-5 text-sm text-muted">{v.uncertainties.map((u: string) => <li key={u}>{u}</li>)}</ul></>)}
              {v.knowledge_excerpts?.length > 0 && (<>
                <h2 className="mt-4 text-sm font-bold">Reference guidance</h2>
                {v.knowledge_excerpts.map((k: any) => <blockquote key={k.document_id + k.chunk_index} className="mt-1 border-l-2 border-teal pl-3 text-sm">
                  {k.excerpt.slice(0, 280)}… <cite className="block text-xs not-italic text-muted">{k.title}, {k.publisher}{k.version ? `, v${k.version}` : ""}</cite></blockquote>)}
              </>)}
            </div>
          </section>
        )}

        {v.image_evidence?.length > 0 && (
          <section className="mt-6">
            <h2 className="text-sm font-bold">Photos</h2>
            <div className="mt-2 grid gap-3 sm:grid-cols-2">
              {v.image_evidence.map((m: any) => (
                <figure key={m.id} className="panel overflow-hidden">
                  {images[m.id] ? <img src={images[m.id]} alt="Citizen-submitted scene" className="aspect-video w-full object-cover" />
                    : <div className="flex aspect-video items-center justify-center bg-paper text-muted"><ImageOff className="h-6 w-6" /></div>}
                  <figcaption className="p-3 text-sm">
                    <p className="font-semibold">{m.status.replaceAll("_", " ").toLowerCase()}{m.recommended_review && <span className="ml-2 text-pri-high">needs human review</span>}</p>
                    {m.findings?.length > 0 && <ul className="mt-1 text-muted">{m.findings.map((f: any, i: number) => <li key={i}>{f.finding.replaceAll("_", " ")} ({f.confidence_level}){f.description ? `: ${f.description}` : ""}</li>)}</ul>}
                    {m.error && <p className="text-xs text-muted">Analysis: {m.error}</p>}
                    {m.quality_flags?.length > 0 && <p className="text-xs text-pri-high">{m.quality_flags.join(", ").replaceAll("_", " ")}</p>}
                  </figcaption>
                </figure>
              ))}
            </div>
          </section>
        )}

        {v.sensor_evidence?.length > 1 && (
          <section className="mt-6"><h2 className="text-sm font-bold">All sensor alerts on this incident</h2>
            <ul className="mt-1 text-sm">{v.sensor_evidence.map((s: any) => <li key={s.event_id}><span className="tabular text-muted">{clock(s.timestamp)}</span> {s.device_name}: {s.reason} ({s.observed_value} {s.unit})</li>)}</ul></section>
        )}

        <section className="mt-6">
          <h2 className="text-sm font-bold">Why your service was included</h2>
          {(Array.isArray(v.routing) ? v.routing : [v.routing]).filter(Boolean).map((r: any) => (
            <p key={r.department} className="mt-1 text-sm"><strong>{DEPT_LABEL[r.department]}</strong> {r.included ? `(${r.role?.toLowerCase()})` : "(not included)"}: {r.reasons.join("; ")} <span className="text-xs text-muted">{r.policy_version}</span></p>
          ))}
        </section>

        <section className="mt-6">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-bold">Priority evidence</h2>
            <button className="btn-text text-xs" onClick={() => setOverride((o) => ({ ...o, open: !o.open }))}>Override priority</button>
          </div>
          <ul className="mt-1 text-sm text-muted">{v.priority_evidence?.evidence.map((e: any, i: number) => <li key={i} className="tabular">+{e.points} {e.factor} <span className="opacity-70">({e.source})</span></li>)}</ul>
          {v.priority_evidence?.override_reason && <p className="mt-1 text-sm text-pri-high">Manually set: {v.priority_evidence.override_reason}</p>}
          {override.open && (
            <form className="mt-2 flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); act(() => api(`/control-room/incidents/${id}/priority-override`, { method: "POST", json: { score: Number(override.score), reason: override.reason } })).then(() => setOverride({ open: false, score: "", reason: "" })); }}>
              <input className="field w-24" type="number" min={0} max={100} required placeholder="0–100" value={override.score} onChange={(e) => setOverride({ ...override, score: e.target.value })} />
              <input className="field flex-1" required minLength={5} placeholder="Reason (recorded in audit log)" value={override.reason} onChange={(e) => setOverride({ ...override, reason: e.target.value })} />
              <button className="btn-primary" disabled={busy}>Save override</button>
            </form>
          )}
        </section>

        {v.updates && (
          <section className="mt-6"><h2 className="text-sm font-bold">History</h2>
            <ul className="mt-1 text-sm">{v.updates.map((u: any, i: number) => <li key={i}><span className="tabular text-muted">{clock(u.at)}</span> {u.by} {u.status ? `→ ${u.status}` : ""} {u.note}</li>)}</ul></section>
        )}
      </div>

      <div className="border-t border-line bg-surface p-4 xl:border-l xl:border-t-0">
        {markers.length > 0 ? <MapView markers={markers} route={route} routes={unitRoutes} height={360} fitKey={`${v.incident_id}:${activeDs.length}:${(v.resources || []).length}`} /> : <Empty title="No coordinates">The location could not be verified. Use the landmark text above.</Empty>}
        {v.route && (
          <div className="mt-3 text-sm">
            {v.route.available ? (<>
              <p className="font-semibold">{v.route.distance_km} km by road, about {v.route.eta_min} min</p>
              <p className="text-muted">From {v.route.origin_name}. {v.route.eta_note}</p>
              <p className="text-xs text-muted">Route: {v.route.provider}{v.route.route_corridor ? `, via ${v.route.route_corridor}` : ""}</p>
            </>) : (
              <p className="flex gap-2 text-pri-high"><AlertTriangle className="h-4 w-4 shrink-0" />Routing unavailable. {v.route.message} {v.route.straight_line_km != null && `Straight-line distance: ${v.route.straight_line_km} km.`}</p>
            )}
          </div>
        )}
        <h2 className="mt-5 text-sm font-bold">Nearest {isAdmin ? "" : "relevant "}facilities</h2>
        <ul className="mt-1 divide-y divide-line text-sm">
          {(v.resources || []).map((r: any) => (
            <li key={r.id} className="py-2"><p className="font-semibold">{r.name}</p>
              <p className="text-muted">{r.straight_line_km} km straight line · availability {r.availability_status.toLowerCase()}{r.data_source === "DEMO_SEED" ? " · demo data" : r.data_source === "OSM" ? " · OpenStreetMap" : ""}</p></li>
          ))}
          {(v.resources || []).length === 0 && <li className="py-2 text-muted">No registered facilities within 25 km.</li>}
        </ul>
      </div>
    </div>
  );
}

export default function ControlRoom() {
  const { user, token, ready } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("open");
  const [err, setErr] = useState("");
  const [live, setLive] = useState<"connecting" | "live" | "offline">("connecting");
  const wsRef = useRef<WebSocket | null>(null);

  const load = useCallback(() => {
    api(`/control-room/incidents?status=${filter}&limit=100`).then((d) => { setItems(d.items); setTotal(d.total); setErr(""); }).catch((e) => setErr(e.message));
  }, [filter]);
  useEffect(() => { if (user) load(); }, [user, load]);

  useEffect(() => {  // WebSocket with reconnect; polling fallback when offline
    if (!token || !user) return;
    let stop = false, retry = 1000, timer: any;
    const connect = () => {
      setLive("connecting");
      const ws = new WebSocket(wsUrl("/ws/control-room", token));
      wsRef.current = ws;
      ws.onopen = () => { setLive("live"); retry = 1000; };
      ws.onmessage = (e) => {
        const m = JSON.parse(e.data);
        if (m.type === "incident.notification" && m.notification_id) ws.send(JSON.stringify({ type: "delivered", notification_id: m.notification_id }));
        if (m.incident_id || m.incident?.incident_id) {
          load();
          window.dispatchEvent(new CustomEvent("resq:incident", { detail: m.incident_id || m.incident.incident_id }));
        }
      };
      ws.onclose = () => { setLive("offline"); if (!stop) timer = setTimeout(connect, (retry = Math.min(retry * 2, 30000))); };
    };
    connect();
    const poll = setInterval(() => wsRef.current?.readyState !== WebSocket.OPEN && load(), 20000);
    return () => { stop = true; clearTimeout(timer); clearInterval(poll); wsRef.current?.close(); };
  }, [token, user, load]);

  if (!ready) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div lang="en" className="flex h-screen flex-col">
      <Header live={live} />
      {err && <div className="p-3"><ErrorBox onRetry={load}>{err}</ErrorBox></div>}
      <div className="grid min-h-0 flex-1 md:grid-cols-[360px_1fr]">
        <div className={`${id ? "hidden md:flex" : "flex"} min-h-0 flex-col`}>
          <Queue items={items} total={total} selected={id} onSelect={(i: string) => navigate(`/ops/${i}`)} filter={filter} setFilter={setFilter} />
        </div>
        <main className={`${id ? "block" : "hidden md:block"} min-h-0 overflow-y-auto xl:overflow-hidden`}>
          {id ? (<>
            <button className="btn-text m-3 md:hidden" onClick={() => navigate("/ops")}>Back to queue</button>
            <DetailBoundary id={id}><Detail id={id} onChanged={load} /></DetailBoundary>
          </>) : <SensorConsole isAdmin={user.role === "ADMIN"} />}
        </main>
      </div>
    </div>
  );
}
