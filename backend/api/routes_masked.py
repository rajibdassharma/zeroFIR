"""Masking Application routes — the officer-facing inbox + detail view.

Phase 1a scope:
- List complaints scoped by role (super_admin sees all, PS-scoped
  roles see their own PS).
- Detail view merges the read-only NCRP data + the current Masking
  Application row.

Full FIR-entry mutations, save-as-draft, and status transitions land
in Phase 1b.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import CurrentUser, get_current_user
from database import get_db
from models.masked_application import MaskedApplication, STATUS_VALUES
from models.ncrp_complaint import NcrpComplaint
from models.ncrp_efir_answer import NcrpEfirAnswer
from models.ncrp_suspect_mobile import NcrpSuspectMobile
from models.ncrp_transaction import NcrpTransaction
from models.police_station import PoliceStation
from schemas.masked_application import (
    MaskedApplicationDetail,
    MaskedApplicationListItem,
    NcrpComplaintView,
    NcrpEfirAnswerView,
    NcrpTransactionView,
)


router = APIRouter(prefix="/api/v1/masked-applications", tags=["masked-applications"])


def _require_ps_id(user: CurrentUser) -> int:
    """Non-super_admin routes NEED a ps_id in the token — reject
    early rather than return an empty list (which would look like
    a data bug to the operator)."""
    if user.ps_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "User is not attached to a Police Station. "
                "Contact the super admin to complete provisioning."
            ),
        )
    return user.ps_id


def _scope_by_role(query, user: CurrentUser):
    """super_admin sees everything, everyone else is pinned to
    their JWT's ps_id. Phase 1b adds finer per-role scoping once
    the KSP role list is locked."""
    if user.role == "super_admin":
        return query
    return query.where(MaskedApplication.ps_id == _require_ps_id(user))


@router.get("", response_model=List[MaskedApplicationListItem])
async def list_masked_applications(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Inbox — one row per Masking Application, joined to the
    complaint + PS so the frontend renders without a second call."""
    if status_filter is not None and status_filter not in STATUS_VALUES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown status '{status_filter}'.",
        )

    # Aggregate transaction totals in the same query — fine at
    # Phase 1a volumes; revisit if we ever cross tens of thousands.
    txn_sum = (
        select(
            NcrpTransaction.complaint_id.label("complaint_id"),
            func.coalesce(func.sum(NcrpTransaction.amount), 0).label("total_amount"),
        )
        .group_by(NcrpTransaction.complaint_id)
        .subquery()
    )

    q = (
        select(
            MaskedApplication.id,
            MaskedApplication.complaint_id,
            MaskedApplication.status,
            MaskedApplication.ps_id,
            NcrpComplaint.acknowledgement_no,
            NcrpComplaint.complainant_name,
            NcrpComplaint.complainant_mobile,
            NcrpComplaint.category,
            NcrpComplaint.received_at,
            PoliceStation.name.label("ps_name"),
            txn_sum.c.total_amount,
        )
        .select_from(MaskedApplication)
        .join(NcrpComplaint, MaskedApplication.complaint_id == NcrpComplaint.id)
        .join(PoliceStation, MaskedApplication.ps_id == PoliceStation.id)
        .join(txn_sum, txn_sum.c.complaint_id == NcrpComplaint.id, isouter=True)
        .order_by(NcrpComplaint.received_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status_filter is not None:
        q = q.where(MaskedApplication.status == status_filter)

    q = _scope_by_role(q, user)

    rows = (await db.execute(q)).all()
    return [
        MaskedApplicationListItem(
            id=r.id,
            complaint_id=r.complaint_id,
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


async def _load_complaint_view(db: AsyncSession, complaint_id: str) -> NcrpComplaintView:
    complaint = (
        await db.execute(
            select(NcrpComplaint).where(NcrpComplaint.id == complaint_id)
        )
    ).scalar_one_or_none()
    if complaint is None:
        raise HTTPException(status_code=404, detail="NCRP complaint not found.")

    mobiles = (
        await db.execute(
            select(NcrpSuspectMobile.mobile)
            .where(NcrpSuspectMobile.complaint_id == complaint_id)
            .order_by(NcrpSuspectMobile.created_at)
        )
    ).scalars().all()

    txns = (
        await db.execute(
            select(NcrpTransaction)
            .where(NcrpTransaction.complaint_id == complaint_id)
            .order_by(NcrpTransaction.transaction_date)
        )
    ).scalars().all()

    answers = (
        await db.execute(
            select(NcrpEfirAnswer)
            .where(NcrpEfirAnswer.complaint_id == complaint_id)
            .order_by(NcrpEfirAnswer.question_code)
        )
    ).scalars().all()

    return NcrpComplaintView(
        id=complaint.id,
        acknowledgement_no=complaint.acknowledgement_no,
        category=complaint.category,
        call_start_at=complaint.call_start_at,
        complainant_name=complaint.complainant_name,
        complainant_gender=complaint.complainant_gender,
        complainant_dob=complaint.complainant_dob,
        complainant_mobile=complaint.complainant_mobile,
        complainant_email=complaint.complainant_email,
        complainant_relation_type=complaint.complainant_relation_type,
        complainant_relation_name=complaint.complainant_relation_name,
        address_house_no=complaint.address_house_no,
        address_street=complaint.address_street,
        address_colony=complaint.address_colony,
        address_city=complaint.address_city,
        address_tehsil=complaint.address_tehsil,
        address_country=complaint.address_country,
        address_state=complaint.address_state,
        address_district=complaint.address_district,
        address_ps_name=complaint.address_ps_name,
        address_pincode=complaint.address_pincode,
        incident_occurred_at=complaint.incident_occurred_at,
        additional_information=complaint.additional_information,
        suspect_mobiles=list(mobiles),
        transactions=[
            NcrpTransactionView(
                id=t.id,
                sub_category=t.sub_category,
                bank_wallet=t.bank_wallet,
                account_id=t.account_id,
                transaction_id=t.transaction_id,
                transaction_date=t.transaction_date,
                approx_time=t.approx_time,
                amount=t.amount,
                reference_no=t.reference_no,
                other=t.other,
            )
            for t in txns
        ],
        efir_answers=[
            NcrpEfirAnswerView(
                id=a.id,
                question_code=a.question_code,
                question_text=a.question_text,
                answer=a.answer,
            )
            for a in answers
        ],
        received_at=complaint.received_at,
    )


@router.get("/{application_id}", response_model=MaskedApplicationDetail)
async def get_masked_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    row = (
        await db.execute(
            select(MaskedApplication, PoliceStation.name.label("ps_name"))
            .join(PoliceStation, MaskedApplication.ps_id == PoliceStation.id)
            .where(MaskedApplication.id == application_id)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Masking Application not found.")

    ma, ps_name = row
    if user.role != "super_admin" and ma.ps_id != _require_ps_id(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This Masking Application belongs to a different Police Station.",
        )

    # Total fraud amount = sum of NCRP-declared transaction amounts.
    total_amount = (
        await db.execute(
            select(func.coalesce(func.sum(NcrpTransaction.amount), 0))
            .where(NcrpTransaction.complaint_id == ma.complaint_id)
        )
    ).scalar_one()

    complaint_view = await _load_complaint_view(db, ma.complaint_id)

    return MaskedApplicationDetail(
        id=ma.id,
        ps_id=ma.ps_id,
        ps_name=ps_name,
        picked_up_by=ma.picked_up_by,
        picked_up_at=ma.picked_up_at,
        status=ma.status,
        total_fraud_amount=Decimal(str(total_amount)) if total_amount is not None else None,
        above_threshold=ma.above_threshold,
        threshold_at_decision=ma.threshold_at_decision,
        within_karnataka_jurisdiction=ma.within_karnataka_jurisdiction,
        zero_fir_no=ma.zero_fir_no,
        v2_fir_no=ma.v2_fir_no,
        fir_summary=ma.fir_summary,
        efir_pushed_at=ma.efir_pushed_at,
        notice_lien_pulled_at=ma.notice_lien_pulled_at,
        registered_pushed_at=ma.registered_pushed_at,
        created_at=ma.created_at,
        updated_at=ma.updated_at,
        complaint=complaint_view,
    )
