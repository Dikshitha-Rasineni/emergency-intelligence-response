from typing import Optional, Iterable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


def get_current_user_optional(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not creds:
        return None
    payload = decode_access_token(creds.credentials)
    if not payload:
        return None
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        return None
    return user


def get_current_user(user: Optional[User] = Depends(get_current_user_optional)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"error": "UNAUTHENTICATED", "message": "Sign in required."},
                            headers={"WWW-Authenticate": "Bearer"})
    return user


def require_roles(*roles: str):
    allowed = {r.upper() for r in roles}

    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role.upper() not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail={"error": "FORBIDDEN", "message": "Your role cannot access this resource."})
        return user
    return _dep


CONTROL_ROOM_ROLES = ("HOSPITAL", "POLICE", "FIRE", "DISASTER", "ADMIN")


def verify_device(request: Request) -> None:
    """ESP32 devices authenticate with a shared bearer token (IOT_DEVICE_TOKEN)."""
    expected = settings.IOT_DEVICE_TOKEN
    if not expected:
        if settings.APP_ENV == "production":
            raise HTTPException(status_code=503, detail={"error": "DEVICE_AUTH_NOT_CONFIGURED"})
        logger.warning("IOT_DEVICE_TOKEN not set: IoT endpoint accepting unauthenticated devices (development only).")
        return
    header = request.headers.get("authorization", "")
    if header != f"Bearer {expected}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "INVALID_DEVICE_TOKEN"})
