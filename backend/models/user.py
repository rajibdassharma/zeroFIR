"""User model — one row per person who can log in.

**Placeholder role model (2026-07-08).** Phase 0 uses the CyberFraud
role list: `super_admin`, `admin`, `unit_user`. The user will
provide the final role list in Phase 1; that update will edit
`VALID_ROLES` here plus add the `require_role(...)` dependencies in
`api/deps.py`, plus adjust seeding.
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from database import Base


VALID_ROLES = {
    "super_admin",
    "admin",
    "unit_user",
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    email = Column(String(200), nullable=True, unique=True)
    mobile = Column(String(20), nullable=True)

    # See VALID_ROLES above. Not an ENUM to keep migrations cheap when
    # roles are added; validated at the API layer.
    role = Column(String(40), nullable=False)

    # Per-PS scoping (nullable — super_admin doesn't belong to a PS).
    # Phase 1 will add FKs to units + police_stations once those tables land.
    unit_id = Column(Integer, nullable=True)
    ps_id = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    must_change_password = Column(Boolean, default=True, nullable=False, server_default="1")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
