"""
Unit dispatch: which ambulance / fire tender / patrol / rescue team goes, how far away it is,
when it should arrive, and where it is now.

- Candidates are the department's AVAILABLE units, nearest first. ETAs come from the road router
  (OSRM) when it answers, otherwise a clearly-labelled straight-line estimate.
- Auto-dispatch (AUTO_DISPATCH=true): sensor alerts and HIGH/CRITICAL incidents get the nearest
  unit of every PRIMARY department (and SUPPORTING ones when CRITICAL) without waiting for a
  human. Control rooms can cancel or reassign; every action is in the history and audit log.
- Unit position: crew phone GPS when shared (crew page), otherwise the station. With
  DEMO_SIMULATE_UNITS the unit moves along its route so the demo shows arrival; the UI labels it.
"""
from __future__ import annotations

import hashlib
import math
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.dispatch import ResponseUnit, Dispatch, ACTIVE_DISPATCH, UNIT_DEPARTMENT
from app.models.incident import EmergencyReport
from app.models.operations import IncidentUpdate
from app.models.resource import EmergencyResource

UNIT_LABEL = {"AMBULANCE": "Ambulance", "FIRE_TENDER": "Fire tender", "RESCUE_TENDER": "Rescue tender",
              "POLICE_PATROL": "Police patrol", "HIGHWAY_PATROL": "Highway patrol",
              "DISASTER_TEAM": "Disaster response team", "RESCUE_BOAT": "Rescue boat team"}
# Which unit types a department prefers for a category (first match wins; any unit of the department otherwise)
PREFERRED = {
    ("FIRE", "road_accident"): ("RESCUE_TENDER", "FIRE_TENDER"),
    ("FIRE", "rescue"): ("RESCUE_TENDER", "FIRE_TENDER"),
    ("FIRE", "structural_collapse"): ("RESCUE_TENDER", "FIRE_TENDER"),
    ("FIRE", "fire"): ("FIRE_TENDER", "RESCUE_TENDER"),
    ("POLICE", "road_accident"): ("HIGHWAY_PATROL", "POLICE_PATROL"),
    ("DISASTER", "flood"): ("RESCUE_BOAT", "DISASTER_TEAM"),
}
NEXT_STATUS = {  # allowed forward moves
    "ASSIGNED": {"EN_ROUTE", "ON_SCENE", "CANCELLED"},
    "EN_ROUTE": {"ON_SCENE", "CANCELLED"},
    "ON_SCENE": {"TRANSPORTING", "COMPLETED", "CANCELLED"},
    "TRANSPORTING": {"AT_HOSPITAL", "COMPLETED"},
    "AT_HOSPITAL": {"COMPLETED"},
}
UNIT_STATUS_FOR = {"ASSIGNED": "ASSIGNED", "EN_ROUTE": "EN_ROUTE", "ON_SCENE": "ON_SCENE",
                   "TRANSPORTING": "TRANSPORTING", "AT_HOSPITAL": "TRANSPORTING"}
STRAIGHT_LINE_FACTOR, FALLBACK_KMH = 1.4, 35.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(t: Optional[datetime]) -> Optional[datetime]:
    return t if t is None or t.tzinfo else t.replace(tzinfo=timezone.utc)


def haversine_km(a_lat, a_lng, b_lat, b_lng) -> float:
    r = 6371.0
    dlat, dlng = math.radians(b_lat - a_lat), math.radians(b_lng - a_lng)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(dlng / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def _along(route: List[List[float]], frac: float) -> Tuple[float, float]:
    """Point at `frac` (0..1) of the way along a polyline [[lat, lng], ...]."""
    if not route:
        raise ValueError("empty route")
    if len(route) == 1 or frac <= 0:
        return route[0][0], route[0][1]
    if frac >= 1:
        return route[-1][0], route[-1][1]
    seg = [haversine_km(*route[i], *route[i + 1]) for i in range(len(route) - 1)]
    target, acc = sum(seg) * frac, 0.0
    for i, d in enumerate(seg):
        if acc + d >= target and d > 0:
            t = (target - acc) / d
            return (route[i][0] + (route[i + 1][0] - route[i][0]) * t,
                    route[i][1] + (route[i + 1][1] - route[i][1]) * t)
        acc += d
    return route[-1][0], route[-1][1]


class DispatchService:
    # ------------------------------------------------------------- estimates
    @staticmethod
    def _estimate(o_lat, o_lng, d_lat, d_lng, with_road: bool) -> Dict[str, Any]:
        straight = haversine_km(o_lat, o_lng, d_lat, d_lng)
        if with_road:
            try:
                from app.services.routing_service import RoutingService
                r = RoutingService.calculate_route(o_lat, o_lng, d_lat, d_lng)
                if r.available and r.coordinates:
                    return {"distance_km": round(r.distance_km, 1), "eta_min": round(r.eta_min or 1, 1),
                            "eta_source": "ROAD_ROUTE", "route": r.coordinates}
            except Exception as e:
                logger.info(f"road route unavailable for dispatch: {e}")
        km = straight * STRAIGHT_LINE_FACTOR
        return {"distance_km": round(km, 1), "eta_min": round(max(1.0, km / FALLBACK_KMH * 60 + 1), 1),
                "eta_source": "STRAIGHT_LINE_ESTIMATE", "route": [[o_lat, o_lng], [d_lat, d_lng]]}

    # ------------------------------------------------------------ candidates
    @classmethod
    def candidates(cls, db: Session, inc: EmergencyReport, department: str, limit: int = 5,
                   with_road: bool = True) -> List[Dict[str, Any]]:
        if inc.latitude is None:
            return []
        units = db.query(ResponseUnit).filter(ResponseUnit.department == department, ResponseUnit.active.is_(True),
                                              ResponseUnit.status == "AVAILABLE",
                                              ResponseUnit.latitude.isnot(None)).all()
        pref = PREFERRED.get((department, inc.category or ""), ())
        rank = lambda u: (pref.index(u.unit_type) if u.unit_type in pref else len(pref))
        scored = sorted(units, key=lambda u: haversine_km(u.latitude, u.longitude, inc.latitude, inc.longitude))[:limit]
        out = []
        for i, u in enumerate(scored):
            est = cls._estimate(u.latitude, u.longitude, inc.latitude, inc.longitude, with_road and i < 3)
            out.append({**cls.unit_dict(u), "distance_km": est["distance_km"], "eta_min": est["eta_min"],
                        "eta_source": est["eta_source"], "preferred_type": bool(pref) and u.unit_type == pref[0], "_rank": rank(u)})
        # Nearest first; a better-suited unit type (e.g. rescue tender for a crash) goes first only
        # when it is at most 5 minutes slower than the nearest unit.
        out.sort(key=lambda c: c["eta_min"])
        if out:
            fastest = out[0]["eta_min"]
            out.sort(key=lambda c: (0 if c["preferred_type"] and c["eta_min"] <= fastest + 5 else 1, c["eta_min"]))
        for c in out:
            c.pop("_rank")
        return out

    # --------------------------------------------------------------- actions
    @classmethod
    def dispatch(cls, db: Session, inc: EmergencyReport, unit: ResponseUnit, actor: str, auto: bool = False,
                 with_road: bool = True) -> Dispatch:
        est = cls._estimate(unit.latitude, unit.longitude, inc.latitude, inc.longitude, with_road)
        dest = None
        if unit.unit_type == "AMBULANCE":
            h = (db.query(EmergencyResource).filter(EmergencyResource.resource_type == "HOSPITAL").all())
            if h:
                dest = min(h, key=lambda r: haversine_km(r.latitude, r.longitude, inc.latitude, inc.longitude)).id
        now = _now()
        d = Dispatch(incident_id=inc.id, unit_id=unit.id, department=unit.department, status="ASSIGNED", auto=auto,
                     assigned_by=actor, origin_lat=unit.latitude, origin_lng=unit.longitude,
                     distance_km=est["distance_km"], eta_min=est["eta_min"], eta_source=est["eta_source"],
                     route=est["route"], destination_resource_id=dest, assigned_at=now,
                     history=[{"status": "ASSIGNED", "at": now.isoformat(), "by": actor}])
        unit.status = "ASSIGNED"
        db.add(d)
        if inc.status in ("REPORTED", "ACKNOWLEDGED"):
            inc.status = "RESPONDING"
        db.add(IncidentUpdate(incident_id=inc.id, actor_label=actor, department=unit.department, status="UNIT_ASSIGNED",
                              note=f"{UNIT_LABEL.get(unit.unit_type, unit.unit_type)} {unit.call_sign} assigned, "
                                   f"about {round(est['eta_min'])} min away", public=False))
        db.flush()
        return d

    @classmethod
    def set_status(cls, db: Session, d: Dispatch, status: str, actor: str) -> Dispatch:
        status = status.upper()
        if status == d.status:
            return d
        if status not in NEXT_STATUS.get(d.status, set()):
            raise ValueError(f"Cannot move a dispatch from {d.status} to {status}")
        now = _now()
        unit, inc = d.unit, d.incident
        if status == "EN_ROUTE":
            d.en_route_at = now
        elif status == "ON_SCENE":
            d.on_scene_at = now
            d.en_route_at = d.en_route_at or now
            if unit.position_source != "CREW_GPS":
                unit.latitude, unit.longitude = inc.latitude, inc.longitude
            if inc.status in ("REPORTED", "ACKNOWLEDGED", "RESPONDING"):
                inc.status = "ON_SCENE"
        elif status == "TRANSPORTING":
            d.transporting_at = now
        elif status in ("COMPLETED", "CANCELLED"):
            d.completed_at = now
        d.status = status
        d.history = list(d.history or []) + [{"status": status, "at": now.isoformat(), "by": actor}]
        if status in ("COMPLETED", "CANCELLED"):
            unit.status = "AVAILABLE"
            base = db.get(EmergencyResource, unit.base_resource_id) if unit.base_resource_id else None
            if base and unit.position_source != "CREW_GPS":  # demo units return to their station
                unit.latitude, unit.longitude = base.latitude, base.longitude
        else:
            unit.status = UNIT_STATUS_FOR.get(status, unit.status)
        label = UNIT_LABEL.get(unit.unit_type, unit.unit_type)
        db.add(IncidentUpdate(incident_id=inc.id, actor_label=actor, department=d.department, status=f"UNIT_{status}",
                              note=f"{label} {unit.call_sign}: {status.replace('_', ' ').lower()}", public=False))
        db.flush()
        return d

    @classmethod
    def auto_dispatch(cls, db: Session, inc: EmergencyReport) -> List[Dispatch]:
        """Nearest unit for every PRIMARY department (and SUPPORTING when CRITICAL) of sensor alerts
        and HIGH/CRITICAL incidents. Idempotent: skips departments that already have an active unit."""
        if not settings.AUTO_DISPATCH or inc.latitude is None or inc.merged_into_id:
            return []
        if inc.status in ("RESOLVED", "CLOSED", "FALSE_ALARM"):
            return []
        ass = inc.severity_assessments[0] if inc.severity_assessments else None
        severity = ass.severity if ass else "LOW"
        from_sensor = inc.source == "IOT" or bool(inc.sensor_readings)
        if not (from_sensor or severity in ("HIGH", "CRITICAL")):
            return []
        active = {d.department for d in inc.dispatches if d.status in ACTIVE_DISPATCH}
        made = []
        for dec in inc.routing_decisions:
            if dec.superseded or not dec.included or dec.department in active:
                continue
            if dec.role_in_response != "PRIMARY" and severity != "CRITICAL":
                continue
            cands = cls.candidates(db, inc, dec.department, limit=3, with_road=False)
            cands = [c for c in cands if c["distance_km"] <= settings.AUTO_DISPATCH_MAX_KM * STRAIGHT_LINE_FACTOR]
            if not cands:
                continue
            unit = db.get(ResponseUnit, cands[0]["id"])
            made.append(cls.dispatch(db, inc, unit, "RESQ.AI auto-dispatch (rules)", auto=True, with_road=False))
        return made

    # ------------------------------------------------------- live position
    @classmethod
    def tick(cls, db: Session, d: Dispatch) -> None:
        """Advance the demo simulation for units without live crew GPS (no-op otherwise)."""
        if not settings.DEMO_SIMULATE_UNITS or d.status not in ("ASSIGNED", "EN_ROUTE"):
            return
        unit = d.unit
        gps_fresh = unit.position_source == "CREW_GPS" and unit.position_at and \
            _now() - _aware(unit.position_at) < timedelta(minutes=2)
        if gps_fresh:
            return
        speed = max(1.0, settings.DEMO_SIM_SPEED)
        if d.status == "ASSIGNED" and (_now() - _aware(d.assigned_at)).total_seconds() * speed >= 60:
            cls.set_status(db, d, "EN_ROUTE", "crew (demo simulation)")
        if d.status == "EN_ROUTE" and d.en_route_at and d.eta_min:
            if (_now() - _aware(d.en_route_at)).total_seconds() * speed >= d.eta_min * 60:
                cls.set_status(db, d, "ON_SCENE", "crew (demo simulation)")

    @classmethod
    def live(cls, d: Dispatch) -> Dict[str, Any]:
        """Current position, progress and remaining minutes for a dispatch."""
        unit = d.unit
        speed = max(1.0, settings.DEMO_SIM_SPEED) if settings.DEMO_SIMULATE_UNITS else 1.0
        gps = unit.position_source == "CREW_GPS" and unit.position_at and _now() - _aware(unit.position_at) < timedelta(minutes=2)
        if d.status in ("ON_SCENE", "TRANSPORTING", "AT_HOSPITAL", "COMPLETED"):
            frac = 1.0
        elif d.status == "EN_ROUTE" and d.en_route_at and d.eta_min:
            frac = min(1.0, (_now() - _aware(d.en_route_at)).total_seconds() * (speed if not gps else 1) / (d.eta_min * 60))
        else:
            frac = 0.0
        if gps:
            lat, lng, src = unit.latitude, unit.longitude, "CREW_GPS"
            if d.status == "EN_ROUTE" and d.incident.latitude is not None and d.distance_km:
                left = haversine_km(lat, lng, d.incident.latitude, d.incident.longitude) * STRAIGHT_LINE_FACTOR
                frac = max(0.0, min(1.0, 1 - left / max(d.distance_km, 0.1)))
        elif settings.DEMO_SIMULATE_UNITS and d.route and d.status in ("EN_ROUTE", "ON_SCENE"):
            lat, lng = _along(d.route, frac)
            src = "SIMULATED"
        else:
            lat, lng, src = unit.latitude, unit.longitude, "STATION" if d.status == "ASSIGNED" else unit.position_source
        remaining = None
        if d.status in ("ASSIGNED", "EN_ROUTE") and d.eta_min:
            remaining = max(0, math.ceil(d.eta_min * (1 - frac)))
        return {"latitude": lat, "longitude": lng, "position_source": src, "progress": round(frac, 3),
                "eta_remaining_min": remaining, "simulation_speed": speed if src == "SIMULATED" else None}

    # ------------------------------------------------------------- views
    @staticmethod
    def unit_dict(u: ResponseUnit) -> Dict[str, Any]:
        from sqlalchemy.orm import object_session
        sess = object_session(u)
        base = sess.get(EmergencyResource, u.base_resource_id) if (sess and u.base_resource_id) else None
        return {"id": u.id, "call_sign": u.call_sign, "unit_type": u.unit_type,
                "base_name": base.name if base else None, "base_source": base.data_source if base else None,
                "unit_label": UNIT_LABEL.get(u.unit_type, u.unit_type), "department": u.department,
                "status": u.status, "latitude": u.latitude, "longitude": u.longitude,
                "position_source": u.position_source, "capabilities": u.capabilities or [],
                "base": u.base_resource_id, "demo": u.data_source == "DEMO_SEED"}

    @classmethod
    def control_dict(cls, db: Session, d: Dispatch) -> Dict[str, Any]:
        dest = db.get(EmergencyResource, d.destination_resource_id) if d.destination_resource_id else None
        return {"id": d.id, "incident_id": d.incident_id, "department": d.department, "status": d.status,
                "auto": d.auto, "assigned_by": d.assigned_by, "unit": cls.unit_dict(d.unit),
                "distance_km": d.distance_km, "eta_min": d.eta_min, "eta_source": d.eta_source,
                "route": d.route if d.status in ("ASSIGNED", "EN_ROUTE") else None,
                "assigned_at": d.assigned_at, "en_route_at": d.en_route_at, "on_scene_at": d.on_scene_at,
                "transporting_at": d.transporting_at, "completed_at": d.completed_at,
                "destination": ({"id": dest.id, "name": dest.name, "latitude": dest.latitude, "longitude": dest.longitude}
                                if dest else None),
                "history": d.history or [], "live": cls.live(d)}

    @classmethod
    def citizen_dict(cls, d: Dispatch) -> Dict[str, Any]:
        live = cls.live(d)
        return {"unit_type": d.unit.unit_type, "call_sign": d.unit.call_sign, "department": d.department,
                "status": d.status, "eta_remaining_min": live["eta_remaining_min"],
                "latitude": live["latitude"], "longitude": live["longitude"],
                "position_source": live["position_source"], "progress": live["progress"],
                "assigned_at": d.assigned_at, "on_scene_at": d.on_scene_at}

    _route_tried: set = set()

    @classmethod
    def refine_route(cls, d: Dispatch) -> None:
        """Auto-dispatch starts with a straight-line estimate (instant); swap in the road route once."""
        if d.eta_source != "STRAIGHT_LINE_ESTIMATE" or d.status != "ASSIGNED" or d.id in cls._route_tried:
            return
        cls._route_tried.add(d.id)
        if d.origin_lat is None or d.incident.latitude is None:
            return
        est = cls._estimate(d.origin_lat, d.origin_lng, d.incident.latitude, d.incident.longitude, True)
        if est["eta_source"] == "ROAD_ROUTE":
            d.distance_km, d.eta_min, d.eta_source, d.route = est["distance_km"], est["eta_min"], "ROAD_ROUTE", est["route"]

    @classmethod
    def active_and_recent(cls, db: Session, inc: EmergencyReport, refine: bool = False) -> List[Dispatch]:
        """refine=True (control-room detail only) swaps straight-line estimates for road routes.
        Network calls happen before any write so no row lock is held while waiting on the router."""
        if refine:
            pending = [d for d in inc.dispatches if d.eta_source == "STRAIGHT_LINE_ESTIMATE" and d.status == "ASSIGNED"
                       and d.id not in cls._route_tried and d.origin_lat is not None and inc.latitude is not None]
            results = {}
            for d in pending:
                cls._route_tried.add(d.id)
                results[d.id] = cls._estimate(d.origin_lat, d.origin_lng, inc.latitude, inc.longitude, True)
            for d in pending:
                est = results[d.id]
                if est["eta_source"] == "ROAD_ROUTE":
                    d.distance_km, d.eta_min, d.eta_source, d.route = est["distance_km"], est["eta_min"], "ROAD_ROUTE", est["route"]
        out = []
        for d in inc.dispatches:
            if d.status == "CANCELLED":
                continue
            try:
                cls.tick(db, d)
            except Exception as e:
                logger.info(f"dispatch tick failed: {e}")
            out.append(d)
        if db.dirty:
            db.commit()
        return out

    # ------------------------------------------------------------- crew
    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def new_crew_token(cls, unit: ResponseUnit) -> str:
        token = secrets.token_urlsafe(18)
        unit.crew_token_hash = cls.hash_token(token)
        return token

    @classmethod
    def crew_unit(cls, db: Session, unit_id: str, token: Optional[str]) -> Optional[ResponseUnit]:
        u = db.get(ResponseUnit, unit_id)
        if not u or not token or not u.crew_token_hash:
            return None
        return u if secrets.compare_digest(u.crew_token_hash, cls.hash_token(token)) else None

    @staticmethod
    def current_for_unit(db: Session, unit: ResponseUnit) -> Optional[Dispatch]:
        return (db.query(Dispatch).filter(Dispatch.unit_id == unit.id, Dispatch.status.in_(ACTIVE_DISPATCH))
                .order_by(Dispatch.assigned_at.desc()).first())
