"""PoliceStation — reference list of the 44 KA CEN PSes.

Kept as a standalone lookup (no districts FK) so complaints can be
anchored to a receiving PS for the Zero-FIR transfer workflow. Since
2026-07-13 there is no District entity in the system — the PS's
district is implied by its `name` (e.g. "Bengaluru City East CEN PS").
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from database import Base


class PoliceStation(Base):
    __tablename__ = "police_stations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    # Short slug (e.g. "BLR-C-E-CEN"). Unique so scripts + reports can
    # reference PSes without depending on the display name.
    code = Column(String(50), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
