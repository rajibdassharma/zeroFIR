"""OutboundEvent — append-only audit log of every outbound / inbound
integration event for a complaint.

Populated by the placeholder functions in `services/outbound.py`. When
real HTTP integrations land the same helpers will keep writing here,
just with `status='success'` (or `'failed'`) instead of `'placeholder'`
and with the actual response body captured in `response`.

Never `UPDATE` or `DELETE` — new rows only. Same append-only rule as
CyberFraud/eParole event tables.
"""
import uuid

from sqlalchemy import (
    Column, DateTime, ForeignKey, JSON, String, Text, func,
)

from database import Base


# Slug catalog — keeps event_type consistent across code + reports.
# One slug per arrow in the KarnatakazeroFIR process flow.
EVENT_TYPES = frozenset({
    "push_complaint_to_ncrp",         # Arrow 1
    "push_v2_intake",                 # Arrow 2 (Masking App → V2 for FIR creation)
    "push_efir_detail_to_ncrp",       # Arrow 3 (KA CEN PS → NCRP after eFIR)
    "pull_notice_lien_from_ncrp",     # Arrow 4 (V2 → NCRP)
    "push_crimac_transfer",           # Arrow 5 (out-of-KA jurisdiction)
    "push_registered_fir_to_ncrp",    # Arrow 6 (V2 → NCRP after FIR registered)
    "push_e_lost_transfer",           # Below-threshold routing (not numbered in deck)
})

TARGET_SYSTEMS = frozenset({"NCRP", "POLICE_IT_V2", "CRIMAC", "E_LOST"})

DIRECTIONS = frozenset({"outbound", "inbound"})   # outbound = we initiate

STATUSES = frozenset({"placeholder", "success", "failed"})


class OutboundEvent(Base):
    __tablename__ = "outbound_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    acknowledgement_no = Column(
        String(60),
        ForeignKey("ncrp_data.acknowledgement_no", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction = Column(String(10), nullable=False)         # outbound | inbound
    target_system = Column(String(30), nullable=False)     # NCRP | POLICE_IT_V2 | CRIMAC | E_LOST
    event_type = Column(String(60), nullable=False)        # from EVENT_TYPES
    status = Column(String(20), nullable=False, default="placeholder")
    payload = Column(JSON, nullable=True)                  # what we would send / did send
    response = Column(JSON, nullable=True)                 # what came back (null for placeholders)
    notes = Column(Text, nullable=True)                    # human-readable summary
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
