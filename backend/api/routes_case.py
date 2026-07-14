"""Case-query routes — the operator's inbox and per-complaint detail
view, plus the V2-draft PATCH the NCRP-entry screen uses to persist
Section 1-6 fields.

Every URL is keyed on `acknowledgement_no` (both `ncrp_data` and
`police_it_v2_data` share it as PK).
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import CurrentUser, get_current_user
from database import get_db
from models.ncrp_data import NcrpData
from models.ncrp_efir_answer import NcrpEfirAnswer
from models.ncrp_suspect_account import NcrpSuspectAccount
from models.ncrp_suspect_mobile import NcrpSuspectMobile
from models.ncrp_transaction import NcrpTransaction
from models.police_it_v2_act import PoliceITV2Act
from models.police_it_v2_data import PoliceITV2Data, STATUS_VALUES
from models.police_station import PoliceStation
from schemas.complaint import (
    ComplaintDetail,
    ComplaintListItem,
    NcrpDataView,
    NcrpEfirAnswerView,
    NcrpSuspectAccountView,
    NcrpTransactionView,
)
from schemas.fir_entry import FirActView, FirDraftUpdate, FirEntryView
from services.outbound import push_ncrp_data, push_police_it_v2_data


router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])


# States from which Submit is allowed. Once a case has moved past
# these (transferred, closed, cancelled) re-submitting would corrupt
# downstream audit — block and require an explicit state transition.
_SUBMITTABLE_FROM = frozenset({"RECEIVED", "IN_PROGRESS"})


# ── List (inbox) ─────────────────────────────────────────────────


@router.get("", response_model=List[ComplaintListItem])
async def list_complaints(
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Every authenticated user (call-centre operator) sees the full
    state-wide inbox — one row per ack_no."""
    if status_filter is not None and status_filter not in STATUS_VALUES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown status '{status_filter}'.",
        )

    # Sum transaction amounts per complaint in a single scan.
    txn_sum = (
        select(
            NcrpTransaction.acknowledgement_no.label("ack_no"),
            func.coalesce(func.sum(NcrpTransaction.amount), 0).label("total_amount"),
        )
        .group_by(NcrpTransaction.acknowledgement_no)
        .subquery()
    )

    q = (
        select(
            NcrpData.acknowledgement_no,
            NcrpData.complainant_name,
            NcrpData.complainant_mobile,
            NcrpData.category,
            NcrpData.received_at,
            PoliceITV2Data.status,
            PoliceITV2Data.ps_id,
            PoliceStation.name.label("ps_name"),
            txn_sum.c.total_amount,
        )
        .select_from(NcrpData)
        .join(PoliceITV2Data, PoliceITV2Data.acknowledgement_no == NcrpData.acknowledgement_no)
        .join(PoliceStation, PoliceITV2Data.ps_id == PoliceStation.id, isouter=True)
        .join(txn_sum, txn_sum.c.ack_no == NcrpData.acknowledgement_no, isouter=True)
        .order_by(NcrpData.received_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status_filter is not None:
        q = q.where(PoliceITV2Data.status == status_filter)

    rows = (await db.execute(q)).all()
    return [
        ComplaintListItem(
            acknowledgement_no=r.acknowledgement_no,
            complainant_name=r.complainant_name,
            complainant_mobile=r.complainant_mobile,
            category=r.category,
            total_fraud_amount=(
                Decimal(str(r.total_amount)) if r.total_amount is not None else None
            ),
            ps_id=r.ps_id,
            ps_name=r.ps_name,
            status=r.status,
            received_at=r.received_at,
        )
        for r in rows
    ]


# ── Detail ───────────────────────────────────────────────────────


async def _load_ncrp_view(db: AsyncSession, ack_no: str) -> NcrpDataView:
    ncrp = (
        await db.execute(
            select(NcrpData).where(NcrpData.acknowledgement_no == ack_no)
        )
    ).scalar_one_or_none()
    if ncrp is None:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    mobiles = (
        await db.execute(
            select(NcrpSuspectMobile.mobile)
            .where(NcrpSuspectMobile.acknowledgement_no == ack_no)
            .order_by(NcrpSuspectMobile.created_at)
        )
    ).scalars().all()

    txns = (
        await db.execute(
            select(NcrpTransaction)
            .where(NcrpTransaction.acknowledgement_no == ack_no)
            .order_by(NcrpTransaction.transaction_date)
        )
    ).scalars().all()

    answers = (
        await db.execute(
            select(NcrpEfirAnswer)
            .where(NcrpEfirAnswer.acknowledgement_no == ack_no)
            .order_by(NcrpEfirAnswer.question_code)
        )
    ).scalars().all()

    sus_accts = (
        await db.execute(
            select(NcrpSuspectAccount)
            .where(NcrpSuspectAccount.acknowledgement_no == ack_no)
            .order_by(NcrpSuspectAccount.created_at)
        )
    ).scalars().all()

    return NcrpDataView(
        acknowledgement_no=ncrp.acknowledgement_no,
        category=ncrp.category,
        call_start_at=ncrp.call_start_at,
        complainant_name=ncrp.complainant_name,
        complainant_gender=ncrp.complainant_gender,
        complainant_dob=ncrp.complainant_dob,
        complainant_mobile=ncrp.complainant_mobile,
        complainant_email=ncrp.complainant_email,
        complainant_relation_type=ncrp.complainant_relation_type,
        complainant_relation_name=ncrp.complainant_relation_name,
        address_house_no=ncrp.address_house_no,
        address_street=ncrp.address_street,
        address_colony=ncrp.address_colony,
        address_city=ncrp.address_city,
        address_tehsil=ncrp.address_tehsil,
        address_country=ncrp.address_country,
        address_state=ncrp.address_state,
        address_district=ncrp.address_district,
        address_ps_name=ncrp.address_ps_name,
        address_pincode=ncrp.address_pincode,
        incident_place=ncrp.incident_place,
        additional_information=ncrp.additional_information,
        has_suspect_account_details=ncrp.has_suspect_account_details,
        suspect_mobiles=list(mobiles),
        transactions=[
            NcrpTransactionView(
                id=t.id, sub_category=t.sub_category, bank_wallet=t.bank_wallet,
                account_id=t.account_id, transaction_id=t.transaction_id,
                transaction_date=t.transaction_date, approx_time=t.approx_time,
                amount=t.amount, reference_no=t.reference_no, other=t.other,
            )
            for t in txns
        ],
        suspect_accounts=[
            NcrpSuspectAccountView(
                id=sa.id, bank_wallet=sa.bank_wallet, account_id=sa.account_id,
                ifsc_code=sa.ifsc_code, account_holder_name=sa.account_holder_name,
                amount_credited=sa.amount_credited, credited_on=sa.credited_on,
                remarks=sa.remarks,
            )
            for sa in sus_accts
        ],
        efir_answers=[
            NcrpEfirAnswerView(
                id=a.id, question_code=a.question_code,
                question_text=a.question_text, answer=a.answer,
            )
            for a in answers
        ],
        received_at=ncrp.received_at,
    )


# Fields on PoliceITV2Data that FirDraftUpdate can write.
_V2_DIRECT_FIELDS = frozenset(FirDraftUpdate.model_fields.keys()) - {"acts"}


async def _build_detail(db: AsyncSession, v2: PoliceITV2Data) -> ComplaintDetail:
    """Shared assembler for GET /{ack_no}, PATCH v2-draft, and POST
    /{ack_no}/submit. Returns the composed ComplaintDetail."""
    ack_no = v2.acknowledgement_no
    ps_name = None
    if v2.ps_id is not None:
        ps_name = (
            await db.execute(
                select(PoliceStation.name).where(PoliceStation.id == v2.ps_id)
            )
        ).scalar_one_or_none()
    total_amount = (
        await db.execute(
            select(func.coalesce(func.sum(NcrpTransaction.amount), 0))
            .where(NcrpTransaction.acknowledgement_no == ack_no)
        )
    ).scalar_one()
    ncrp_view = await _load_ncrp_view(db, ack_no)
    v2_view = await _build_v2_view(db, v2)

    return ComplaintDetail(
        acknowledgement_no=v2.acknowledgement_no,
        ps_id=v2.ps_id,
        ps_name=ps_name,
        picked_up_by=v2.picked_up_by,
        picked_up_at=v2.picked_up_at,
        status=v2.status,
        total_fraud_amount=Decimal(str(total_amount)) if total_amount is not None else None,
        above_threshold=v2.above_threshold,
        threshold_at_decision=v2.threshold_at_decision,
        within_karnataka_jurisdiction=v2.within_karnataka_jurisdiction,
        zero_fir_no=v2.zero_fir_no,
        v2_fir_no=v2.v2_fir_no,
        fir_summary=v2.fir_summary,
        efir_pushed_at=v2.efir_pushed_at,
        notice_lien_pulled_at=v2.notice_lien_pulled_at,
        registered_pushed_at=v2.registered_pushed_at,
        created_at=v2.created_at,
        updated_at=v2.updated_at,
        ncrp_data=ncrp_view,
        police_it_v2=v2_view,
    )


async def _build_v2_view(db: AsyncSession, v2: PoliceITV2Data) -> FirEntryView:
    acts = (
        await db.execute(
            select(PoliceITV2Act)
            .where(PoliceITV2Act.acknowledgement_no == v2.acknowledgement_no)
            .order_by(PoliceITV2Act.created_at)
        )
    ).scalars().all()
    payload: dict = {
        name: getattr(v2, name) for name in _V2_DIRECT_FIELDS if hasattr(v2, name)
    }
    payload["acts"] = [
        FirActView(
            id=a.id, act_code=a.act_code, act_name=a.act_name,
            sections=a.sections, offence_type=a.offence_type, gravity=a.gravity,
        )
        for a in acts
    ]
    return FirEntryView(**payload)


@router.get("/{ack_no}", response_model=ComplaintDetail)
async def get_complaint(
    ack_no: str,
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    row = (
        await db.execute(
            select(PoliceITV2Data, PoliceStation.name.label("ps_name"))
            .join(PoliceStation, PoliceITV2Data.ps_id == PoliceStation.id, isouter=True)
            .where(PoliceITV2Data.acknowledgement_no == ack_no)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    v2, _ = row
    return await _build_detail(db, v2)


# ── V2 draft PATCH (writes Section 1-6 fields into police_it_v2_data) ─


@router.patch("/{ack_no}/v2-draft", response_model=ComplaintDetail)
async def save_v2_draft(
    ack_no: str,
    body: FirDraftUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """PATCH sections 1-6 of the FIR entry form. Fields absent from
    the body are left untouched. `acts` (if provided) fully replaces
    the child rows for this complaint — the frontend always sends
    the current desired list."""
    v2 = (
        await db.execute(
            select(PoliceITV2Data).where(PoliceITV2Data.acknowledgement_no == ack_no)
        )
    ).scalar_one_or_none()
    if v2 is None:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    # Apply scalar fields — only those the caller explicitly set
    # (Pydantic v2 `exclude_unset` keeps us from wiping unrelated columns).
    updates = body.model_dump(exclude_unset=True)
    acts_update = updates.pop("acts", None)
    for field, value in updates.items():
        setattr(v2, field, value)

    # Replace acts child rows if the caller sent an `acts` key.
    if acts_update is not None:
        await db.execute(
            PoliceITV2Act.__table__.delete().where(
                PoliceITV2Act.acknowledgement_no == v2.acknowledgement_no
            )
        )
        for row_ in acts_update:
            db.add(PoliceITV2Act(
                acknowledgement_no=v2.acknowledgement_no,
                act_code=row_.get("act_code"),
                act_name=row_.get("act_name"),
                sections=row_.get("sections"),
                offence_type=row_.get("offence_type"),
                gravity=row_.get("gravity"),
            ))

    # Advance workflow status on first save.
    if v2.status == "RECEIVED":
        v2.status = "IN_PROGRESS"
        if v2.picked_up_by is None:
            v2.picked_up_by = user.user_id
            v2.picked_up_at = datetime.now(tz=timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(v2)
    return await _build_detail(db, v2)


# ── Submit (fires outbound placeholders + advances status) ────────


@router.post("/{ack_no}/submit", response_model=ComplaintDetail)
async def submit_complaint(
    ack_no: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Final Submit action — fires the two outbound APIs (placeholders
    today) and advances status to SUBMITTED. The frontend calls this
    AFTER a full Save so any pending edits are already persisted.

    Blocks re-submit after the case has moved past IN_PROGRESS (a
    transferred / registered / cancelled case can't be re-submitted;
    dedicated state transitions land in Phase 1b.3)."""
    v2 = (
        await db.execute(
            select(PoliceITV2Data).where(PoliceITV2Data.acknowledgement_no == ack_no)
        )
    ).scalar_one_or_none()
    if v2 is None:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    if v2.status not in _SUBMITTABLE_FROM:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot submit — complaint is in state '{v2.status}'.",
        )

    # Both outbound placeholders — real HTTP calls land here in
    # Phase 1b.3 when NCRP + V2 endpoints are up.
    await push_ncrp_data(db, ack_no)
    await push_police_it_v2_data(db, ack_no)

    v2.status = "SUBMITTED"
    if v2.picked_up_by is None:
        v2.picked_up_by = user.user_id
        v2.picked_up_at = datetime.now(tz=timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(v2)
    return await _build_detail(db, v2)
