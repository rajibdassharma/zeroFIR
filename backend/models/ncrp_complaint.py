"""NcrpComplaint — one row per complaint pushed to us via API 1.

Design decision (2026-07-10): NCRP data is stored BOTH normalised
(typed columns + child tables for query/render) AND as a raw JSON
blob (audit + future field extraction). If NCRP's payload evolves
we handle the new columns in code, not by re-ingesting.

Every complaint is anchored to the KA CEN PS that will handle it.
NCRP tells us which PS by name; we resolve to `ps_id` at receive
time, falling back to the "unknown/needs triage" flag if the name
doesn't match our seed.
"""
import uuid

from sqlalchemy import (
    Column, Date, DateTime, ForeignKey, Integer,
    JSON, String, Text, func,
)

from database import Base


class NcrpComplaint(Base):
    __tablename__ = "ncrp_complaints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # NCRP-side ID — unique across the country. Format seen in decks:
    # 30811240050021. Kept as text to be tolerant of format changes.
    acknowledgement_no = Column(String(60), nullable=False, unique=True)
    category = Column(String(120), nullable=True)          # "Online Financial Fraud"

    # Timing at the NCRP end.
    call_start_at = Column(DateTime, nullable=True)

    # ── Complainant identity ────────────────────────────────────────
    complainant_name = Column(String(200), nullable=False)
    complainant_gender = Column(String(20), nullable=True)
    complainant_dob = Column(Date, nullable=True)
    complainant_mobile = Column(String(20), nullable=False)
    complainant_email = Column(String(200), nullable=True)
    complainant_relation_type = Column(String(30), nullable=True)   # 'Father'|'Mother'|'Spouse'
    complainant_relation_name = Column(String(200), nullable=True)

    # ── Complainant address (as given to NCRP) ──────────────────────
    address_house_no = Column(String(100), nullable=True)
    address_street = Column(String(200), nullable=True)
    address_colony = Column(String(200), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_tehsil = Column(String(100), nullable=True)
    address_country = Column(String(100), nullable=True)
    address_state = Column(String(100), nullable=True)
    address_district = Column(String(100), nullable=True)
    address_ps_name = Column(String(200), nullable=True)   # free text as sent
    address_pincode = Column(String(20), nullable=True)

    # ── Incident context ────────────────────────────────────────────
    incident_occurred_at = Column(String(500), nullable=True)   # dropdown value
    additional_information = Column(Text, nullable=True)        # ≤ 500 chars

    # ── Anchoring inside zeroFIR ────────────────────────────────────
    # Resolved from `address_ps_name` at receive time; nullable when
    # the name didn't match our seed so triage staff can reassign.
    ps_id = Column(Integer, ForeignKey("police_stations.id"), nullable=True)

    # ── Audit + raw payload (design decision 2026-07-10) ───────────
    raw_payload = Column(JSON, nullable=False)
    received_at = Column(DateTime, server_default=func.now(), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
