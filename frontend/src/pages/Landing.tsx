import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowRight, Bell, Camera, Car, Cpu, Droplets, Flame, HeartPulse, Languages, Layers, Lock, MapPinned, MessageSquare, Phone, Radio, Shield, ShieldCheck, Sparkles, BookOpen } from "lucide-react";
import { Radar } from "../components/Radar";

const SAMPLES = [
  "Car hit a bike at the signal, one person bleeding…",
  "సిగ్నల్ దగ్గర కారు బైక్‌ను ఢీకొంది, ఒకరికి రక్తం కారుతోంది…",
  "சிக்னலில் கார் பைக்கை மோதியது, ஒருவருக்கு இரத்தம் வருகிறது…",
  "सिग्नल पर कार ने बाइक को टक्कर मारी, एक व्यक्ति को खून बह रहा है…",
];

const PIPE = [
  { Icon: MessageSquare, t: "Report", d: "Text, voice, photos or an ESP32 sensor alert" },
  { Icon: Languages, t: "GenAI translates", d: "Qwen3 turns Telugu, Tamil or Hindi into faithful English", ai: true },
  { Icon: Sparkles, t: "GenAI understands", d: "Few-shot Qwen3-4B and Qwen2.5-VL-3B extract checked facts from text and photos", ai: true },
  { Icon: Layers, t: "Priority & routing", d: "A 0–100 score with every reason; only the services needed" },
  { Icon: BookOpen, t: "GenAI briefs (RAG)", d: "Each control room gets a brief grounded in the record and cited guidance", ai: true },
  { Icon: Bell, t: "Dispatch", d: "Nearest unit sent; GenAI guides the citizen while help arrives" },
];

const FEATURES = [
  { Icon: Sparkles, t: "GenAI incident briefs", d: "For every service, the LLM writes what happened, what to do first, what to prepare and what to confirm, from the verified record and retrieved guidance. Invented numbers are removed before anyone sees it.", c: "#7A55C7" },
  { Icon: MessageSquare, t: "Ask RESQ", d: "Responders ask questions about an incident in plain English. GenAI answers only from the record and the guidance, and says so when the record does not know.", c: "#C8102E" },
  { Icon: BookOpen, t: "RAG safety guidance", d: "Approved guidance is retrieved for the situation and GenAI writes calm, cited steps for the citizen, in their own language, while help is on the way.", c: "#0E8C8F" },
  { Icon: Languages, t: "Four languages, end to end", d: "A Telugu, Tamil or Hindi report is machine-translated to English for control rooms, and responders' notes are translated back for the citizen.", c: "#0E8C8F" },
  { Icon: Camera, t: "Photos as evidence", d: "Location metadata stripped, blur and duplicates flagged, then a vision model describes only what is visible.", c: "#C8102E" },
  { Icon: Cpu, t: "ESP32 roadside sensors", d: "Impact, smoke, water level and an SOS pad. Every event has a unique ID, so retries never duplicate incidents.", c: "#2F5DB8" },
  { Icon: MapPinned, t: "Nearest unit, sent automatically", d: "Sensor alerts and high-priority incidents get the closest ambulance, fire tender or patrol at once. The citizen watches it arrive; the crew updates status from their phone.", c: "#E0602A" },
  { Icon: Radio, t: "Live control rooms", d: "Instant WebSocket alerts, acknowledgement deadlines and automatic escalation to a supervisor.", c: "#7A55C7" },
  { Icon: Lock, t: "Private by design", d: "Role-based access, per-department field filtering, private tracking codes and a full audit log.", c: "#2F7A55" },
];

export default function Landing() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const [text, setText] = useState("");
  const [i, setI] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = setInterval(() => setI((x) => (x + 1) % SAMPLES.length), 3200);
    return () => clearInterval(id);
  }, []);

  return (
    <div>
      {/* ============ HERO ============ */}
      <section className="dark-band relative overflow-hidden text-white">
        <div className="speed-lines absolute inset-0" />
        <div className="absolute -right-40 top-1/2 hidden -translate-y-1/2 opacity-90 lg:block xl:right-0"><Radar size={620} /></div>
        <div className="relative mx-auto max-w-7xl px-4 pb-20 pt-32 sm:px-6 lg:pb-28 lg:pt-40">
          <div className="max-w-2xl animate-rise">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-sm font-bold backdrop-blur">
              <span className="h-2 w-2 animate-blink rounded-full bg-sos-glow" />GenAI emergency decision support
            </span>
            <h1 className="mt-6 text-4xl font-black leading-[1.05] sm:text-5xl lg:text-6xl"><span className="grad-text">{t("hero.title")}</span></h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/75">{t("hero.subtitle")}</p>
          </div>

          <form className="glass mt-10 max-w-2xl animate-rise p-5 shadow-lift [animation-delay:.15s] sm:p-6"
            onSubmit={(e) => { e.preventDefault(); nav("/report", { state: { text } }); }}>
            <label htmlFor="hero-report" className="text-lg font-bold">{t("hero.label")}</label>
            <textarea id="hero-report" rows={3} value={text} onChange={(e) => setText(e.target.value)}
              placeholder={SAMPLES[i]} className="mt-3 w-full resize-none rounded-xl border border-white/20 bg-white/95 px-4 py-3 text-base text-ink placeholder:text-muted/70 focus:outline-none focus:ring-4 focus:ring-teal-glow/30" />
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <button className="btn-sos px-6 py-3.5 text-base" type="submit">{t("hero.cta")}<ArrowRight className="h-5 w-5" /></button>
              <a href="tel:112" className="btn-ghost-dark"><Phone className="h-4 w-4" />{t("hero.call")}</a>
            </div>
          </form>

          <dl className="mt-10 grid max-w-2xl grid-cols-3 gap-4 animate-rise [animation-delay:.3s]">
            {[["0", "phone calls needed when a sensor detects a crash"], ["4", "languages for citizens"], ["1", "incident per event, however many reports"]].map(([n, l]) => (
              <div key={l} className="border-l-2 border-teal-glow/60 pl-4">
                <dt className="text-4xl font-black text-white">{n}</dt><dd className="mt-1 text-sm text-white/65">{l}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* ============ HARDWARE AUTO-DISPATCH (headline) ============ */}
      <section className="relative overflow-hidden bg-surface">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-sos/10 px-3 py-1 text-sm font-black text-sos"><Cpu className="h-4 w-4" />Hardware that calls for help</span>
            <h2 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">When nobody can make the call, the sensor makes it.</h2>
            <p className="mt-4 max-w-xl text-lg leading-relaxed text-muted">A crash victim may be unconscious. A fire may start at 3 a.m. in an empty shop. RESQ.AI's ESP32 units detect it themselves and alert the hospital, police and fire service at once, with the exact location.</p>
            <ol className="mt-8 space-y-5">
              {[
                ["Detects", "MPU6050 impact, MQ-2 smoke and gas, DHT22 heat and a water-level probe watch the scene around the clock."],
                ["Confirms on the device", "A reading must stay above its limit before it counts, so a pothole or a passing lorry is not reported as a crash."],
                ["Dispatches everyone needed", "Over Wi-Fi, or SIM800L mobile data when Wi-Fi is down. A crash alerts hospital and police, a severe crash adds fire and rescue, and a fire alerts all three."],
              ].map(([h, d], n) => (
                <li key={h} className="flex gap-4">
                  <span className="step-num shrink-0">{n + 1}</span>
                  <div><h3 className="text-lg font-black">{h}</h3><p className="mt-0.5 text-[15px] leading-relaxed text-muted">{d}</p></div>
                </li>
              ))}
            </ol>
          </div>

          {/* animated flow: device -> RESQ.AI -> three control rooms */}
          <div className="dark-band relative overflow-hidden rounded-xl2 p-6 text-white shadow-lift sm:p-8" aria-hidden="true">
            <div className="speed-lines absolute inset-0 opacity-70" />
            <div className="relative grid grid-cols-[1fr_auto_1fr] items-center gap-3 sm:gap-6">
              <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur">
                <div className="flex items-center gap-2 text-xs font-bold text-teal-glow"><Cpu className="h-4 w-4" />RESQ-ESP32-001</div>
                <p className="mt-1 text-sm font-black">GST Road crash sensor</p>
                <div className="mt-3 space-y-1.5 text-xs">
                  <p className="flex items-center gap-2 rounded-lg bg-sos/40 px-2 py-1.5 font-bold"><Car className="h-3.5 w-3.5" />Impact 6.4 g <span className="ml-auto animate-blink">ALERT</span></p>
                  <p className="flex items-center gap-2 rounded-lg bg-white/10 px-2 py-1.5"><Flame className="h-3.5 w-3.5" />Smoke normal</p>
                  <p className="flex items-center gap-2 rounded-lg bg-white/10 px-2 py-1.5"><Droplets className="h-3.5 w-3.5" />Water normal</p>
                </div>
              </div>

              <div className="relative flex h-full flex-col items-center justify-center">
                <div className="relative h-1.5 w-12 overflow-hidden rounded-full bg-white/15 sm:w-20">
                  {[0, 1.5, 3].map((d) => <span key={d} className="absolute top-1/2 h-2.5 w-2.5 -translate-y-1/2 animate-travel rounded-full bg-sos-glow shadow-[0_0_10px_#FF4A64]" style={{ animationDelay: `${d}s` }} />)}
                </div>
                <span className="relative mt-3 grid h-16 w-16 place-items-center rounded-full shadow-glowred" style={{ backgroundImage: "radial-gradient(circle at 35% 30%,#FF4A64,#C8102E 60%,#8E0A20)" }}>
                  <span className="absolute inset-0 animate-ring rounded-full border-2 border-sos-glow/70" />
                  <Sparkles className="h-7 w-7" />
                </span>
                <span className="mt-2 text-xs font-black">RESQ.AI</span>
                <div className="relative mt-3 h-1.5 w-12 overflow-hidden rounded-full bg-white/15 sm:w-20">
                  {[0.7, 2.2, 3.7].map((d) => <span key={d} className="absolute top-1/2 h-2.5 w-2.5 -translate-y-1/2 animate-travel rounded-full bg-teal-glow shadow-[0_0_10px_#6EE7E2]" style={{ animationDelay: `${d}s` }} />)}
                </div>
              </div>

              <ul className="space-y-2.5">
                {[
                  { Icon: HeartPulse, n: "Hospital", r: "Ambulance needed", c: "#0E8C8F" },
                  { Icon: Shield, n: "Police", r: "Scene and traffic", c: "#2F5DB8" },
                  { Icon: Flame, n: "Fire & rescue", r: "Severe impact", c: "#E0602A" },
                ].map(({ Icon, n, r, c }, k) => (
                  <li key={n} className="flex items-center gap-3 rounded-2xl border border-white/15 bg-white/10 p-3 backdrop-blur animate-rise" style={{ animationDelay: `${0.2 + k * 0.15}s` }}>
                    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl" style={{ background: c }}><Icon className="h-5 w-5" /></span>
                    <div className="min-w-0"><p className="text-sm font-black">{n}</p><p className="truncate text-xs text-white/70">{r}</p></div>
                    <span className="ml-auto h-2.5 w-2.5 shrink-0 animate-blink rounded-full bg-sun" />
                  </li>
                ))}
              </ul>
            </div>
            <p className="relative mt-6 rounded-xl bg-white/10 px-4 py-3 text-sm text-white/85">
              <strong className="text-white">Incident created, scored and sent</strong> to every control room in the same step. Each room sees the sensor reading, the location on the map and who else is on the way.
            </p>
          </div>
        </div>
      </section>

      {/* ============ PIPELINE ============ */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <p className="text-sm font-black uppercase tracking-widest text-teal-mid">How it works</p>
        <h2 className="mt-2 max-w-2xl text-4xl font-black">Generative AI at every step, from alert to arrival</h2>
        <div className="relative mt-14">
          <div className="absolute left-[8%] right-[8%] top-10 hidden h-1.5 overflow-hidden rounded-full bg-gradient-to-r from-teal via-sos to-teal md:block">
            {[0, 1.5, 3].map((d) => <span key={d} className="absolute top-1/2 h-3 w-3 -translate-y-1/2 animate-travel rounded-full bg-white shadow-[0_0_12px_white]" style={{ animationDelay: `${d}s` }} />)}
          </div>
          <ol className="relative grid gap-10 sm:grid-cols-2 md:grid-cols-6 md:gap-4">
            {PIPE.map(({ Icon, t: title, d, ai }, n) => (
              <li key={title} className="flex flex-col items-center text-center">
                <div className={`flex h-20 w-20 items-center justify-center rounded-full transition hover:scale-110 ${ai ? "text-white shadow-glowred ring-8 ring-sos/15" : "border-4 border-teal-mid bg-white text-teal shadow-card"}`}
                  style={ai ? { backgroundImage: "radial-gradient(circle at 35% 30%,#FF4A64,#C8102E 60%,#8E0A20)" } : undefined}>
                  <Icon className="h-9 w-9" strokeWidth={2} />
                </div>
                <span className="mt-4 text-xs font-black text-muted">STEP {n + 1}</span>
                <h3 className={`mt-1 text-xl font-black ${ai ? "text-sos" : ""}`}>{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted">{d}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ============ SHOWCASE ============ */}
      <section className="dark-band relative overflow-hidden text-white">
        <div className="speed-lines absolute inset-0" />
        <div className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6">
          <p className="text-sm font-black uppercase tracking-widest text-teal-glow">See it work</p>
          <h2 className="mt-2 max-w-3xl text-4xl font-black">One road accident, reported in Telugu, seen by the fire control room in English</h2>
          <div className="mt-14 grid items-end gap-10 lg:grid-cols-[1.6fr_1fr]">
            <figure className="relative">
              <span className="absolute -top-4 left-6 z-10 rounded-full bg-teal-mid px-4 py-1.5 text-sm font-bold shadow-lg">3 · Fire control room</span>
              <div className="rounded-t-2xl border border-white/15 bg-navy-3 p-3 pb-0 shadow-[0_30px_80px_rgba(0,0,0,.5),0_0_80px_rgba(14,140,143,.35)]">
                <img src="/showcase/control-room.webp" alt="Fire control room console showing the incident as an English brief" className="w-full rounded-t-lg" loading="lazy" />
              </div>
              <div className="-mx-6 h-5 rounded-b-3xl bg-gradient-to-b from-slate-300 to-slate-500" />
            </figure>
            <div className="flex justify-center gap-6">
              {[["/showcase/report-te.webp", "1 · Report in Telugu", "bg-sos", "-rotate-3"], ["/showcase/track-te.webp", "2 · Priority + guidance", "bg-sun text-ink", "rotate-3 translate-y-6"]].map(([src, label, chip, rot]) => (
                <figure key={src} className={`relative ${rot} transition hover:rotate-0`}>
                  <span className={`absolute -top-4 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded-full px-3 py-1 text-xs font-bold shadow-lg ${chip}`}>{label}</span>
                  <div className="w-40 rounded-[2rem] border border-white/15 bg-navy-3 p-2 shadow-[0_30px_60px_rgba(0,0,0,.55)] sm:w-48">
                    <img src={src} alt={label} className="w-full rounded-[1.6rem]" loading="lazy" />
                  </div>
                </figure>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============ FEATURES ============ */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <p className="text-sm font-black uppercase tracking-widest text-teal-mid">What's inside</p>
        <h2 className="mt-2 text-4xl font-black">Built for real emergencies</h2>
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ Icon, t: title, d, c }) => (
            <div key={title} className="panel group relative overflow-hidden p-7 transition duration-300 hover:-translate-y-1 hover:shadow-lift">
              <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full opacity-10 transition group-hover:scale-125" style={{ background: c }} />
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl text-white" style={{ background: c, boxShadow: `0 12px 26px -8px ${c}` }}>
                <Icon className="h-7 w-7" />
              </div>
              <h3 className="mt-5 text-xl font-black">{title}</h3>
              <p className="mt-2 leading-relaxed text-muted">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ============ ONE INCIDENT, THREE VIEWS ============ */}
      <section className="mx-auto max-w-7xl px-4 pb-20 sm:px-6">
        <div className="panel overflow-hidden">
          <div className="grid lg:grid-cols-[1fr_1.4fr]">
            <div className="dark-band p-8 text-white sm:p-10">
              <p className="text-sm font-black uppercase tracking-widest text-teal-glow">Smart routing</p>
              <h2 className="mt-2 text-3xl font-black">Not every alert goes to everyone</h2>
              <p lang="te" className="mt-6 rounded-2xl border border-white/15 bg-white/10 p-4 text-lg">“సిగ్నల్ దగ్గర కారు బైక్‌ను ఢీకొంది. ఒకరు లోపల చిక్కుకున్నారు, పెట్రోల్ లీక్ అవుతోంది.”</p>
              <p className="mt-3 text-sm text-white/65">+ impact sensor alert + photo of a damaged vehicle</p>
            </div>
            <div className="grid gap-4 p-6 sm:grid-cols-3 sm:p-8">
              {[["Hospital / EMS", "Person trapped, may need care", "#0E8C8F", true], ["Police", "Road accident: traffic and scene", "#2F5DB8", true], ["Fire & rescue", "Entrapment and fuel leak", "#E0602A", true], ["Disaster response", "Not a flood, under 20 people", "#94A3B8", false]].map(([dep, why, c, inc]) => (
                <div key={dep as string} className={`rounded-2xl border p-4 ${inc ? "border-line bg-white" : "border-dashed border-line bg-paper sm:col-span-3"}`}>
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full" style={{ background: c as string, boxShadow: inc ? `0 0 10px ${c}` : "none" }} />
                    <h3 className="font-black">{dep as string}</h3>
                    <span className={`ml-auto rounded-full px-2 py-0.5 text-xs font-bold ${inc ? "bg-teal-soft text-teal" : "bg-line text-muted"}`}>{inc ? "Notified" : "Not needed"}</span>
                  </div>
                  <p className="mt-2 text-sm text-muted">{why as string}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============ CTA ============ */}
      <section className="mx-auto grid max-w-7xl gap-6 px-4 pb-24 sm:px-6 md:grid-cols-2">
        <div className="relative overflow-hidden rounded-xl2 p-8 text-white shadow-glowred" style={{ backgroundImage: "linear-gradient(135deg,#FF4A64,#C8102E 55%,#7E0919)" }}>
          <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full border-[28px] border-white/10" />
          <h2 className="relative text-3xl font-black">Need help now?</h2>
          <p className="relative mt-2 text-white/85">Call 112, then send a report so the right services get the details.</p>
          <div className="relative mt-6 flex flex-wrap gap-3">
            <a href="tel:112" className="btn bg-white text-sos shadow-lg hover:-translate-y-0.5"><Phone className="h-4 w-4" />Call 112</a>
            <Link to="/report" className="btn-ghost-dark">Report an emergency<ArrowRight className="h-4 w-4" /></Link>
          </div>
        </div>
        <div className="dark-band relative overflow-hidden rounded-xl2 p-8 text-white shadow-lift">
          <div className="absolute -bottom-20 -right-20 h-64 w-64 rounded-full border border-teal-glow/30" />
          <h2 className="relative flex items-center gap-3 text-3xl font-black"><ShieldCheck className="h-8 w-8 text-teal-glow" />Emergency services</h2>
          <p className="relative mt-2 text-white/75">Hospitals, police, fire stations and disaster cells see only the incidents routed to them.</p>
          <Link to="/login" className="btn-primary relative mt-6">Sign in to your control room<ArrowRight className="h-4 w-4" /></Link>
        </div>
      </section>
    </div>
  );
}
