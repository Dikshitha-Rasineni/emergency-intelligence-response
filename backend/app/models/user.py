from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models._common import utcnow, new_uuid

# Roles. Citizens report without an account (they get a private tracking token instead).
ROLES = ("ADMIN", "HOSPITAL", "POLICE", "FIRE", "DISASTER")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(150), nullable=False)
    department = Column(String(20), nullable=False, index=True)  # HOSPITAL, POLICE, FIRE, DISASTER
    resource_id = Column(String(50), ForeignKey("emergency_resources.id", ondelete="SET NULL"), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    users = relationship("User", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(50), nullable=False, default="HOSPITAL")
    password_hash = Column(String(255), nullable=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="users")
