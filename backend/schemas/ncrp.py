"""Schemas for NCRP API 1 — the receive-side of the NCRP → zeroFIR push.

NCRP posts a JSON body matching `NcrpComplaintPushRequest` to
`POST /api/v1/ncrp/complaints` with `X-API-Key` set. We validate,
normalise into typed columns + child tables, AND store the raw
payload for audit.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


# ── Sub-shapes ───────────────────────────────────────────────────


class NcrpTransactionPayload(BaseModel):
    sub_category: str | None = None
    bank_wallet: str | None = None
    account_id: str | None = None
    transaction_id: str | None = None
    transaction_date: date | None = None
    approx_time: str | None = None      # "09:37 PM"
    amount: Decimal | None = None
    reference_no: str | None = None
    other: str | None = None


class NcrpEfirAnswerPayload(BaseModel):
    question_code: str = Field(max_length=60)   # canonical slug or "unknown"
    question_text: str
    answer: bool


class NcrpSuspectAccountPayload(BaseModel):
    """NCRP Screen 2 — reveals when the caller toggles 'Do You have
    Suspect Account Details?' to Yes."""
    bank_wallet: str | None = Field(default=None, max_length=150)
    account_id: str | None = Field(default=None, max_length=60)
    ifsc_code: str | None = Field(default=None, max_length=20)
    account_holder_name: str | None = Field(default=None, max_length=200)
    amount_credited: Decimal | None = None
    credited_on: date | None = None
    remarks: str | None = Field(default=None, max_length=500)


class NcrpAddressPayload(BaseModel):
    house_no: str | None = None
    street: str | None = None
    colony: str | None = None
    city: str | None = None
    tehsil: str | None = None
    country: str | None = None
    state: str | None = None
    district: str | None = None
    police_station: str | None = None
    pincode: str | None = None


class NcrpComplainantPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    gender: str | None = None
    dob: date | None = None
    mobile: str = Field(min_length=1, max_length=20)
    email: str | None = None
    relation_type: str | None = None    # 'Father'|'Mother'|'Spouse'
    relation_name: str | None = None


# ── Top-level push body ───────────────────────────────────────────


class NcrpComplaintPushRequest(BaseModel):
    """Body NCRP posts to us. Structured so all fields NCRP asks the
    caller during 1930 / self-service intake land in one call."""
    acknowledgement_no: str = Field(min_length=1, max_length=60)
    category: str | None = None
    call_start_at: datetime | None = None

    complainant: NcrpComplainantPayload
    address: NcrpAddressPayload

    # NCRP Screen 1 "Where did the incident occur?" — value picked
    # from the incident_place dropdown (see seed_data.py).
    incident_place: str | None = Field(default=None, max_length=120)
    additional_information: str | None = Field(default=None, max_length=500)

    has_suspect_account_details: bool = False

    suspect_mobiles: List[str] = []
    transactions: List[NcrpTransactionPayload] = []
    suspect_accounts: List[NcrpSuspectAccountPayload] = []
    efir_answers: List[NcrpEfirAnswerPayload] = []


class NcrpComplaintPushResponse(BaseModel):
    """Ack we send back to NCRP. `acknowledgement_no` is the PK of
    both `ncrp_data` and `police_it_v2_data` — that's the correlator
    for future API 2 / 3 / 5 traffic and for the frontend's follow-up
    PATCH to `/api/v1/complaints/{ack_no}/v2-draft`."""
    ok: bool = True
    acknowledgement_no: str
    ps_id: int | None = None
    ps_matched: bool = False
    duplicate: bool = False
