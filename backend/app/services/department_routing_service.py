"""
Deterministic department-routing policy (routing-v1).

Input: validated canonical incident facts. Output: for EVERY department, whether it
is included, its role (PRIMARY / SUPPORTING / ESCALATION) and the reasons — exclusions
are explained too. No LLM is involved in this decision.
"""
from __future__ import annotations

from typing import Dict, Any, List

POLICY_VERSION = "routing-v1"
DEPARTMENTS = ("HOSPITAL", "POLICE", "FIRE", "DISASTER")


def decide(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    cat = facts.get("category", "other")
    needs = set(facts.get("needs") or [])
    hazards = set(facts.get("hazards") or [])
    injuries = int(facts.get("injuries") or 0)
    affected = int(facts.get("affected_people") or 0)
    trapped = bool(facts.get("trapped"))
    unconscious = bool(facts.get("unconscious"))
    severity = facts.get("severity", "LOW")
    visual = set(facts.get("visual_findings") or [])  # validated finding codes from images
    sensors = set(facts.get("sensor_types") or [])     # ACCIDENT / FIRE / GAS / FLOOD from qualified IoT alerts
    sensor_severe = bool(facts.get("sensor_severe"))   # device graded the reading HIGH/CRITICAL or impact >= 4 g

    d: Dict[str, Dict[str, Any]] = {k: {"department": k, "included": False, "role": None, "reasons": []}
                                    for k in DEPARTMENTS}

    def inc(dep: str, role: str, reason: str):
        e = d[dep]
        rank = {"PRIMARY": 3, "SUPPORTING": 2, "ESCALATION": 1}
        if not e["included"] or rank[role] > rank.get(e["role"], 0):
            e["role"] = role
        e["included"] = True
        e["reasons"].append(reason)

    # ---- HOSPITAL / ambulance
    if cat == "medical":
        inc("HOSPITAL", "PRIMARY", "Medical emergency reported")
    if unconscious:
        inc("HOSPITAL", "PRIMARY", "Person reported unconscious or not breathing")
    if injuries > 0:
        inc("HOSPITAL", "PRIMARY", f"{injuries} injured reported")
    if "medical" in needs and not d["HOSPITAL"]["included"]:
        inc("HOSPITAL", "PRIMARY", "Medical assistance indicated in report")
    if cat in ("fire", "gas_leak") and affected > 0 and not d["HOSPITAL"]["included"]:
        inc("HOSPITAL", "SUPPORTING", "People present at fire/gas incident: possible smoke or gas exposure")
    if trapped and not d["HOSPITAL"]["included"]:
        inc("HOSPITAL", "SUPPORTING", "Trapped people may need medical care after rescue")
    # Hardware alerts: nobody may be able to call, so dispatch medical help on the sensor alone.
    if "ACCIDENT" in sensors:
        inc("HOSPITAL", "PRIMARY", "Vehicle crash detected by impact sensor: occupants may be injured and unable to call")
    if sensors & {"FIRE", "GAS"} and not d["HOSPITAL"]["included"]:
        inc("HOSPITAL", "SUPPORTING", "Smoke/heat or gas sensor alert: possible burns or smoke/gas exposure")

    # ---- FIRE & rescue
    if cat in ("fire", "gas_leak"):
        inc("FIRE", "PRIMARY", f"{cat.replace('_', ' ').title()} incident")
    if "FIRE" in sensors:
        inc("FIRE", "PRIMARY", "Qualified smoke/temperature sensor alert")
    if "GAS" in sensors:
        inc("FIRE", "PRIMARY", "Qualified gas sensor alert")
    if "ACCIDENT" in sensors and sensor_severe:
        inc("FIRE", "SUPPORTING", "Severe impact detected: possible entrapment, fuel leak or vehicle fire")
    if "FLOOD" in sensors:
        inc("FIRE", "SUPPORTING", "Water-level sensor alert: water rescue may be needed")
    if "visible_flames" in visual or "visible_smoke" in visual:
        inc("FIRE", "PRIMARY" if cat in ("fire", "gas_leak") else "SUPPORTING", "Flames or smoke visible in uploaded image")
    if cat in ("structural_collapse", "rescue"):
        inc("FIRE", "PRIMARY", "Physical rescue required")
    if trapped:
        inc("FIRE", "PRIMARY", "People trapped: extrication/rescue capability needed")
    if hazards & {"fire", "fuel_leak", "chemical", "gas"} and cat not in ("fire", "gas_leak"):
        inc("FIRE", "SUPPORTING", "Hazard reported: " + ", ".join(sorted(hazards & {"fire", "fuel_leak", "chemical", "gas"})))
    if cat == "flood" and ("rescue" in needs or "submerged_vehicle" in visual):
        inc("FIRE", "PRIMARY", "Flood with rescue need")
    if "electrical" in hazards and not d["FIRE"]["included"]:
        inc("FIRE", "SUPPORTING", "Electrical hazard reported")

    # ---- POLICE
    if cat == "road_accident":
        inc("POLICE", "PRIMARY", "Road accident: traffic and scene management")
    if "ACCIDENT" in sensors:
        inc("POLICE", "PRIMARY", "Qualified impact sensor alert on roadway")
    if cat == "security" or "weapon" in hazards or "security" in needs:
        inc("POLICE", "PRIMARY", "Security or threat-related conditions reported")
    if "road_obstruction" in visual and not d["POLICE"]["included"]:
        inc("POLICE", "SUPPORTING", "Road obstruction visible in uploaded image")
    if "evacuation" in needs or (cat in ("fire", "gas_leak", "flood", "structural_collapse") and affected >= 5):
        inc("POLICE", "SUPPORTING", "Evacuation / crowd and traffic control may be needed")
    if cat == "flood" and "traffic" in hazards and not d["POLICE"]["included"]:
        inc("POLICE", "SUPPORTING", "Flooded roadway: traffic diversion")
    if sensors & {"FIRE", "GAS", "FLOOD"} and not d["POLICE"]["included"]:
        inc("POLICE", "SUPPORTING", "Sensor alert: cordon, crowd and traffic control")

    # ---- DISASTER management
    if cat == "flood":
        inc("DISASTER", "PRIMARY", "Flood incident")
    if "FLOOD" in sensors:
        inc("DISASTER", "PRIMARY", "Qualified water-level sensor alert")
    if cat == "structural_collapse" and affected >= 10:
        inc("DISASTER", "SUPPORTING", f"Structural collapse affecting {affected} people")
    if affected >= 20:
        inc("DISASTER", "SUPPORTING", f"Large number of people affected ({affected})")

    # ---- Safety escalation for ambiguous / unmatched incidents
    if not any(e["included"] for e in d.values()):
        inc("POLICE", "ESCALATION", "No specific rule matched: default escalation to police control room for verification")
        if severity in ("HIGH", "CRITICAL") or cat == "sos":
            inc("HOSPITAL", "ESCALATION", "Unclear high-priority/SOS report: precautionary medical escalation")

    # ---- Explain exclusions
    for dep, e in d.items():
        if not e["included"]:
            if dep == "FIRE" and cat == "road_accident":
                e["reasons"].append("Road accident with no fire, fuel leak, hazardous material or entrapment reported")
            elif dep == "HOSPITAL":
                e["reasons"].append("No injuries, medical need or exposure reported")
            elif dep == "DISASTER":
                e["reasons"].append("Not a flood and fewer than 20 people affected")
            else:
                e["reasons"].append(f"No {dep.lower()} criteria met for category '{cat}'")
    return list(d.values())


# ---------------------------------------------------------------------------
# Field-level filtering of the canonical incident record per department
# ---------------------------------------------------------------------------
COMMON_FIELDS = {
    "incident_id", "category", "emergency_type", "priority_score", "severity", "priority_evidence",
    "uncertainties", "status", "source", "created_at", "updated_at", "location", "english_summary",
    "original_language", "routing", "notification", "linked_report_count", "evidence_sources", "injury_certainty",
    "sensor_evidence",  # every service sees what the hardware detected
    "dispatched_to",    # and which other services were alerted (coordination)
    "translation", "reports", "dispatches",
}
DEPARTMENT_FIELDS = {
    "HOSPITAL": COMMON_FIELDS | {"injuries", "injury_certainty", "affected_people", "unconscious", "trapped",
                                 "medical_needs", "exposure_hazards", "image_evidence", "resources", "route"},
    "FIRE": COMMON_FIELDS | {"affected_people", "trapped", "hazards", "sensor_evidence", "image_evidence",
                             "injuries", "resources", "route", "access_notes"},
    "POLICE": COMMON_FIELDS | {"affected_people", "injuries", "traffic_hazards", "security_hazards",
                               "image_evidence", "resources", "route"},
    "DISASTER": COMMON_FIELDS | {"affected_people", "injuries", "trapped", "hazards", "sensor_evidence",
                                 "image_evidence", "resources", "route"},
}
IMAGE_FINDINGS_BY_DEPT = {
    "HOSPITAL": {"visible_person", "person_on_ground", "visible_smoke", "visible_flames", "damaged_vehicle"},
    "FIRE": None,  # all findings
    "POLICE": {"damaged_vehicle", "vehicle_collision", "road_obstruction", "multiple_vehicles", "crowd",
               "visible_flames", "visible_smoke", "blocked_exit"},
    "DISASTER": None,
}


def filter_for_department(full: Dict[str, Any], department: str) -> Dict[str, Any]:
    if department == "ADMIN":
        return full
    allowed = DEPARTMENT_FIELDS[department]
    out = {k: v for k, v in full.items() if k in allowed}
    hz = set(full.get("hazards") or [])
    if department == "HOSPITAL":
        out["medical_needs"] = [n for n in full.get("needs", []) if n in ("medical", "rescue")]
        out["exposure_hazards"] = sorted(hz & {"smoke", "gas", "chemical", "fire"})
    if department == "POLICE":
        out["traffic_hazards"] = sorted(hz & {"traffic", "structural", "fuel_leak", "flood_water"})
        out["security_hazards"] = sorted(hz & {"weapon"})
    allowed_findings = IMAGE_FINDINGS_BY_DEPT[department]
    if "image_evidence" in out:
        imgs = []
        for img in full.get("image_evidence") or []:
            img = dict(img)
            if allowed_findings is not None:
                img["findings"] = [f for f in img.get("findings", []) if f.get("finding") in allowed_findings]
            imgs.append(img)
        out["image_evidence"] = imgs
    if "resources" in out:
        wanted = {"HOSPITAL": {"HOSPITAL", "AMBULANCE"}, "FIRE": {"FIRE"}, "POLICE": {"POLICE"},
                  "DISASTER": {"DISASTER", "SHELTER", "FIRE"}}[department]
        out["resources"] = [r for r in full.get("resources") or [] if r.get("type") in wanted]
    out["routing"] = next((r for r in full.get("routing") or [] if r["department"] == department), None)
    out["notification"] = next((n for n in full.get("notifications") or [] if n["department"] == department), None)
    if "reports" in out:  # originals stay admin-only; services read the English text
        out["reports"] = [{k: v for k, v in r.items() if k != "original_text"} for r in out["reports"]]
    out["department_view"] = department
    return out
