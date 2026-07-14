"""NcrpData — one row per complaint that will be sent back to NCRP.

This is the "NCRP outbound" bucket in our data model (2026-07-13
scope decision). Every field here is data that either came FROM
NCRP or will go TO NCRP via APIs 2 / 5.

Primary key = `acknowledgement_no` (business key) rather than a
synthetic UUID — makes joins and integration lookups trivially
correlatable with what NCRP holds on its side.

Child tables:
- `ncrp_transactions`      (victim's debited transactions)
- `ncrp_suspect_mobiles`   (any mobile numbers the victim can attribute to the fraudster)
- `ncrp_suspect_accounts`  (bank / wallet accounts where money went)
- `ncrp_efir_answers`      (the 7 e-FIR Yes/No questionnaire answers)

All children FK on `acknowledgement_no` with ON DELETE CASCADE.
"""
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Integer, ForeignKey,
    String, Text, func,
)

from database import Base


class NcrpData(Base):
    __tablename__ = "ncrp_data"

    # NCRP-side ID — unique across the country. Format seen in decks:
    # 30811240050021. Kept as text to be tolerant of format changes.
    acknowledgement_no = Column(String(60), primary_key=True)
    category = Column(String(120), nullable=True)          # "Online Financial Fraud"

    # Timing at the NCRP end (when the call intake started).
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
    address_ps_name = Column(String(200), nullable=True)   # picked from PS dropdown
    address_pincode = Column(String(20), nullable=True)

    # ── Incident context ────────────────────────────────────────────
    # "Where did the incident occur?" — dropdown, see INCIDENT_PLACE_OPTIONS.
    incident_place = Column(String(120), nullable=True)
    additional_information = Column(Text, nullable=True)   # ≤ 500 chars
    # "Do You have Suspect Account Details?" toggle. When True, the
    # operator should have added rows in ncrp_suspect_accounts.
    has_suspect_account_details = Column(Boolean, nullable=False, default=False, server_default="0")

    # ── PS anchoring (drives the police_it_v2 side) ────────────────
    # Resolved from `address_ps_name` at receive time via the PS
    # dropdown, so it's guaranteed to match a real PS row. Nullable
    # only for the (rare) unresolved-PS case.
    ps_id = Column(Integer, ForeignKey("police_stations.id"), nullable=True)

    received_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
