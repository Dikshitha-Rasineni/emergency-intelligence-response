"""
Demo seed for local development and project demonstrations.

Everything created here is clearly labelled DEMO:
- Facilities have fictional names, data_source=DEMO_SEED, verified=False, no phone numbers,
  and availability UNKNOWN (unverified). Real facilities come from admin entry or the
  optional OpenStreetMap lookup.
- Demo accounts use SEED_DEMO_PASSWORD (default below). Change it or disable the accounts
  before any shared deployment.

Usage:
  python -m app.db.seed_demo_data                 # orgs, users, demo facilities, demo device
  python -m app.db.seed_demo_data --sample-reports  # also submit sample reports through the real pipeline
  python -m app.db.seed_demo_data --reset           # clear all incidents first (clean demo), then seed
  python -m app.db.seed_demo_data --demo-only       # do not re-apply saved real OpenStreetMap facilities
"""
import os
import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.resource import EmergencyResource, ResourceAvailability
from app.models.sensor import Device
from app.models.user import User, Organization

DEMO_PASSWORD = os.environ.get("SEED_DEMO_PASSWORD", "resq-demo-2026")

# Fictional facilities around Chennai for map demonstrations: a central cluster
# (Guindy / T. Nagar / Egmore), a middle cluster (Velachery / Chromepet) and a south
# cluster along GST Road (Tambaram / Potheri / Guduvanchery, near SRM IST).
# Each cluster has every service, so a report anywhere in Chennai finds help within 25 km.
RESOURCES = [
    # central
    ("DEMO-H1", "Demo Central Government Hospital", "HOSPITAL", 13.0810, 80.2750, ["Emergency department", "Trauma care"]),
    ("DEMO-A1", "Demo Ambulance Base Guindy", "AMBULANCE", 13.0067, 80.2206, ["ALS ambulance"]),
    ("DEMO-P1", "Demo T. Nagar Police Station", "POLICE", 13.0418, 80.2341, ["Patrol", "Traffic"]),
    ("DEMO-F1", "Demo Egmore Fire Station", "FIRE", 13.0732, 80.2609, ["Fire tender", "Rescue tender"]),
    ("DEMO-D1", "Demo District Disaster Response Cell", "DISASTER", 13.0604, 80.2496, ["Flood response", "Shelters"]),
    ("DEMO-S1", "Demo Community Relief Shelter", "SHELTER", 13.0350, 80.2120, ["Shelter (capacity unverified)"]),
    # middle
    ("DEMO-H2", "Demo Velachery Medical Centre", "HOSPITAL", 12.9791, 80.2210, ["Emergency department"]),
    ("DEMO-P2", "Demo Chromepet Traffic Police", "POLICE", 12.9516, 80.1462, ["Traffic", "Patrol"]),
    ("DEMO-F2", "Demo Velachery Fire Sub-Station", "FIRE", 12.9750, 80.2180, ["Fire tender"]),
    # south (GST Road)
    ("DEMO-H3", "Demo GST Road Trauma Centre", "HOSPITAL", 12.8240, 80.0460, ["Emergency department", "Trauma care"]),
    ("DEMO-A2", "Demo Ambulance Base Guduvanchery", "AMBULANCE", 12.8457, 80.0601, ["ALS ambulance"]),
    ("DEMO-P3", "Demo Maraimalai Nagar Police Station", "POLICE", 12.7920, 80.0230, ["Patrol", "Highway"]),
    ("DEMO-F3", "Demo Tambaram Fire Station", "FIRE", 12.9249, 80.1000, ["Fire tender", "Rescue tender"]),
    ("DEMO-D2", "Demo Chengalpattu Disaster Response Unit", "DISASTER", 12.8340, 80.0700, ["Flood response"]),
]

# Hardware units (ESP32 + MPU6050 / MQ-2 / DHT22 / water level). If a unit sends no GPS,
# its registered location below is used for the incident.
DEVICES = [
    ("RESQ-ESP32-001", "In-car crash unit — TN 22 AB 4521", 12.8231, 80.0442,
     "Car TN 22 AB 4521 — GST Road, Potheri junction (near SRM IST)"),
    ("RESQ-ESP32-002", "Smoke & heat unit — Velachery", 12.9780, 80.2200,
     "Demo smoke/heat unit — commercial block, Velachery Main Road"),
    ("RESQ-ESP32-003", "Water-level unit — Guindy subway", 13.0080, 80.2130,
     "Demo water-level unit — Guindy railway subway"),
]

# Response units, each based at a station above (demo fleet; positions start at the station).
UNITS = [  # (id, call sign, type, base station, capabilities)
    ("AMB-01", "Ambulance A-01", "AMBULANCE", "DEMO-H1", ["Advanced life support"]),
    ("AMB-02", "Ambulance A-02", "AMBULANCE", "DEMO-A1", ["Advanced life support"]),
    ("AMB-03", "Ambulance A-03", "AMBULANCE", "DEMO-H2", ["Basic life support"]),
    ("AMB-04", "Ambulance A-04", "AMBULANCE", "DEMO-H3", ["Advanced life support", "Trauma kit"]),
    ("AMB-05", "Ambulance A-05", "AMBULANCE", "DEMO-A2", ["Basic life support"]),
    ("FT-01", "Fire Tender F-01", "FIRE_TENDER", "DEMO-F1", ["Water tender 4500 L"]),
    ("RT-01", "Rescue Tender R-01", "RESCUE_TENDER", "DEMO-F1", ["Hydraulic cutters", "Extrication"]),
    ("FT-02", "Fire Tender F-02", "FIRE_TENDER", "DEMO-F2", ["Water tender 4500 L"]),
    ("FT-03", "Fire Tender F-03", "FIRE_TENDER", "DEMO-F3", ["Water tender 4500 L", "Foam"]),
    ("RT-02", "Rescue Tender R-02", "RESCUE_TENDER", "DEMO-F3", ["Hydraulic cutters", "Extrication"]),
    ("PCR-01", "Patrol P-01", "POLICE_PATROL", "DEMO-P1", ["Traffic control"]),
    ("PCR-02", "Patrol P-02", "POLICE_PATROL", "DEMO-P2", ["Traffic control"]),
    ("PCR-03", "Patrol P-03", "POLICE_PATROL", "DEMO-P3", ["Traffic control"]),
    ("HWP-01", "Highway Patrol H-01", "HIGHWAY_PATROL", "DEMO-P3", ["Highway closure", "Crash scene"]),
    ("DRT-01", "Disaster Team D-01", "DISASTER_TEAM", "DEMO-D1", ["Evacuation", "Shelter setup"]),
    ("BOAT-01", "Rescue Boat B-01", "RESCUE_BOAT", "DEMO-D1", ["Inflatable boat", "Divers"]),
    ("DRT-02", "Disaster Team D-02", "DISASTER_TEAM", "DEMO-D2", ["Evacuation"]),
]

ORGS = [  # (key, name, department, resource_id)
    ("hospital", "Demo Central Government Hospital — Emergency Dept", "HOSPITAL", "DEMO-H1"),
    ("police", "Demo T. Nagar Police Station — Control Room", "POLICE", "DEMO-P1"),
    ("fire", "Demo Egmore Fire Station — Control Room", "FIRE", "DEMO-F1"),
    ("disaster", "Demo District Disaster Response Cell", "DISASTER", "DEMO-D1"),
]

USERS = [  # (name, email, role, org_key)
    ("Demo Administrator", "admin@resq.demo", "ADMIN", None),
    ("Demo Hospital Operator", "hospital@resq.demo", "HOSPITAL", "hospital"),
    ("Demo Police Operator", "police@resq.demo", "POLICE", "police"),
    ("Demo Fire Operator", "fire@resq.demo", "FIRE", "fire"),
    ("Demo Disaster Operator", "disaster@resq.demo", "DISASTER", "disaster"),
]

SAMPLE_REPORTS = [
    ("Bike and car collided at the T. Nagar signal. One person is bleeding from the head, "
     "traffic is blocked.", 13.0420, 80.2345, "en"),
    ("రెండవ అంతస్తులో వంటగది నుండి పొగ వస్తోంది, ఇద్దరు లోపల చిక్కుకున్నారు", 12.9785, 80.2195, "te"),
    ("सबवे में पानी भर गया है, एक कार फंसी है और दो लोग छत पर हैं", 13.0082, 80.2133, "hi"),
]


def reset_incidents() -> None:
    """Delete every incident, sensor reading and notification (keeps users, facilities, devices)."""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("TRUNCATE emergency_reports, sensor_readings RESTART IDENTITY CASCADE"))  # also clears dispatches
        db.execute(text("UPDATE iot_devices SET last_seen_at = NULL"))
        db.commit()
        print("[seed] Cleared all incidents, sensor readings and notifications.")
    finally:
        db.close()


def seed(sample_reports: bool = False) -> None:
    db = SessionLocal()
    try:
        # Remove demo facilities from older seeds that are no longer in the list (e.g. old Bengaluru set).
        keep = {r[0] for r in RESOURCES}
        for old in db.query(EmergencyResource).filter(EmergencyResource.data_source == "DEMO_SEED").all():
            if old.id not in keep:
                db.delete(old)
        db.flush()
        for rid, name, rtype, lat, lng, caps in RESOURCES:
            r = db.get(EmergencyResource, rid) or EmergencyResource(id=rid)
            r.name, r.resource_type, r.latitude, r.longitude = name, rtype, lat, lng
            r.address, r.phone, r.capabilities = "Demo location (fictional facility)", None, caps
            r.verified, r.data_source = False, "DEMO_SEED"
            db.add(r)
            if not r.availability:
                db.add(ResourceAvailability(resource_id=rid, status="UNKNOWN", verified=False, available_units=0))
        db.flush()

        orgs = {}
        for key, name, dept, rid in ORGS:
            o = (db.query(Organization).filter_by(name=name).first()
                 or db.query(Organization).filter_by(department=dept).first()
                 or Organization(name=name, department=dept))
            o.name, o.department, o.resource_id = name, dept, rid
            db.add(o)
            orgs[key] = o
        db.flush()

        for name, email, role, org_key in USERS:
            u = db.query(User).filter_by(email=email).first() or User(email=email)
            u.name, u.role, u.is_active = name, role, True
            u.organization_id = orgs[org_key].id if org_key else None
            u.password_hash = hash_password(DEMO_PASSWORD)
            db.add(u)

        from app.models.dispatch import ResponseUnit, UNIT_DEPARTMENT
        base = {r[0]: (r[3], r[4]) for r in RESOURCES}
        for uid, call, utype, station, caps in UNITS:
            u = db.get(ResponseUnit, uid) or ResponseUnit(id=uid)
            u.call_sign, u.unit_type, u.department = call, utype, UNIT_DEPARTMENT[utype]
            u.base_resource_id, u.capabilities, u.data_source, u.active = station, caps, "DEMO_SEED", True
            u.latitude, u.longitude = base[station]
            u.position_source, u.status = "STATION", "AVAILABLE"
            db.add(u)
        for dev_id, dname, lat, lng, label in DEVICES:
            dev = db.get(Device, dev_id) or Device(device_id=dev_id)
            dev.name, dev.latitude, dev.longitude, dev.location_label, dev.active = dname, lat, lng, label, True
            db.add(dev)
        db.commit()
        from app.db.knowledge_seed import seed_knowledge
        kn = seed_knowledge(db)
        db.commit()
        print(f"[seed] GenAI knowledge base: {kn} guidance document(s) added for RAG.")
        print(f"[seed] {len(RESOURCES)} demo facilities (Chennai), {len(ORGS)} organisations, "
              f"{len(USERS)} users, {len(DEVICES)} sensor units, {len(UNITS)} response units.")
        print(f"[seed] Demo logins: {', '.join(u[1] for u in USERS)}  password: {DEMO_PASSWORD}")

        if sample_reports:
            from app.schemas.incident import IncidentCreate
            from app.services.incident_service import IncidentService
            for text, lat, lng, lang in SAMPLE_REPORTS:
                rep, _, _ = IncidentService.create_citizen_report(db, IncidentCreate(
                    description=text, latitude=lat, longitude=lng, location_source="DEVICE_GPS",
                    location="Sample report (demo)", preferred_language=lang))
                IncidentService.enrich_with_llm(rep.id)
                print(f"[seed] sample report {rep.id} ({lang})")
    finally:
        db.close()


seed_database = seed  # backwards-compatible name

if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_incidents()
    seed(sample_reports="--sample-reports" in sys.argv)
    # Re-apply real OpenStreetMap facilities if they were imported before (saved snapshot, works offline)
    from app.db import import_osm_facilities as osm
    if os.path.exists(osm.SNAPSHOT) and "--demo-only" not in sys.argv:
        print("[seed] re-applying saved OpenStreetMap facilities (use --demo-only to skip)")
        osm.main(["--from-file", osm.SNAPSHOT])
