"""PoliceITV2Data — the "outbound to Police IT V2" bucket.

Every field that the Zero-FIR flow eventually pushes to Police IT V2
(so V2 can raise the actual FIR record) lives here, keyed on
`acknowledgement_no` so the row correlates 1:1 with the NCRP-side
`ncrp_data` row.

Also carries the internal workflow state (status, ps_id, picked-up
tracking, threshold/jurisdiction decisions, echo timestamps, and
the FIR numbers assigned along the way) — that state is what tells
the operator + downstream jobs where each complaint is in the
pipeline.

Child table: `police_it_v2_acts` (Section 3 per-act rows).

Kept as a single table (rather than splitting workflow off) per the
2026-07-13 scope decision to run with two main outbound tables.
"""
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric,
    String, Text, func,
)
from sqlalchemy.orm import relationship

from database import Base


# Workflow states — canonical transitions:
#
#   RECEIVED
#     ├── picked-up by operator ──▶ IN_PROGRESS
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
    # Operator hit Submit → NCRP outbound (API 2) + Police IT V2
    # outbound both fired (placeholders today). The auto-decision
    # states below come afterwards once threshold + jurisdiction
    # checks land in Phase 1b.3.
    "SUBMITTED",
    "ROUTED_TO_E_LOST",
    "ZERO_FIR_CREATED",
    "TRANSFERRED_TO_JURISDICTION_PS",
    "TRANSFERRED_TO_CRIMAC",
    "REGISTERED_IN_V2",
    "CLOSED_UNSIGNED",   # complainant didn't sign in 3 days
    "CANCELLED",
})


class PoliceITV2Data(Base):
    __tablename__ = "police_it_v2_data"

    # Same business key as ncrp_data — 1:1 relationship. Cascade
    # delete so tearing down an NCRP row cleans up here too.
    acknowledgement_no = Column(
        String(60),
        ForeignKey("ncrp_data.acknowledgement_no", ondelete="CASCADE"),
        primary_key=True,
    )

    # ── Workflow state ──────────────────────────────────────────────
    ps_id = Column(Integer, ForeignKey("police_stations.id"), nullable=True)
    picked_up_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    picked_up_at = Column(DateTime, nullable=True)
    status = Column(String(40), nullable=False, default="RECEIVED")

    # ── Auto-decision flags (populated at transition time) ─────────
    total_fraud_amount = Column(Numeric(18, 2), nullable=True)
    above_threshold = Column(Boolean, nullable=True)
    threshold_at_decision = Column(Numeric(18, 2), nullable=True)   # for audit
    within_karnataka_jurisdiction = Column(Boolean, nullable=True)

    # ── FIR identifiers (populated when Zero FIR is created) ───────
    zero_fir_no = Column(String(50), nullable=True)   # "0/2026" style
    v2_fir_no = Column(String(50), nullable=True)     # once V2 assigns a number

    # ── NCRP echo tracking (outbound API 2 / 3 / 5 timestamps) ─────
    efir_pushed_at = Column(DateTime, nullable=True)          # API 2 fired
    notice_lien_pulled_at = Column(DateTime, nullable=True)   # API 3 fired
    registered_pushed_at = Column(DateTime, nullable=True)    # API 5 fired

    # ═════════════════════════════════════════════════════════════════
    # ── FIR ENTRY FIELDS (V2 deck sections 1-6) ────────────────────
    # Every field is nullable so operators can save-as-draft with
    # partial data. Server-side "submit" validation lands with
    # Phase 1b.3's dedicated submit endpoint.
    # ═════════════════════════════════════════════════════════════════

    # ── Section 1: Police Station Details ────────────────────────
    ps_details_district = Column(String(100), nullable=True)
    ps_details_sub_division = Column(String(100), nullable=True)
    ps_details_ps_name = Column(String(200), nullable=True)
    ps_details_entry_date = Column(Date, nullable=True)
    ps_details_last_fir_no = Column(String(50), nullable=True)
    ps_details_last_fir_time = Column(DateTime, nullable=True)
    ps_details_gsc_no = Column(String(50), nullable=True)

    # ── Section 2: FIR Summary ──────────────────────────────────
    fir_summary = Column(Text, nullable=True)

    # ── Section 3: Acts & Sections aggregate flags ─────────────
    # Per-row acts live in `police_it_v2_acts`.
    crime_classification_major = Column(String(100), nullable=True)
    crime_classification_minor = Column(String(100), nullable=True)
    offences_involve_aadhaar = Column(Boolean, nullable=True)

    # ── Section 4: Time of Occurrence ────────────────────────────
    incident_from_at = Column(DateTime, nullable=True)
    incident_to_at = Column(DateTime, nullable=True)
    info_received_at_ps_at = Column(DateTime, nullable=True)
    mode_of_complaint = Column(String(50), nullable=True)
    fir_case_type = Column(String(30), nullable=True)
    shd_reference = Column(String(100), nullable=True)
    reasons_for_delay = Column(Text, nullable=True)
    complainant_saw_occurrence = Column(Boolean, nullable=True)

    # ── Section 5: Place of Incident ─────────────────────────────
    poi_house_no = Column(String(100), nullable=True)
    poi_street = Column(String(200), nullable=True)
    poi_colony = Column(String(200), nullable=True)     # V2 slide 4 "Colony/Locality/Area"
    poi_beat_name = Column(String(100), nullable=True)
    poi_village = Column(String(200), nullable=True)
    poi_city = Column(String(100), nullable=True)
    poi_tehsil = Column(String(100), nullable=True)     # V2 slide 4 "Tehsil/Block/Mandal"
    poi_district = Column(String(100), nullable=True)
    poi_state = Column(String(100), nullable=True)
    poi_country = Column(String(100), nullable=True)    # V2 slide 4 "Country" *
    poi_police_station = Column(String(200), nullable=True)  # V2 slide 4 "Police Station of incident" *
    poi_pincode = Column(String(20), nullable=True)
    poi_distance_from_ps = Column(String(50), nullable=True)
    poi_direction_from_ps = Column(String(20), nullable=True)
    poi_mla_constituency = Column(String(150), nullable=True)
    poi_mp_constituency = Column(String(150), nullable=True)
    poi_is_forest = Column(Boolean, nullable=True)
    poi_is_sea = Column(Boolean, nullable=True)
    poi_location_nature = Column(String(30), nullable=True)
    poi_latitude = Column(Numeric(10, 7), nullable=True)
    poi_longitude = Column(Numeric(10, 7), nullable=True)
    poi_other_juris_state = Column(String(100), nullable=True)
    poi_other_juris_district = Column(String(100), nullable=True)
    poi_other_juris_ps = Column(String(200), nullable=True)

    # ── Section 6: Complainant / Informant (extras beyond NCRP) ─
    comp_relation_to_victim = Column(String(50), nullable=True)
    comp_role = Column(String(50), nullable=True)
    comp_middle_name = Column(String(100), nullable=True)
    comp_nationality = Column(String(50), nullable=True)
    comp_occupation = Column(String(100), nullable=True)
    comp_religion = Column(String(50), nullable=True)         # V2 slide 2 dropdown
    comp_caste = Column(String(50), nullable=True)            # V2 slide 2 dropdown
    comp_father_name = Column(String(200), nullable=True)
    comp_mother_name = Column(String(200), nullable=True)
    comp_uid_type = Column(String(30), nullable=True)
    comp_uid_number = Column(String(50), nullable=True)
    comp_aadhaar_ref_no = Column(String(20), nullable=True)   # V2 slide 2 mandatory *
    comp_alt_mobile = Column(String(20), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    acts = relationship(
        "PoliceITV2Act",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
