"""
Response Copilot: English responder briefs built from the validated canonical record.
`facts` come only from validated data (record, sensors, images, routing provider).
`suggestions` are rule-based operational prompts for trained personnel, clearly separated.
The copilot never confirms dispatch or assigns resources.
"""
from __future__ import annotations

from typing import Dict, Any, List

CHECKLISTS = {
    "HOSPITAL": {
        "base": ["Confirm patient count and condition with first responders on scene.",
                 "Prepare emergency department to receive the reported number of patients."],
        "trapped": ["Expect delayed arrival: patients may need extrication first."],
        "exposure": ["Prepare for possible smoke or gas exposure cases."],
        "unconscious": ["Prepare for a patient reported unconscious or not breathing."],
    },
    "POLICE": {
        "base": ["Secure the scene and keep an access lane open for ambulances and fire tenders."],
        "road_accident": ["Set up traffic diversion upstream of the incident."],
        "evacuation": ["Support evacuation and crowd control."],
        "security": ["Treat as a potential threat: assess before approach."],
    },
    "FIRE": {
        "base": ["Verify the hazard on arrival and establish a safety perimeter."],
        "trapped": ["Bring rescue/extrication equipment: people reported trapped."],
        "gas": ["Approach from upwind; eliminate ignition sources."],
        "flood": ["Bring water-rescue equipment."],
    },
    "DISASTER": {
        "base": ["Assess scale and need for shelters or evacuation support."],
        "flood": ["Check rainfall/water-level trend and nearby low-lying areas."],
    },
}
EQUIPMENT = {
    "HOSPITAL": ["Ambulance (ALS/BLS per local protocol)"],
    "POLICE": ["Patrol vehicle", "Traffic cones / barricades"],
    "FIRE": ["Fire tender"],
    "DISASTER": ["Rapid assessment team"],
}


class ResponseCopilot:
    @staticmethod
    def brief(view: Dict[str, Any]) -> Dict[str, Any]:
        dep = view["department_view"]
        cat = view.get("category", "other")
        hazards = set(view.get("hazards") or []) | set(view.get("exposure_hazards") or []) | set(view.get("traffic_hazards") or [])
        loc = view.get("location") or {}
        facts: List[Dict[str, str]] = [
            {"label": "Incident", "value": f"{view.get('emergency_type')} — priority {view.get('priority_score')}/100 ({view.get('severity')})",
             "source": "priority engine " + str((view.get('priority_evidence') or {}).get('version', ''))},
            {"label": "Location", "value": (f"{loc.get('label')} ({loc.get('latitude')}, {loc.get('longitude')})"
                                             if loc.get("latitude") is not None else f"{loc.get('label')} — coordinates not available"),
             "source": f"{(loc.get('source') or 'unknown').lower().replace('_', ' ')}, {'verified' if loc.get('verified') else 'NOT verified'}"},
            {"label": "Report (English)", "value": view.get("english_summary") or "Translation unavailable — see original language",
             "source": "citizen report" if view.get("source") == "USER" else "sensor event"},
        ]
        if "injuries" in view:
            facts.append({"label": "Reported injuries", "value": f"{view.get('injuries')} ({view.get('injury_certainty', 'unknown')})", "source": "citizen report"})
        if view.get("trapped"):
            facts.append({"label": "Entrapment", "value": "People reported trapped", "source": "citizen report"})
        for s in view.get("sensor_evidence") or []:
            facts.append({"label": f"Sensor {s.get('device_id')}", "value": f"{s.get('reason')}: {s.get('observed_value')} {s.get('unit') or ''} (threshold {s.get('threshold_value')})",
                          "source": f"IoT at {s.get('timestamp')}"})
        for img in view.get("image_evidence") or []:
            for f in img.get("findings", [])[:4]:
                facts.append({"label": "Image finding", "value": f"{f['finding']} ({f['confidence_level']} model confidence)",
                              "source": f"vision model, image {img['id'][:8]}{' — needs review' if img.get('recommended_review') else ''}"})
        route = view.get("route")
        if route and route.get("available"):
            facts.append({"label": "Route", "value": f"{route['distance_km']} km, ETA {route['eta_min']} min from {route['origin_name']}",
                          "source": route["provider"]})
        elif route:
            facts.append({"label": "Route", "value": "Routing unavailable — " + (route.get("message") or ""), "source": route.get("provider", "routing")})

        c = CHECKLISTS.get(dep, {})
        sugg = list(c.get("base", []))
        if view.get("trapped") and "trapped" in c: sugg += c["trapped"]
        if hazards & {"smoke", "gas", "chemical"} and "exposure" in c: sugg += c["exposure"]
        if view.get("unconscious") and "unconscious" in c: sugg += c["unconscious"]
        if cat == "road_accident" and "road_accident" in c: sugg += c["road_accident"]
        if cat in ("gas_leak",) or "gas" in hazards:
            sugg += c.get("gas", [])
        if cat == "flood": sugg += c.get("flood", [])
        if cat == "security": sugg += c.get("security", [])
        if (view.get("affected_people") or 0) >= 5: sugg += c.get("evacuation", [])
        return {
            "department": dep,
            "facts": facts,
            "suggestions": sugg,
            "suggested_equipment": EQUIPMENT.get(dep, []),
            "uncertainties": view.get("uncertainties") or [],
            "knowledge_excerpts": view.get("knowledge_excerpts") or [],
            "notice": "Suggestions are rule-based prompts for trained personnel. They are not dispatch orders.",
        }

    @staticmethod
    def standalone_brief(role: str, category: str, injuries: int, affected: int, indicators: List[str], priority: int) -> Dict[str, Any]:
        ind = " ".join(indicators or []).lower()
        view = {"department_view": role if role in CHECKLISTS else "POLICE", "category": category,
                "trapped": "trapped" in ind, "unconscious": "unconscious" in ind, "affected_people": affected,
                "hazards": ["gas"] if "gas" in ind or "smoke" in ind else []}
        b = ResponseCopilot.brief({**view, "priority_score": priority, "severity": "", "emergency_type": category})
        return {
            "summary": f"{category.replace('_', ' ')} — priority {priority}/100, {injuries} injured reported, {affected} affected.",
            "recommendation": b["suggestions"][0] if b["suggestions"] else "Verify incident details.",
            "operational_checklist": b["suggestions"],
            "required_services": [], "required_equipment": b["suggested_equipment"],
            "missing_information": ["Scene conditions not yet verified by responders"], "language": "en",
        }
