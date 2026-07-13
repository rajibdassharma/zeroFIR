"""Schemas for the Masking Application UI — complaints inbox + detail."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel


class MaskedApplicationListItem(BaseModel):
    """One row on the operator's inbox — enough to scan + click into."""
    id: str
    complaint_id: str
    acknowledgement_no: str
    complainant_name: str
    complainant_mobile: str
    category: str | None = None
    total_fraud_amount: Decimal | None = None
    ps_id: int
    ps_name: str | None = None
    status: str
    received_at: datetime


class NcrpTransactionView(BaseModel):
    id: str
    sub_category: str | None = None
    bank_wallet: str | None = None
    account_id: str | None = None
    transaction_id: str | None = None
    transaction_date: date | None = None
    approx_time: str | None = None
    amount: Decimal | None = None
    reference_no: str | None = None
    other: str | None = None


class NcrpEfirAnswerView(BaseModel):
    id: str
    question_code: str
    question_text: str
    answer: bool


class NcrpComplaintView(BaseModel):
    """Full read-only view of the NCRP data — everything API 1 sent
    us, split into typed columns + child collections. This is the top
    half of the Masking App screen."""
    id: str
    acknowledgement_no: str
    category: str | None = None
    call_start_at: datetime | None = None

    complainant_name: str
    complainant_gender: str | None = None
    complainant_dob: date | None = None
    complainant_mobile: str
    complainant_email: str | None = None
    complainant_relation_type: str | None = None
    complainant_relation_name: str | None = None

    address_house_no: str | None = None
    address_street: str | None = None
    address_colony: str | None = None
    address_city: str | None = None
    address_tehsil: str | None = None
    address_country: str | None = None
    address_state: str | None = None
    address_district: str | None = None
    address_ps_name: str | None = None
    address_pincode: str | None = None

    incident_occurred_at: str | None = None
    additional_information: str | None = None

    suspect_mobiles: List[str] = []
    transactions: List[NcrpTransactionView] = []
    efir_answers: List[NcrpEfirAnswerView] = []
    received_at: datetime


class MaskedApplicationDetail(BaseModel):
    """The whole screen — NCRP data (read-only) + Masking status +
    what the officer has filled in so far."""
    id: str
    ps_id: int
    ps_name: str | None = None
    picked_up_by: int | None = None
    picked_up_at: datetime | None = None

    status: str

    total_fraud_amount: Decimal | None = None
    above_threshold: bool | None = None
    threshold_at_decision: Decimal | None = None
    within_karnataka_jurisdiction: bool | None = None

    zero_fir_no: str | None = None
    v2_fir_no: str | None = None
    fir_summary: str | None = None

    efir_pushed_at: datetime | None = None
    notice_lien_pulled_at: datetime | None = None
    registered_pushed_at: datetime | None = None

    created_at: datetime
    updated_at: datetime

    complaint: NcrpComplaintView
