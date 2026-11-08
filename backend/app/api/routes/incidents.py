"""Citizen-facing incident endpoints (no account; a private tracking token proves ownership)."""
import hmac
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.core.config import settings
from app.core.rate_limit import check_rate, client_ip
from app.core.security import hash_tracking_token
from app.db.session import get_db
from app.models.incident import EmergencyReport
from app.models.media import IncidentMedia
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentCreated
from app.services.incident_service import IncidentService
from app.services.vision_service import VisionService, ImageValidationError

router = APIRouter()


def _get_report(db: Session, incident_id: str) -> EmergencyReport:
    r = db.get(EmergencyReport, incident_id)
    if not r:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Report not found."})
    return r


def _authorize(report: EmergencyReport, token: Optional[str], user: Optional[User], db: Session) -> str:
    """Returns 'citizen' or the department of an authorized user. Raises 403 otherwise."""
    if token and report.tracking_token_hash and hmac.compare_digest(hash_tracking_token(token), report.tracking_token_hash):
        return "citizen"
    if user:
        canonical = db.get(EmergencyReport, report.merged_into_id) if report.merged_into_id else report
        if IncidentService.is_routed_to(canonical, user.role.upper()):
            return user.role.upper()
    raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "Not authorized for this report."})


def _genai_prewarm(incident_id: str) -> None:
    from app.services.genai_service import prewarm
    prewarm(incident_id)


@router.post("/incidents", response_model=IncidentCreated, status_code=status.HTTP_201_CREATED)
def create_incident(body: IncidentCreate, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Submit an emergency report. Returns immediately with a rule-based assessment;
    LLM extraction refines it in the background. The tracking token is returned once."""
    check_rate(request, "report", settings.RATE_LIMIT_REPORTS_PER_MIN)
    report, token, merged = IncidentService.create_citizen_report(db, body, actor_ip=client_ip(request))
    background.add_task(IncidentService.enrich_with_llm, report.id)
    background.add_task(_genai_prewarm, report.id)
    return IncidentCreated(incident_id=report.id, tracking_token=token, merged_into=merged.id if merged else None,
                           citizen_view=IncidentService.citizen_view(db, report))


@router.get("/incidents/{incident_id}/track")
def track_incident(incident_id: str, x_tracking_token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    report = _get_report(db, incident_id)
    _authorize(report, x_tracking_token, None, db)
    return IncidentService.citizen_view(db, report)


@router.get("/incidents/{incident_id}/genai-guidance")
def genai_guidance(incident_id: str, x_tracking_token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """GenAI (RAG) safety steps for the citizen, from approved guidance, in the citizen's language."""
    from app.services.genai_service import GenAIService
    report = _get_report(db, incident_id)
    _authorize(report, x_tracking_token, None, db)
    canonical = db.get(EmergencyReport, report.merged_into_id) if report.merged_into_id else report
    lang = report.preferred_language or report.detected_language or "en"
    out = GenAIService.citizen_guidance(db, canonical, IncidentService.full_view(db, canonical), lang)
    db.commit()
    return out or {"generated": False}


@router.post("/incidents/{incident_id}/media", status_code=status.HTTP_202_ACCEPTED)
async def upload_media(incident_id: str, request: Request, background: BackgroundTasks,
                       files: List[UploadFile] = File(...), x_tracking_token: Optional[str] = Header(None),
                       user: Optional[User] = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    """Attach 1..N images. Each is validated, cleaned (EXIF stripped) and analysed in the background.
    The incident already exists, so a failed image never blocks the report."""
    check_rate(request, "upload", settings.RATE_LIMIT_UPLOADS_PER_MIN)
    report = _get_report(db, incident_id)
    _authorize(report, x_tracking_token, user, db)
    results = []
    limit = int(settings.MAX_IMAGE_MB * 1024 * 1024) + 1
    for f in files[: settings.MAX_IMAGES_PER_INCIDENT]:
        raw = await f.read(limit)
        try:
            media, is_new = VisionService.ingest(db, report.id, raw, f.content_type)
            db.commit()
            if is_new:
                background.add_task(IncidentService.analyze_media, media.id)
            results.append({"filename": f.filename, "accepted": True, "duplicate": not is_new, "media_id": media.id,
                            "status": media.status})
        except ImageValidationError as e:
            db.rollback()
            results.append({"filename": f.filename, "accepted": False, "error": str(e)})
    return {"incident_id": report.id, "results": results}


@router.get("/incidents/{incident_id}/media")
def list_media(incident_id: str, x_tracking_token: Optional[str] = Header(None),
               user: Optional[User] = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    report = _get_report(db, incident_id)
    who = _authorize(report, x_tracking_token, user, db)
    if who == "citizen":
        return [{"id": m.id, "status": m.status, "created_at": m.created_at} for m in report.media]
    return [VisionService.to_dict(m) for m in report.media]


@router.get("/incidents/{incident_id}/media/{media_id}/file")
def get_media_file(incident_id: str, media_id: str, x_tracking_token: Optional[str] = Header(None),
                   user: Optional[User] = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    report = _get_report(db, incident_id)
    m = db.get(IncidentMedia, media_id)
    if not m:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
    canonical_id = report.merged_into_id or report.id
    owner = db.get(EmergencyReport, m.incident_id)
    if m.incident_id != report.id and (owner.merged_into_id or owner.id) != canonical_id:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})
    _authorize(report, x_tracking_token, user, db)
    return FileResponse(VisionService.file_path(m), media_type=m.mime_type,
                        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
