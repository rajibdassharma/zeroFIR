"""PoliceITV2Act — one row per (act × sections) tuple on a FIR.

Parent: `police_it_v2_data` (FK on `acknowledgement_no`).

V2 FIR entry Section 3 lets the officer add multiple acts (BNS,
BNSS, IT Act, IPC-legacy, etc.), each with its own comma-separated
sections and metadata. Kept as a child table (not a JSON column) so
downstream reports can group and count by act / section.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, func

from database import Base


class PoliceITV2Act(Base):
    __tablename__ = "police_it_v2_acts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    acknowledgement_no = Column(
        String(60),
        ForeignKey("police_it_v2_data.acknowledgement_no", ondelete="CASCADE"),
        nullable=False,
    )
    act_code = Column(String(30), nullable=True)      # BNS / BNSS / IT / IPC
    act_name = Column(String(200), nullable=True)     # Human label
    sections = Column(String(500), nullable=True)     # Comma-separated section numbers
    offence_type = Column(String(100), nullable=True) # Cognisable / Non-cognisable
    gravity = Column(String(50), nullable=True)       # Major / Minor / Petty

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
