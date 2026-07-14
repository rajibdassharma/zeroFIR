"""Schemas for the FIR entry form (V2 sections 1-6, Phase 1b.1).

Every field is optional so the operator can save partial drafts.
Server-side "submit" validation (required-field enforcement) lands
in Phase 1b.3 alongside the auto-decisions.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Section 3 child row ──────────────────────────────────────────


class FirActPayload(BaseModel):
    """One row of the Acts & Sections grid. `id` is only sent when the
    operator is editing an existing row — server treats missing id as
    "new row"."""
    id: Optional[str] = None
    act_code: Optional[str] = Field(default=None, max_length=30)
    act_name: Optional[str] = Field(default=None, max_length=200)
    sections: Optional[str] = Field(default=None, max_length=500)
    offence_type: Optional[str] = Field(default=None, max_length=100)
    gravity: Optional[str] = Field(default=None, max_length=50)


class FirActView(BaseModel):
    id: str
    act_code: Optional[str] = None
    act_name: Optional[str] = None
    sections: Optional[str] = None
    offence_type: Optional[str] = None
    gravity: Optional[str] = None


# ── Draft update body ────────────────────────────────────────────


class FirDraftUpdate(BaseModel):
    """PATCH body for /api/v1/complaints/{ack_no}/v2-draft.

    All fields optional. `acts` (if present) REPLACES the child rows
    for this application — send the full desired list, not a diff.
    Passing an empty list `[]` deletes all act rows; omitting the key
    leaves them unchanged."""

    # ── Section 1 — Police Station Details ────────────────────────
    ps_details_district: Optional[str] = Field(default=None, max_length=100)
    ps_details_sub_division: Optional[str] = Field(default=None, max_length=100)
    ps_details_ps_name: Optional[str] = Field(default=None, max_length=200)
    ps_details_entry_date: Optional[date] = None
    ps_details_last_fir_no: Optional[str] = Field(default=None, max_length=50)
    ps_details_last_fir_time: Optional[datetime] = None
    ps_details_gsc_no: Optional[str] = Field(default=None, max_length=50)
    zero_fir_no: Optional[str] = Field(default=None, max_length=50)

    # ── Section 2 — FIR Summary ───────────────────────────────────
    fir_summary: Optional[str] = None    # unbounded on API; server-side cap in submit path

    # ── Section 3 — Acts (aggregate) + acts[] ─────────────────────
    crime_classification_major: Optional[str] = Field(default=None, max_length=100)
    crime_classification_minor: Optional[str] = Field(default=None, max_length=100)
    offences_involve_aadhaar: Optional[bool] = None
    acts: Optional[List[FirActPayload]] = None   # None = leave alone; [] = clear

    # ── Section 4 — Time of Occurrence ───────────────────────────
    incident_from_at: Optional[datetime] = None
    incident_to_at: Optional[datetime] = None
    info_received_at_ps_at: Optional[datetime] = None
    mode_of_complaint: Optional[str] = Field(default=None, max_length=50)
    fir_case_type: Optional[str] = Field(default=None, max_length=30)
    shd_reference: Optional[str] = Field(default=None, max_length=100)
    reasons_for_delay: Optional[str] = None
    complainant_saw_occurrence: Optional[bool] = None

    # ── Section 5 — Place of Incident ────────────────────────────
    poi_house_no: Optional[str] = Field(default=None, max_length=100)
    poi_street: Optional[str] = Field(default=None, max_length=200)
    poi_colony: Optional[str] = Field(default=None, max_length=200)
    poi_beat_name: Optional[str] = Field(default=None, max_length=100)
    poi_village: Optional[str] = Field(default=None, max_length=200)
    poi_city: Optional[str] = Field(default=None, max_length=100)
    poi_tehsil: Optional[str] = Field(default=None, max_length=100)
    poi_district: Optional[str] = Field(default=None, max_length=100)
    poi_state: Optional[str] = Field(default=None, max_length=100)
    poi_country: Optional[str] = Field(default=None, max_length=100)
    poi_police_station: Optional[str] = Field(default=None, max_length=200)
    poi_pincode: Optional[str] = Field(default=None, max_length=20)
    poi_distance_from_ps: Optional[str] = Field(default=None, max_length=50)
    poi_direction_from_ps: Optional[str] = Field(default=None, max_length=20)
    poi_mla_constituency: Optional[str] = Field(default=None, max_length=150)
    poi_mp_constituency: Optional[str] = Field(default=None, max_length=150)
    poi_is_forest: Optional[bool] = None
    poi_is_sea: Optional[bool] = None
    poi_location_nature: Optional[str] = Field(default=None, max_length=30)
    poi_latitude: Optional[Decimal] = None
    poi_longitude: Optional[Decimal] = None
    poi_other_juris_state: Optional[str] = Field(default=None, max_length=100)
    poi_other_juris_district: Optional[str] = Field(default=None, max_length=100)
    poi_other_juris_ps: Optional[str] = Field(default=None, max_length=200)

    # ── Section 6 — Complainant / Informant ──────────────────────
    comp_relation_to_victim: Optional[str] = Field(default=None, max_length=50)
    comp_role: Optional[str] = Field(default=None, max_length=50)
    comp_first_name: Optional[str] = Field(default=None, max_length=100)
    comp_middle_name: Optional[str] = Field(default=None, max_length=100)
    comp_last_name: Optional[str] = Field(default=None, max_length=100)
    comp_dob: Optional[date] = None
    comp_age: Optional[int] = None
    comp_gender: Optional[str] = Field(default=None, max_length=20)
    comp_nationality: Optional[str] = Field(default=None, max_length=50)
    comp_occupation: Optional[str] = Field(default=None, max_length=100)
    comp_religion: Optional[str] = Field(default=None, max_length=50)
    comp_caste: Optional[str] = Field(default=None, max_length=50)
    comp_father_name: Optional[str] = Field(default=None, max_length=200)
    comp_mother_name: Optional[str] = Field(default=None, max_length=200)
    comp_uid_type: Optional[str] = Field(default=None, max_length=30)
    comp_uid_number: Optional[str] = Field(default=None, max_length=50)
    comp_aadhaar_ref_no: Optional[str] = Field(default=None, max_length=20)
    comp_email: Optional[str] = Field(default=None, max_length=200)
    comp_mobile: Optional[str] = Field(default=None, max_length=20)
    comp_alt_mobile: Optional[str] = Field(default=None, max_length=20)
    comp_address_house_no: Optional[str] = Field(default=None, max_length=100)
    comp_address_street: Optional[str] = Field(default=None, max_length=200)
    comp_address_city: Optional[str] = Field(default=None, max_length=100)
    comp_address_state: Optional[str] = Field(default=None, max_length=100)
    comp_address_pincode: Optional[str] = Field(default=None, max_length=20)
    comp_address_country: Optional[str] = Field(default=None, max_length=100)


# ── Read view — nested onto ComplaintDetail as `police_it_v2` ────


class FirEntryView(BaseModel):
    """Everything the FIR entry page needs to render sections 1-6.
    Composed onto ComplaintDetail as `police_it_v2`."""

    # Section 1
    ps_details_district: Optional[str] = None
    ps_details_sub_division: Optional[str] = None
    ps_details_ps_name: Optional[str] = None
    ps_details_entry_date: Optional[date] = None
    ps_details_last_fir_no: Optional[str] = None
    ps_details_last_fir_time: Optional[datetime] = None
    ps_details_gsc_no: Optional[str] = None
    zero_fir_no: Optional[str] = None

    # Section 2
    fir_summary: Optional[str] = None

    # Section 3
    crime_classification_major: Optional[str] = None
    crime_classification_minor: Optional[str] = None
    offences_involve_aadhaar: Optional[bool] = None
    acts: List[FirActView] = []

    # Section 4
    incident_from_at: Optional[datetime] = None
    incident_to_at: Optional[datetime] = None
    info_received_at_ps_at: Optional[datetime] = None
    mode_of_complaint: Optional[str] = None
    fir_case_type: Optional[str] = None
    shd_reference: Optional[str] = None
    reasons_for_delay: Optional[str] = None
    complainant_saw_occurrence: Optional[bool] = None

    # Section 5
    poi_house_no: Optional[str] = None
    poi_street: Optional[str] = None
    poi_colony: Optional[str] = None
    poi_beat_name: Optional[str] = None
    poi_village: Optional[str] = None
    poi_city: Optional[str] = None
    poi_tehsil: Optional[str] = None
    poi_district: Optional[str] = None
    poi_state: Optional[str] = None
    poi_country: Optional[str] = None
    poi_police_station: Optional[str] = None
    poi_pincode: Optional[str] = None
    poi_distance_from_ps: Optional[str] = None
    poi_direction_from_ps: Optional[str] = None
    poi_mla_constituency: Optional[str] = None
    poi_mp_constituency: Optional[str] = None
    poi_is_forest: Optional[bool] = None
    poi_is_sea: Optional[bool] = None
    poi_location_nature: Optional[str] = None
    poi_latitude: Optional[Decimal] = None
    poi_longitude: Optional[Decimal] = None
    poi_other_juris_state: Optional[str] = None
    poi_other_juris_district: Optional[str] = None
    poi_other_juris_ps: Optional[str] = None

    # Section 6
    comp_relation_to_victim: Optional[str] = None
    comp_role: Optional[str] = None
    comp_first_name: Optional[str] = None
    comp_middle_name: Optional[str] = None
    comp_last_name: Optional[str] = None
    comp_dob: Optional[date] = None
    comp_age: Optional[int] = None
    comp_gender: Optional[str] = None
    comp_nationality: Optional[str] = None
    comp_occupation: Optional[str] = None
    comp_religion: Optional[str] = None
    comp_caste: Optional[str] = None
    comp_father_name: Optional[str] = None
    comp_mother_name: Optional[str] = None
    comp_uid_type: Optional[str] = None
    comp_uid_number: Optional[str] = None
    comp_aadhaar_ref_no: Optional[str] = None
    comp_email: Optional[str] = None
    comp_mobile: Optional[str] = None
    comp_alt_mobile: Optional[str] = None
    comp_address_house_no: Optional[str] = None
    comp_address_street: Optional[str] = None
    comp_address_city: Optional[str] = None
    comp_address_state: Optional[str] = None
    comp_address_pincode: Optional[str] = None
    comp_address_country: Optional[str] = None
