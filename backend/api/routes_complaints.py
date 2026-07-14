"""Internal complaint entry routes (Call-Centre only).

Two endpoints — both keyed on `acknowledgement_no`:
  - `POST   /api/v1/complaints`             — create a complaint
    from a phone call (mirrors what NCRP would push over API 1).
  - `PATCH  /api/v1/complaints/{ack_no}`    — edit an existing
    complaint's NCRP fields + child collections.

Both require an authenticated `call_center` user. The API-1-facing
`POST /api/v1/ncrp/complaints` in `routes_ncrp.py` stays as-is and
is guarded only by the shared `X-API-Key` — the two endpoints are
intentionally isolated (JWT users cannot mint via API 1 and vice
versa).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import CurrentUser, get_current_user
from database import get_db
from models.ncrp_data import NcrpData
from models.ncrp_efir_answer import NcrpEfirAnswer, QUESTION_CODES
from models.ncrp_suspect_account import NcrpSuspectAccount
from models.ncrp_suspect_mobile import NcrpSuspectMobile
from models.ncrp_transaction import NcrpTransaction
from models.police_it_v2_data import PoliceITV2Data
from schemas.ncrp import NcrpComplaintPushRequest, NcrpComplaintPushResponse
from services.ncrp_persistence import (
    create_complaint_from_payload,
    resolve_ps_id,
)


router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])


def _require_cc(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Only call_center may enter or edit complaints. Kept as its own
    dep so future roles (supervisor, auditor) can be added by
    widening the check in one place."""
    if user.role != "call_center":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Call-Centre operators can enter or edit NCRP data.",
        )
    return user


# ── Create ───────────────────────────────────────────────────────


@router.post("", response_model=NcrpComplaintPushResponse)
async def create_complaint(
    body: NcrpComplaintPushRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(_require_cc),
) -> NcrpComplaintPushResponse:
    """Call-Centre operator creates a complaint from a phone call.
    Same payload shape as API 1 (`NcrpComplaintPushRequest`) — the
    operator picks the acknowledgement_no themselves (KSP call-centre
    numbering scheme; NCRP-side ack_nos have their own prefix). Same
    idempotency guarantee: reusing an ack_no returns the existing
    row with `duplicate=True`."""
    ncrp, ps_id, duplicate = await create_complaint_from_payload(db, body)
    if not duplicate:
        await db.commit()
    return NcrpComplaintPushResponse(
        ok=True,
        acknowledgement_no=ncrp.acknowledgement_no,
        ps_id=ps_id,
        ps_matched=ps_id is not None,
        duplicate=duplicate,
    )


# ── Edit (NCRP side) ─────────────────────────────────────────────


@router.patch("/{ack_no}", response_model=NcrpComplaintPushResponse)
async def edit_complaint(
    ack_no: str,
    body: NcrpComplaintPushRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(_require_cc),
) -> NcrpComplaintPushResponse:
    """Full-replace edit of the NCRP-side fields — the caller sends
    the desired end state of ALL fields (same shape as create).
    Child collections (suspect_mobiles, transactions, suspect_accounts,
    efir_answers) are replaced wholesale, not merged. Simplifies both
    the client (always holds full form state) and the server (no diff
    logic).

    If `body.acknowledgement_no` changes vs. the URL param we reject
    — the URL is the source of truth, no rename via body.

    If the address's `police_station` changes and now resolves to a
    different PS, both the `ncrp_data.ps_id` and the mirrored
    `police_it_v2_data.ps_id` update — but only while status is
    RECEIVED / IN_PROGRESS. Once an FIR has been created or
    transferred, moving would corrupt downstream audit; block and
    require an explicit transfer instead."""
    ncrp = (
        await db.execute(
            select(NcrpData).where(NcrpData.acknowledgement_no == ack_no)
        )
    ).scalar_one_or_none()
    if ncrp is None:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    if body.acknowledgement_no != ack_no:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change acknowledgement_no on edit (URL is source of truth).",
        )

    # ── Scalar field updates ─────────────────────────────────────
    ncrp.category = body.category
    ncrp.call_start_at = body.call_start_at

    ncrp.complainant_name = body.complainant.name
    ncrp.complainant_gender = body.complainant.gender
    ncrp.complainant_dob = body.complainant.dob
    ncrp.complainant_mobile = body.complainant.mobile
    ncrp.complainant_email = body.complainant.email
    ncrp.complainant_relation_type = body.complainant.relation_type
    ncrp.complainant_relation_name = body.complainant.relation_name

    ncrp.address_house_no = body.address.house_no
    ncrp.address_street = body.address.street
    ncrp.address_colony = body.address.colony
    ncrp.address_city = body.address.city
    ncrp.address_tehsil = body.address.tehsil
    ncrp.address_country = body.address.country
    ncrp.address_state = body.address.state
    ncrp.address_district = body.address.district
    ncrp.address_ps_name = body.address.police_station
    ncrp.address_pincode = body.address.pincode

    ncrp.incident_place = body.incident_place
    ncrp.additional_information = body.additional_information
    ncrp.has_suspect_account_details = body.has_suspect_account_details

    # ── PS re-resolve (only if the PS name changed) ──────────────
    new_ps_id = ncrp.ps_id
    if body.address.police_station != ncrp.address_ps_name or ncrp.ps_id is None:
        new_ps_id = await resolve_ps_id(db, body.address.police_station)
        if new_ps_id != ncrp.ps_id:
            v2 = (
                await db.execute(
                    select(PoliceITV2Data).where(
                        PoliceITV2Data.acknowledgement_no == ncrp.acknowledgement_no
                    )
                )
            ).scalar_one_or_none()
            if v2 is not None and v2.status not in {"RECEIVED", "IN_PROGRESS"}:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Cannot re-anchor PS on a complaint in state "
                        f"'{v2.status}'. Use the transfer workflow instead."
                    ),
                )
            ncrp.ps_id = new_ps_id
            if v2 is not None:
                v2.ps_id = new_ps_id

    # ── Replace child collections wholesale ──────────────────────
    await db.execute(
        NcrpSuspectMobile.__table__.delete().where(
            NcrpSuspectMobile.acknowledgement_no == ncrp.acknowledgement_no
        )
    )
    await db.execute(
        NcrpTransaction.__table__.delete().where(
            NcrpTransaction.acknowledgement_no == ncrp.acknowledgement_no
        )
    )
    await db.execute(
        NcrpSuspectAccount.__table__.delete().where(
            NcrpSuspectAccount.acknowledgement_no == ncrp.acknowledgement_no
        )
    )
    await db.execute(
        NcrpEfirAnswer.__table__.delete().where(
            NcrpEfirAnswer.acknowledgement_no == ncrp.acknowledgement_no
        )
    )

    for mobile in body.suspect_mobiles:
        if mobile.strip():
            db.add(NcrpSuspectMobile(
                acknowledgement_no=ncrp.acknowledgement_no, mobile=mobile.strip(),
            ))
    for t in body.transactions:
        db.add(NcrpTransaction(
            acknowledgement_no=ncrp.acknowledgement_no,
            sub_category=t.sub_category,
            bank_wallet=t.bank_wallet,
            account_id=t.account_id,
            transaction_id=t.transaction_id,
            transaction_date=t.transaction_date,
            approx_time=t.approx_time,
            amount=t.amount,
            reference_no=t.reference_no,
            other=t.other,
        ))
    for sa in body.suspect_accounts:
        db.add(NcrpSuspectAccount(
            acknowledgement_no=ncrp.acknowledgement_no,
            bank_wallet=sa.bank_wallet,
            account_id=sa.account_id,
            ifsc_code=sa.ifsc_code,
            account_holder_name=sa.account_holder_name,
            amount_credited=sa.amount_credited,
            credited_on=sa.credited_on,
            remarks=sa.remarks,
        ))
    for a in body.efir_answers:
        code = a.question_code if a.question_code in QUESTION_CODES else "unknown"
        db.add(NcrpEfirAnswer(
            acknowledgement_no=ncrp.acknowledgement_no,
            question_code=code,
            question_text=a.question_text,
            answer=a.answer,
        ))

    await db.commit()

    return NcrpComplaintPushResponse(
        ok=True,
        acknowledgement_no=ncrp.acknowledgement_no,
        ps_id=ncrp.ps_id,
        ps_matched=ncrp.ps_id is not None,
        duplicate=False,
    )
