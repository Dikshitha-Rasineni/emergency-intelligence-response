"""
Import REAL Chennai hospitals, fire stations, police stations and ambulance stations from OpenStreetMap.

Data: OpenStreetMap contributors, ODbL (https://www.openstreetmap.org/copyright), via the Overpass API.
Imported facilities get data_source="OSM", verified=False and availability UNKNOWN: OpenStreetMap
says where a facility is, not whether it has a free bed or a vehicle. Phone numbers are stored but
not shown (only verified facilities show phones).

Usage (run AFTER `python -m app.db.seed_demo_data --reset`):
  python -m app.db.import_osm_facilities                    # download, import, move demo units to real stations
  python -m app.db.import_osm_facilities --keep-demo        # keep the fictional demo facilities too
  python -m app.db.import_osm_facilities --from-file x.json # import a saved Overpass response (offline)
  python -m app.db.import_osm_facilities --bbox 12.75,79.95,13.25,80.35   # south,west,north,east

A copy of the downloaded data is saved to datasets/osm_chennai_facilities.json so it can be
re-imported offline (--from-file).
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Optional, Tuple

import httpx

from app.db.session import SessionLocal
from app.models.resource import EmergencyResource, ResourceAvailability

CHENNAI_BBOX = (12.75, 79.95, 13.25, 80.35)  # south, west, north, east (Chennai + Chengalpattu GST corridor)
ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
             "https://overpass.private.coffee/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
HEADERS = {"User-Agent": "RESQ.AI/2.0 (student emergency-response project; one-time import)"}
SNAPSHOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets", "osm_chennai_facilities.json")

# OSM tag -> RESQ.AI resource type, capabilities
KINDS = [
    (("amenity", "hospital"), "HOSPITAL", ["Hospital (OpenStreetMap)"]),
    (("amenity", "fire_station"), "FIRE", ["Fire station (OpenStreetMap)"]),
    (("amenity", "police"), "POLICE", ["Police station (OpenStreetMap)"]),
    (("emergency", "ambulance_station"), "AMBULANCE", ["Ambulance station (OpenStreetMap)"]),
]
UNIT_BASE_TYPE = {"AMBULANCE": ("AMBULANCE", "HOSPITAL"), "FIRE_TENDER": ("FIRE",), "RESCUE_TENDER": ("FIRE",),
                  "POLICE_PATROL": ("POLICE",), "HIGHWAY_PATROL": ("POLICE",)}
ORG_TYPE = {"HOSPITAL": "HOSPITAL", "FIRE": "FIRE", "POLICE": "POLICE"}


def _query(bbox, kind) -> str:
    s, w, n, e = bbox
    (k, v), _, _ = kind
    return f'[out:json][timeout:60];nwr["{k}"="{v}"]({s},{w},{n},{e});out center tags;'


def download(bbox) -> Dict:
    """One small query per facility kind (busy public servers handle these far better than one big one),
    each tried on every mirror, with two rounds of retries."""
    import time
    elements = []
    for kind in KINDS:
        label = kind[1].lower()
        got = None
        for attempt in range(3):
            for url in ENDPOINTS:
                try:
                    print(f"[osm] {label}: {url.split('/')[2]} …", flush=True)
                    with httpx.Client(timeout=httpx.Timeout(45, connect=10), headers=HEADERS) as c:
                        r = c.post(url, data={"data": _query(bbox, kind)})
                    r.raise_for_status()
                    got = r.json().get("elements")
                    if got is not None:
                        break
                except Exception as e:
                    print(f"[osm]   busy or unreachable ({type(e).__name__}); trying next server", flush=True)
            if got is not None:
                break
            print(f"[osm]   all servers busy; waiting {10 * (attempt + 1)} s before retrying", flush=True)
            time.sleep(10 * (attempt + 1))
        if got is None:
            raise SystemExit("[osm] OpenStreetMap servers are too busy right now. Nothing was changed; "
                             "the app keeps working with its current facilities. Try again in a few minutes.")
        print(f"[osm]   {len(got)} {label} found", flush=True)
        elements += got
    return {"elements": elements}


def _hav(a_lat, a_lng, b_lat, b_lng) -> float:
    r = 6371.0
    dlat, dlng = math.radians(b_lat - a_lat), math.radians(b_lng - a_lng)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(dlng / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def parse(data: Dict) -> List[Dict]:
    out, seen = [], set()
    for el in data.get("elements", []):
        tags = el.get("tags") or {}
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lng = el.get("lon") or (el.get("center") or {}).get("lon")
        name = (tags.get("name:en") or tags.get("name") or "").strip()
        if lat is None or lng is None or not name:
            continue  # unnamed points are not useful to a dispatcher
        kind = next(((t, caps) for (k, v), t, caps in KINDS if tags.get(k) == v), None)
        if not kind:
            continue
        rtype, caps = kind
        if rtype == "HOSPITAL" and tags.get("healthcare") == "clinic":
            continue
        key = (rtype, name.lower(), round(lat, 3), round(lng, 3))
        if key in seen:
            continue
        seen.add(key)
        if tags.get("emergency") == "yes" and rtype == "HOSPITAL":
            caps = caps + ["Emergency department (per OSM)"]
        addr = ", ".join(x for x in (tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:suburb"),
                                     tags.get("addr:city"), tags.get("addr:postcode")) if x) or None
        out.append({"id": f"OSM-{el['type'][0].upper()}{el['id']}", "name": name[:150], "type": rtype,
                    "lat": float(lat), "lng": float(lng), "address": addr,
                    "phone": (tags.get("phone") or tags.get("contact:phone") or None), "caps": caps})
    return out


def import_rows(rows: List[Dict], keep_demo: bool) -> Tuple[int, int]:
    db = SessionLocal()
    try:
        n = 0
        for r in rows:
            res = db.get(EmergencyResource, r["id"]) or EmergencyResource(id=r["id"])
            res.name, res.resource_type, res.latitude, res.longitude = r["name"], r["type"], r["lat"], r["lng"]
            res.address = r["address"] or "Address not listed in OpenStreetMap"
            res.phone = (r["phone"] or "")[:50] or None
            res.capabilities, res.verified, res.data_source = r["caps"], False, "OSM"
            db.add(res)
            if not res.availability:
                db.add(ResourceAvailability(resource_id=r["id"], status="UNKNOWN", verified=False, available_units=0))
            n += 1
        db.flush()

        # Move demo units to the nearest REAL station of the right kind, so dispatch starts from real places.
        from app.models.dispatch import ResponseUnit
        from app.models.user import Organization
        real = db.query(EmergencyResource).filter(EmergencyResource.data_source == "OSM").all()
        moved = 0
        used: Dict[str, int] = {}
        for u in db.query(ResponseUnit).filter(ResponseUnit.data_source == "DEMO_SEED").all():
            kinds = UNIT_BASE_TYPE.get(u.unit_type)
            old = db.get(EmergencyResource, u.base_resource_id) if u.base_resource_id else None
            if not kinds or not old:
                continue
            cands = [x for x in real if x.resource_type in kinds]
            if not cands:
                continue
            # nearest real station to the old demo base; spread units so two do not share one station
            best = min(cands, key=lambda x: _hav(old.latitude, old.longitude, x.latitude, x.longitude) + used.get(x.id, 0) * 2.0)
            used[best.id] = used.get(best.id, 0) + 1
            u.base_resource_id = best.id
            if u.status == "AVAILABLE":
                u.latitude, u.longitude, u.position_source = best.latitude, best.longitude, "STATION"
            moved += 1
        for org in db.query(Organization).all():
            t = ORG_TYPE.get(org.department)
            old = db.get(EmergencyResource, org.resource_id) if org.resource_id else None
            cands = [x for x in real if x.resource_type == t]
            if t and old and cands:
                org.resource_id = min(cands, key=lambda x: _hav(old.latitude, old.longitude, x.latitude, x.longitude)).id
        db.flush()

        if not keep_demo:  # hide fictional facilities that now have real equivalents
            real_types = {x.resource_type for x in real}
            for d in db.query(EmergencyResource).filter(EmergencyResource.data_source == "DEMO_SEED").all():
                if d.resource_type in real_types or (d.resource_type == "AMBULANCE" and "HOSPITAL" in real_types):
                    db.delete(d)
        db.commit()
        return n, moved
    finally:
        db.close()


def main(argv: List[str]) -> None:
    bbox = CHENNAI_BBOX
    if "--bbox" in argv:
        bbox = tuple(float(x) for x in argv[argv.index("--bbox") + 1].split(","))
    if "--from-file" in argv:
        path = argv[argv.index("--from-file") + 1]
        data = json.load(open(path, encoding="utf-8"))
        print(f"[osm] loaded {path}")
    else:
        data = download(bbox)
        try:
            os.makedirs(os.path.dirname(os.path.abspath(SNAPSHOT)), exist_ok=True)
            json.dump(data, open(SNAPSHOT, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"[osm] saved a copy to {os.path.abspath(SNAPSHOT)} (re-import offline with --from-file)")
        except OSError as e:
            print(f"[osm] could not save snapshot: {e}")
    rows = parse(data)
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    print(f"[osm] {len(rows)} named facilities: " + ", ".join(f"{v} {k.lower()}" for k, v in sorted(counts.items())))
    n, moved = import_rows(rows, keep_demo="--keep-demo" in argv)
    print(f"[osm] imported {n} real facilities; {moved} demo units now start from real stations.")
    print("[osm] Data © OpenStreetMap contributors (ODbL). Availability is UNKNOWN until a service reports it.")


if __name__ == "__main__":
    main(sys.argv[1:])
