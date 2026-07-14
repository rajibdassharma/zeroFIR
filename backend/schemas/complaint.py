"""Schemas for the complaint inbox + detail views.

The list endpoint returns `ComplaintListItem` rows for the inbox.
The detail endpoint returns `ComplaintDetail`, which composes the
NCRP-side data (`ncrp_data` view) and the Police-IT-V2-side data
(`police_it_v2_data` view). Both keyed on `acknowledgement_no`.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel

from schemas.fir_entry import FirEntryView


class ComplaintListItem(BaseModel):
    """One row on the operator's inbox — enough to scan + click into."""
    acknowledgement_no: str
    complainant_name: str
    complainant_mobile: str
    category: str | None = None
    total_fraud_amount: Decimal | None = None
    ps_id: int | None = None
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


class NcrpSuspectAccountView(BaseModel):
    id: str
    bank_wallet: str | None = None
    account_id: str | None = None
    ifsc_code: str | None = None
    account_holder_name: str | None = None
    amount_credited: Decimal | None = None
    credited_on: date | None = None
    remarks: str | None = None


class NcrpDataView(BaseModel):
    """Full read-only view of the NCRP-outbound row — everything
    that either came from NCRP or will go back to NCRP via APIs 2 / 5.
    Keyed on `acknowledgement_no`."""
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

    incident_place: str | None = None
    additional_information: str | None = None

    has_suspect_account_details: bool = False
    suspect_mobiles: List[str] = []
    transactions: List[NcrpTransactionView] = []
    suspect_accounts: List[NcrpSuspectAccountView] = []
    efir_answers: List[NcrpEfirAnswerView] = []
    received_at: datetime


class ComplaintDetail(BaseModel):
    """The full complaint — the two outbound bundles side by side plus
    the current workflow status. `ncrp_data` and `police_it_v2_data`
    both share the same `acknowledgement_no` key."""
    acknowledgement_no: str
    ps_id: int | None = None
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

    ncrp_data: NcrpDataView
    police_it_v2: FirEntryView   # Sections 1-6 the FIR-additional tabs write into
