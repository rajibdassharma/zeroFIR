"""District — one row per Karnataka district."""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from database import Base


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    # Short slug for username scaffolding (e.g. "bengaluru_urban").
    code = Column(String(50), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
