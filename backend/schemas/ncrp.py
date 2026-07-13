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

    incident_occurred_at: str | None = None
    additional_information: str | None = Field(default=None, max_length=500)

    suspect_mobiles: List[str] = []
    transactions: List[NcrpTransactionPayload] = []
    efir_answers: List[NcrpEfirAnswerPayload] = []


class NcrpComplaintPushResponse(BaseModel):
    """Ack we send back to NCRP. Includes our own complaint id so
    NCRP can correlate later API 2 / API 5 traffic."""
    ok: bool = True
    complaint_id: str
    ps_id: int | None = None
    ps_matched: bool = False
    duplicate: bool = False
