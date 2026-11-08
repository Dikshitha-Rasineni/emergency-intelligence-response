from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import check_rate, client_ip
from app.core.security import verify_password, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.services.audit_service import AuditService

router = APIRouter()


def user_out(u: User) -> UserOut:
    return UserOut(id=u.id, name=u.name, email=u.email, role=u.role, organization_id=u.organization_id,
                   organization_name=u.organization.name if u.organization else None, is_active=u.is_active)


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    check_rate(request, "login", 10)
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        AuditService.record(db, body.email[:150], "auth.login_failed", ip=client_ip(request))
        db.commit()
        raise HTTPException(status_code=401, detail={"error": "INVALID_CREDENTIALS", "message": "Email or password is incorrect."})
    user.last_login_at = datetime.now(timezone.utc)
    AuditService.record(db, user.email, "auth.login", "user", user.id, ip=client_ip(request))
    db.commit()
    token = create_access_token(user.id, user.role, user.organization_id)
    return TokenResponse(access_token=token, expires_in_minutes=settings.JWT_EXPIRE_MINUTES, user=user_out(user))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)
