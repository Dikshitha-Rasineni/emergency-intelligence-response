import { Flame, MapPin, Shield, Waves, Cross } from "lucide-react";

/** Animated "incident → departments" radar used in hero sections. Decorative. */
export function Radar({ size = 520 }: { size?: number }) {
  const nodes = [
    { Icon: Cross, label: "Hospital", color: "#0E8C8F", x: 18, y: 16, d: "0s" },
    { Icon: Shield, label: "Police", color: "#2F5DB8", x: 82, y: 16, d: ".8s" },
    { Icon: Flame, label: "Fire", color: "#E0602A", x: 82, y: 80, d: "1.6s" },
    { Icon: Waves, label: "Disaster", color: "#7A55C7", x: 18, y: 80, d: "2.4s" },
  ];
  return (
    <div className="relative select-none" style={{ width: size, height: size }} aria-hidden="true">
      {[1, 0.74, 0.5].map((s, i) => (
        <div key={i} className="absolute rounded-full border border-teal-glow/20" style={{ inset: `${(1 - s) * 50}%`, borderStyle: i === 2 ? "dashed" : "solid" }} />
      ))}
      {/* sweeping beam */}
      <div className="absolute inset-[6%] animate-sweep rounded-full" style={{ background: "conic-gradient(from 0deg, rgba(110,231,226,.28), transparent 22%)" }} />
      {/* connector lines */}
      <svg className="absolute inset-0" viewBox="0 0 100 100" preserveAspectRatio="none">
        {nodes.map((n) => (
          <line key={n.label} x1="50" y1="50" x2={n.x} y2={n.y} stroke="rgba(110,231,226,.35)" strokeWidth=".35" strokeDasharray="1.2 1.2">
            <animate attributeName="stroke-dashoffset" from="0" to="-12" dur="2.5s" repeatCount="indefinite" />
          </line>
        ))}
      </svg>
      {/* pulsing incident */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        {[0, 1, 2].map((i) => <span key={i} className="absolute left-1/2 top-1/2 -ml-12 -mt-12 h-24 w-24 animate-ring rounded-full border-2 border-sos-glow" style={{ animationDelay: `${i}s` }} />)}
        <div className="relative flex h-24 w-24 items-center justify-center rounded-full shadow-[0_0_60px_10px_rgba(200,16,46,.55)]" style={{ backgroundImage: "radial-gradient(circle at 35% 30%,#FF4A64,#C8102E 60%,#8E0A20)" }}>
          <MapPin className="h-11 w-11 text-white" strokeWidth={2.2} />
        </div>
      </div>
      {nodes.map(({ Icon, label, color, x, y, d }) => (
        <div key={label} className="absolute -translate-x-1/2 -translate-y-1/2 animate-float" style={{ left: `${x}%`, top: `${y}%`, animationDelay: d }}>
          <div className="flex flex-col items-center gap-2">
            <div className="flex h-16 w-16 items-center justify-center rounded-full" style={{ background: color, boxShadow: `0 0 34px ${color}aa` }}>
              <Icon className="h-8 w-8 text-white" strokeWidth={2.2} />
            </div>
            <span className="text-sm font-bold text-white/90">{label}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
