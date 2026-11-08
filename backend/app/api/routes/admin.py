"""Admin console API: users, organisations, resources, devices, knowledge, audit, routing policy."""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.deps import require_roles, get_current_user
from app.core.security import hash_password
from app.db.session import get_db
from app.models.media import IncidentMedia
from app.models.operations import AuditEvent, KnowledgeDocument
from app.models.resource import EmergencyResource, ResourceAvailability
from app.models.sensor import Device, SensorReading
from app.models.user import User, Organization
from app.schemas.auth import UserCreate, OrganizationCreate
from app.schemas.iot import DeviceUpsert
from app.schemas.resource import ResourceUpsert, AvailabilityUpdate
from app.services import department_routing_service as policy
from app.services.audit_service import AuditService
from app.services.rag_service import RagService
from app.services.taxonomy import CATEGORIES, CATEGORY_LABELS_EN, SUPPORTED_UI_LANGUAGES
from app.services.vision_service import VisionService
from app.api.routes.auth import user_out

router = APIRouter(prefix="/admin")
admin_only = require_roles("ADMIN")


# ---------------------------------------------------------------- users / orgs
@router.get("/users")
def list_users(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    return [user_out(u) for u in db.query(User).order_by(User.role, User.email).all()]


@router.post("/users", status_code=201)
def create_user(body: UserCreate, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, detail={"error": "EMAIL_EXISTS"})
    if body.organization_id and not db.get(Organization, body.organization_id):
        raise HTTPException(400, detail={"error": "UNKNOWN_ORGANIZATION"})
    u = User(name=body.name, email=email, role=body.role, password_hash=hash_password(body.password),
             organization_id=body.organization_id)
    db.add(u)
    AuditService.record(db, admin.email, "admin.user_create", "user", email, {"role": body.role})
    db.commit()
    return user_out(u)


@router.post("/users/{user_id}/active")
def set_user_active(user_id: str, active: bool = Query(...), admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, detail={"error": "NOT_FOUND"})
    if u.id == admin.id and not active:
        raise HTTPException(400, detail={"error": "CANNOT_DISABLE_SELF"})
    u.is_active = active
    AuditService.record(db, admin.email, "admin.user_active", "user", u.id, {"active": active})
    db.commit()
    return user_out(u)


@router.get("/organizations")
def list_orgs(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    return [{"id": o.id, "name": o.name, "department": o.department, "resource_id": o.resource_id, "active": o.active,
             "users": len(o.users)} for o in db.query(Organization).order_by(Organization.department).all()]


@router.post("/organizations", status_code=201)
def create_org(body: OrganizationCreate, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    o = Organization(name=body.name, department=body.department, resource_id=body.resource_id)
    db.add(o)
    AuditService.record(db, admin.email, "admin.org_create", "organization", None, {"name": body.name})
    db.commit()
    return {"id": o.id, "name": o.name, "department": o.department}


# ---------------------------------------------------------------- resources
@router.get("/resources")
def list_resources(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    out = []
    for r in db.query(EmergencyResource).order_by(EmergencyResource.resource_type, EmergencyResource.name).all():
        av = r.availability
        out.append({"id": r.id, "name": r.name, "resource_type": r.resource_type, "latitude": r.latitude,
                    "longitude": r.longitude, "address": r.address, "phone": r.phone, "capabilities": r.capabilities,
                    "verified": r.verified, "data_source": r.data_source,
                    "availability": {"status": av.status, "verified": av.verified, "available_units": av.available_units,
                                     "updated_at": av.updated_at} if av else None})
    return out


@router.post("/resources", status_code=201)
def upsert_resource(body: ResourceUpsert, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    rid = body.id or f"RES-{uuid.uuid4().hex[:8].upper()}"
    r = db.get(EmergencyResource, rid) or EmergencyResource(id=rid, data_source="ADMIN")
    for k in ("name", "resource_type", "latitude", "longitude", "address", "phone", "capabilities", "verified"):
        setattr(r, k, getattr(body, k))
    db.add(r)
    if not r.availability:
        db.add(ResourceAvailability(resource_id=rid, status="UNKNOWN", verified=False))
    AuditService.record(db, admin.email, "admin.resource_upsert", "resource", rid, {"verified": body.verified})
    db.commit()
    return {"id": rid}


@router.delete("/resources/{resource_id}", status_code=204)
def delete_resource(resource_id: str, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    r = db.get(EmergencyResource, resource_id)
    if not r:
        raise HTTPException(404, detail={"error": "NOT_FOUND"})
    db.delete(r)
    AuditService.record(db, admin.email, "admin.resource_delete", "resource", resource_id)
    db.commit()


@router.post("/resources/{resource_id}/availability")
def update_availability(resource_id: str, body: AvailabilityUpdate, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """Admins, or users of the organisation that operates this resource, may report availability."""
    r = db.get(EmergencyResource, resource_id)
    if not r:
        raise HTTPException(404, detail={"error": "NOT_FOUND"})
    allowed = user.role == "ADMIN" or (user.organization and user.organization.resource_id == resource_id)
    if not allowed:
        raise HTTPException(403, detail={"error": "FORBIDDEN", "message": "Only the operating organisation can report availability."})
    av = r.availability or ResourceAvailability(resource_id=resource_id)
    av.status, av.available_units, av.operational_details = body.status, body.available_units or 0, body.operational_details
    av.verified, av.reported_by, av.updated_at = True, user.id, datetime.now(timezone.utc)
    db.add(av)
    AuditService.record(db, user.email, "resource.availability", "resource", resource_id, {"status": body.status})
    db.commit()
    return {"resource_id": resource_id, "status": av.status, "verified": True}


# ---------------------------------------------------------------- devices
@router.get("/devices")
def list_devices(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    out = []
    for d in db.query(Device).order_by(Device.device_id).all():
        last = db.query(SensorReading).filter_by(device_id=d.device_id).order_by(SensorReading.timestamp.desc()).first()
        out.append({"device_id": d.device_id, "name": d.name, "latitude": d.latitude, "longitude": d.longitude,
                    "location_label": d.location_label, "active": d.active, "firmware_version": d.firmware_version,
                    "last_seen_at": d.last_seen_at, "last_transport": d.last_transport,
                    "last_reading": {"event_type": last.event_type, "hazard_severity": last.hazard_severity,
                                     "temperature": last.temperature, "mq2_filtered_adc": last.mq2_filtered_adc,
                                     "water_level_raw_adc": last.water_level_raw_adc, "timestamp": last.timestamp} if last else None})
    return out


@router.post("/devices", status_code=201)
def upsert_device(body: DeviceUpsert, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    d = db.get(Device, body.device_id) or Device(device_id=body.device_id)
    for k in ("name", "latitude", "longitude", "location_label", "active"):
        setattr(d, k, getattr(body, k))
    db.add(d)
    AuditService.record(db, admin.email, "admin.device_upsert", "device", body.device_id)
    db.commit()
    return {"device_id": d.device_id}


# ---------------------------------------------------------------- knowledge (RAG)
@router.get("/knowledge")
def list_docs(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    return [{"id": d.id, "title": d.title, "publisher": d.publisher, "source_url": d.source_url, "version": d.version,
             "published_on": d.published_on, "language": d.language, "categories": d.categories, "approved": d.approved,
             "chunks": len(d.chunks), "created_at": d.created_at}
            for d in db.query(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).all()]


@router.post("/knowledge", status_code=201)
async def add_doc(title: str = Form(..., max_length=255), publisher: str = Form(..., max_length=255),
                  categories: str = Form(""), language: str = Form("en"), source_url: Optional[str] = Form(None),
                  version: Optional[str] = Form(None), published_on: Optional[str] = Form(None),
                  body: Optional[str] = Form(None), file: Optional[UploadFile] = File(None),
                  admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    text = body or ""
    if file:
        raw = await file.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise HTTPException(413, detail={"error": "TOO_LARGE", "message": "Max 2 MB text file."})
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(400, detail={"error": "NOT_TEXT", "message": "Upload a UTF-8 .txt or .md file."})
    if len(text.strip()) < 50:
        raise HTTPException(400, detail={"error": "EMPTY", "message": "Document text is too short."})
    cats = [c.strip() for c in categories.split(",") if c.strip() in CATEGORIES]
    doc = RagService.ingest(db, title=title, publisher=publisher, body=text, categories=cats, language=language,
                            source_url=source_url, version=version, published_on=published_on, approved=False,
                            created_by=admin.id)
    AuditService.record(db, admin.email, "knowledge.add", "knowledge_document", doc.id, {"title": title})
    db.commit()
    return {"id": doc.id, "chunks": len(doc.chunks), "approved": False}


@router.post("/knowledge/{doc_id}/approve")
def approve_doc(doc_id: str, approved: bool = Query(True), admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    d = db.get(KnowledgeDocument, doc_id)
    if not d:
        raise HTTPException(404, detail={"error": "NOT_FOUND"})
    d.approved = approved
    AuditService.record(db, admin.email, "knowledge.approve", "knowledge_document", doc_id, {"approved": approved})
    db.commit()
    return {"id": doc_id, "approved": approved}


@router.delete("/knowledge/{doc_id}", status_code=204)
def delete_doc(doc_id: str, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    d = db.get(KnowledgeDocument, doc_id)
    if not d:
        raise HTTPException(404, detail={"error": "NOT_FOUND"})
    db.delete(d)
    AuditService.record(db, admin.email, "knowledge.delete", "knowledge_document", doc_id)
    db.commit()


@router.get("/knowledge/search")
def search_docs(q: str = Query(..., min_length=2), category: Optional[str] = None,
                _: User = Depends(require_roles("ADMIN", "HOSPITAL", "POLICE", "FIRE", "DISASTER")),
                db: Session = Depends(get_db)):
    return RagService.search(db, q, category, None, limit=5)


# ---------------------------------------------------------------- audit / config
@router.get("/audit")
def audit(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), action: Optional[str] = None,
          _: User = Depends(admin_only), db: Session = Depends(get_db)):
    q = db.query(AuditEvent)
    if action:
        q = q.filter(AuditEvent.action.like(f"{action}%"))
    total = q.count()
    rows = q.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [{"at": a.created_at, "actor": a.actor, "action": a.action, "target_type": a.target_type,
                                       "target_id": a.target_id, "details": a.details, "ip": a.ip} for a in rows]}


@router.get("/config")
def config(_: User = Depends(admin_only)):
    return {
        "routing_policy_version": policy.POLICY_VERSION,
        "routing_rules_source": "app/services/department_routing_service.py (deterministic; edit + redeploy to change)",
        "department_fields": {k: sorted(v) for k, v in policy.DEPARTMENT_FIELDS.items()},
        "categories": [{"code": c, "label": CATEGORY_LABELS_EN[c]} for c in CATEGORIES],
        "ui_languages": list(SUPPORTED_UI_LANGUAGES),
    }


@router.post("/media/purge")
def purge_media(admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Deletes stored images past their retention date (MEDIA_RETENTION_DAYS)."""
    now = datetime.now(timezone.utc)
    n = 0
    for m in db.query(IncidentMedia).filter(IncidentMedia.purge_after < now).all():
        try:
            os.remove(VisionService.file_path(m))
        except FileNotFoundError:
            pass
        db.delete(m)
        n += 1
    AuditService.record(db, admin.email, "media.purge", details={"deleted": n})
    db.commit()
    return {"deleted": n}
