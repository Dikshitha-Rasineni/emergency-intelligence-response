export const SEVERITY_CLASS: Record<string, string> = {
  CRITICAL: "bg-pri-critical text-white", HIGH: "bg-pri-high text-white",
  MODERATE: "bg-pri-moderate text-white", LOW: "bg-pri-low text-white",
};
export const SEVERITY_TEXT: Record<string, string> = {
  CRITICAL: "text-pri-critical", HIGH: "text-pri-high", MODERATE: "text-pri-moderate", LOW: "text-pri-low",
};
export function timeAgo(iso?: string | null) {
  if (!iso) return "";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${Math.round(s)}s ago`;
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 86400) return `${Math.round(s / 3600)} h ago`;
  return new Date(iso).toLocaleDateString();
}
export function clock(iso?: string | null) {
  return iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "";
}
export const DEPT_LABEL: Record<string, string> = { HOSPITAL: "Hospital / EMS", POLICE: "Police", FIRE: "Fire & rescue", DISASTER: "Disaster response", ADMIN: "Administration" };
export const CATEGORY_LABEL: Record<string, string> = {
  road_accident: "Road accident", fire: "Fire", gas_leak: "Smoke or gas leak", flood: "Flood", medical: "Medical emergency",
  structural_collapse: "Structural collapse", rescue: "Rescue required", security: "Security threat", sos: "SOS", other: "Other emergency",
};
