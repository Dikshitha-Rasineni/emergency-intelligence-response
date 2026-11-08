from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=1, max_length=200)


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    is_active: bool = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserOut


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    password: str = Field(..., min_length=10, max_length=200)
    role: str = Field(..., pattern="^(ADMIN|HOSPITAL|POLICE|FIRE|DISASTER)$")
    organization_id: Optional[str] = None


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    department: str = Field(..., pattern="^(HOSPITAL|POLICE|FIRE|DISASTER)$")
    resource_id: Optional[str] = None
