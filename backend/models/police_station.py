"""PoliceStation — one row per KA CEN Police Station.

44 CEN PSes across 31 districts (Bengaluru City has multiple, most
other districts have one). Every zeroFIR complaint is anchored to a
PS via `ncrp_complaints.ps_id` at receive time.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from database import Base


class PoliceStation(Base):
    __tablename__ = "police_stations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    # Short slug for username scaffolding (e.g. "cen_bengaluru_north").
    code = Column(String(50), nullable=False, unique=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
