"""MaskedApplication — the officer's working record for a Zero FIR.

One row per NCRP complaint the officer picks up. Starts life at
`RECEIVED` state the moment the complaint lands, transitions through
the workflow states as the officer + auto-decisions act on it.

Phase 1a stores the header + minimal fields — the full 15-section
FIR entry body (police-station details, acts+sections, complainant,
accused, victims, property, action taken, signatures etc.) lands
progressively across phase 1b in dedicated child tables.
"""
import uuid

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric,
    String, Text, func,
)

from database import Base


# Workflow states — canonical transitions:
#
#   RECEIVED
#     ├── picked-up by officer ──▶ IN_PROGRESS
#     │
#     └── auto/manual decisions ──▶
#           ├── amount < threshold ─────────▶ ROUTED_TO_E_LOST
#           ├── amount ≥ threshold ─────────▶ ZERO_FIR_CREATED
#           │       ├── within Karnataka ─▶ TRANSFERRED_TO_JURISDICTION_PS
#           │       └── outside Karnataka ▶ TRANSFERRED_TO_CRIMAC
#           └── complainant signs w/in 3 days ▶ REGISTERED_IN_V2
#
STATUS_VALUES = frozenset({
    "RECEIVED",
    "IN_PROGRESS",
    "ROUTED_TO_E_LOST",
    "ZERO_FIR_CREATED",
    "TRANSFERRED_TO_JURISDICTION_PS",
    "TRANSFERRED_TO_CRIMAC",
    "REGISTERED_IN_V2",
    "CLOSED_UNSIGNED",   # complainant didn't sign in 3 days
    "CANCELLED",
})


class MaskedApplication(Base):
    __tablename__ = "masked_applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # ── Provenance ──────────────────────────────────────────────────
    complaint_id = Column(
        String(36),
        ForeignKey("ncrp_complaints.id"),
        nullable=False,
        unique=True,   # one Masking Application per NCRP complaint
    )
    ps_id = Column(Integer, ForeignKey("police_stations.id"), nullable=False)
    picked_up_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    picked_up_at = Column(DateTime, nullable=True)

    # ── Workflow status ─────────────────────────────────────────────
    status = Column(String(40), nullable=False, default="RECEIVED")

    # ── Auto-decision flags (populated at transition time) ─────────
    total_fraud_amount = Column(Numeric(18, 2), nullable=True)
    above_threshold = Column(Boolean, nullable=True)          # ≥ configured threshold
    threshold_at_decision = Column(Numeric(18, 2), nullable=True)  # for audit
    within_karnataka_jurisdiction = Column(Boolean, nullable=True)

    # ── FIR identifiers (populated when Zero FIR is created) ───────
    zero_fir_no = Column(String(50), nullable=True)   # "0/2026" style
    v2_fir_no = Column(String(50), nullable=True)     # once V2 assigns a number

    # ── FIR entry — Section 2 lands here as an early Phase 1b hook.
    # The rest of the 15 sections come as child tables in 1b.
    fir_summary = Column(Text, nullable=True)

    # ── NCRP echo tracking ─────────────────────────────────────────
    efir_pushed_at = Column(DateTime, nullable=True)          # API 2 fired
    notice_lien_pulled_at = Column(DateTime, nullable=True)   # API 3 fired
    registered_pushed_at = Column(DateTime, nullable=True)    # API 5 fired

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
