import { useEffect, useRef, useState } from "react";
import { AlertTriangle, BookOpen, CheckCircle2, HelpCircle, Loader2, MessageSquareText, RefreshCw, Send, ShieldCheck, Sparkles, Wrench } from "lucide-react";
import { api, ApiError } from "../lib/api";

type Cite = { id: string; title: string; publisher: string; excerpt: string };

function Citations({ items }: { items: Cite[] }) {
  if (!items?.length) return null;
  return (
    <details className="mt-3 text-sm">
      <summary className="flex cursor-pointer items-center gap-1.5 text-xs font-bold text-teal-glow"><BookOpen className="h-3.5 w-3.5" />
        Grounded in {items.length} retrieved guidance passage{items.length > 1 ? "s" : ""} (RAG)</summary>
      {items.map((c) => (
        <blockquote key={c.id} className="mt-2 rounded-xl bg-white/5 p-3 text-white/85">
          <span className="mr-1.5 rounded bg-white/15 px-1.5 py-0.5 text-[11px] font-black">{c.id}</span>{c.excerpt.slice(0, 260)}…
          <cite className="mt-1 block text-xs not-italic text-white/55">{c.title} · {c.publisher}</cite>
        </blockquote>
      ))}
    </details>
  );
}

/** GenAI incident brief: written by the LLM from the verified record + retrieved guidance, grounding-checked. */
export function GenAIBrief({ v }: { v: any }) {
  const [b, setB] = useState<any>(v.genai_brief || null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [secs, setSecs] = useState(0);
  useEffect(() => { if (!busy) return; setSecs(0); const iv = setInterval(() => setSecs((x) => x + 1), 1000); return () => clearInterval(iv); }, [busy]);
  const key = `${v.incident_id}:${v.priority_score}:${v.reports?.length}:${(v.dispatches || []).length}`;
  const load = (refresh = false) => {
    setBusy(true); setErr("");
    api(`/control-room/incidents/${v.incident_id}/genai-brief${refresh ? "?refresh=true" : ""}`)
      .then(setB).catch((e: ApiError) => setErr(e.message)).finally(() => setBusy(false));
  };
  useEffect(() => { if (v.genai_brief) setB(v.genai_brief); else load(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const gen = b?.generated;
  return (
    <section className="dark-band mt-4 overflow-hidden rounded-panel p-5 text-white shadow-lift" aria-live="polite">
      <div className="flex flex-wrap items-center gap-2">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-[#FF4A64] to-[#7A55C7]"><Sparkles className="h-5 w-5" /></span>
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-wide text-teal-glow">GenAI incident brief</p>
          <p className="text-xs text-white/60">{b ? (gen ? `Written by ${b.model?.replace("ollama:", "")} from ${b.facts_used} verified facts + ${b.guidance_used} guidance passages` : "GenAI offline: rule-based checklist shown") : "Reading the record and the guidance…"}</p>
        </div>
        {b && <span className={`ml-auto flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${b.grounding === "passed" ? "bg-pri-low/25 text-[#8CF0B6]" : b.grounding === "partial" ? "bg-sun/25 text-[#FFD66B]" : "bg-white/10 text-white/70"}`}>
          <ShieldCheck className="h-3.5 w-3.5" />{b.grounding === "passed" ? "Grounding check passed" : b.grounding === "partial" ? "Unsupported lines removed" : "Fallback"}</span>}
        <button onClick={() => load(true)} disabled={busy} className="flex items-center gap-1 rounded-full bg-white/10 px-2.5 py-1 text-xs font-bold hover:bg-white/20 disabled:opacity-50" aria-label="Regenerate brief">
          <RefreshCw className={`h-3.5 w-3.5 ${busy ? "animate-spin" : ""}`} />Regenerate</button>
      </div>

      {!b && busy && <p className="mt-4 flex items-center gap-2 text-white/80"><Loader2 className="h-4 w-4 animate-spin" />GenAI is reading the record and the guidance, and writing the brief for your service… <span className="tabular text-white/55">{secs} s</span></p>}
      {err && !b && <p className="mt-4 text-sm text-[#FFB4BF]">{err}</p>}
      {b && (
        <>
          <h2 className="mt-4 text-xl font-black leading-snug">{b.headline}</h2>
          {b.situation && <p className="mt-1.5 max-w-measure text-[15px] leading-relaxed text-white/85">{b.situation}</p>}
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div>
              <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-white/60"><CheckCircle2 className="h-3.5 w-3.5" />Priority actions</p>
              <ol className="mt-1.5 space-y-1.5">
                {b.actions.map((a: string, i: number) => <li key={i} className="flex gap-2.5 text-[15px]"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white text-xs font-black text-navy">{i + 1}</span>{a}</li>)}
              </ol>
            </div>
            <div className="space-y-3">
              {b.prepare?.length > 0 && <div><p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-white/60"><Wrench className="h-3.5 w-3.5" />Prepare</p>
                <ul className="mt-1 list-disc pl-5 text-[15px] text-white/90">{b.prepare.map((x: string) => <li key={x}>{x}</li>)}</ul></div>}
              {b.risks?.length > 0 && <div><p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-[#FFB4BF]"><AlertTriangle className="h-3.5 w-3.5" />Watch for</p>
                <ul className="mt-1 list-disc pl-5 text-[15px] text-white/90">{b.risks.map((x: string) => <li key={x}>{x}</li>)}</ul></div>}
              {b.confirm?.length > 0 && <div><p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-white/60"><HelpCircle className="h-3.5 w-3.5" />Confirm</p>
                <ul className="mt-1 list-disc pl-5 text-[15px] text-white/90">{b.confirm.map((x: string) => <li key={x}>{x}</li>)}</ul></div>}
            </div>
          </div>
          <Citations items={b.citations} />
          {b.checks?.length > 0 && gen && <p className="mt-2 text-xs text-white/50">Safety check: {b.checks.join("; ")}.</p>}
          <p className="mt-2 text-xs text-white/45">Advice for trained personnel, generated only from this incident's verified record. Dispatch decisions stay with the control room.</p>
        </>
      )}
    </section>
  );
}

const SUGGESTED: Record<string, string[]> = {
  HOSPITAL: ["Is the patient breathing?", "What should the trauma team prepare?", "Which ambulance is closest?"],
  POLICE: ["Is the road blocked?", "What should we do about traffic?", "Has anyone confirmed the crash?"],
  FIRE: ["Is anyone trapped?", "Is there a fire or fuel risk?", "What equipment do we need?"],
  DISASTER: ["How many people are affected?", "Is evacuation needed?", "Which services are responding?"],
  ADMIN: ["Summarise this incident", "Which services were alerted?", "What is still unknown?"],
};

/** Ask RESQ: question answering over this incident's record + guidance, with refusals when the record is silent. */
export function AskResq({ v, dept }: { v: any; dept: string }) {
  const [q, setQ] = useState("");
  const [log, setLog] = useState<{ q: string; a?: any; err?: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { setLog([]); }, [v.incident_id]);
  useEffect(() => { end.current?.scrollIntoView({ block: "nearest" }); }, [log]);
  async function ask(question: string) {
    if (!question.trim() || busy) return;
    setBusy(true); setQ("");
    setLog((l) => [...l, { q: question }]);
    try {
      const a = await api(`/control-room/incidents/${v.incident_id}/ask`, { method: "POST", json: { question } });
      setLog((l) => l.map((x, i) => (i === l.length - 1 ? { ...x, a } : x)));
    } catch (e) {
      setLog((l) => l.map((x, i) => (i === l.length - 1 ? { ...x, err: (e as Error).message } : x)));
    } finally { setBusy(false); }
  }
  return (
    <section className="panel mt-4 p-4">
      <h2 className="flex items-center gap-2 text-sm font-bold"><MessageSquareText className="h-4 w-4 text-teal" />Ask RESQ
        <span className="font-normal text-muted">GenAI answers from this incident's record and the guidance only</span></h2>
      {log.length === 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {(SUGGESTED[dept] || SUGGESTED.ADMIN).map((s) => <button key={s} onClick={() => ask(s)} className="rounded-full border border-line bg-surface px-3 py-1.5 text-sm hover:border-teal">{s}</button>)}
        </div>
      )}
      <div className="mt-3 max-h-80 space-y-3 overflow-y-auto">
        {log.map((x, i) => (
          <div key={i}>
            <p className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-navy px-3 py-2 text-sm text-white">{x.q}</p>
            {x.a ? (
              <div className="mt-1.5 max-w-[90%] rounded-2xl rounded-bl-md border border-line bg-surface px-3 py-2 text-[15px]">
                <p>{x.a.answer}</p>
                <p className={`mt-1 text-xs font-semibold ${x.a.grounded ? "text-pri-low" : "text-pri-high"}`}>
                  {x.a.grounded ? "Answered from the record" : "Not in the record: confirm with the crew or caller"}
                  {x.a.citations?.length ? ` · cites ${x.a.citations.map((c: Cite) => c.id).join(", ")}` : ""}</p>
              </div>
            ) : x.err ? <p className="mt-1 text-sm text-sos">{x.err}</p>
              : <p className="mt-1.5 flex items-center gap-2 text-sm text-muted"><Loader2 className="h-4 w-4 animate-spin" />Thinking…</p>}
          </div>
        ))}
        <div ref={end} />
      </div>
      <form className="mt-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); ask(q); }}>
        <label className="sr-only" htmlFor="askq">Ask a question about this incident</label>
        <input id="askq" className="field flex-1 py-2.5" placeholder="Ask about this incident…" value={q} onChange={(e) => setQ(e.target.value)} maxLength={400} />
        <button className="btn-primary px-4" disabled={busy || q.trim().length < 2} aria-label="Ask"><Send className="h-4 w-4" /></button>
      </form>
    </section>
  );
}
