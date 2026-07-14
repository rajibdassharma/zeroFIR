"""User model — one row per person who can log in.

Centralised call-centre only (2026-07-13). Every user is a
`call_center` operator with state-wide scope. No District, no PS
assignment, no super_admin — future roles land here when needed.
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from database import Base


VALID_ROLES = {
    "call_center",
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    email = Column(String(200), nullable=True, unique=True)
    mobile = Column(String(20), nullable=True)

    # See VALID_ROLES above. Kept as VARCHAR (not ENUM) so a new role
    # only needs an app-layer change, no ALTER TABLE.
    role = Column(String(40), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    must_change_password = Column(Boolean, default=True, nullable=False, server_default="1")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
