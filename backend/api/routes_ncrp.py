"""NCRP-side receiving routes.

**API 1** — `POST /api/v1/ncrp/complaints` — NCRP pushes a complaint
here. Authenticated via shared static `X-API-Key` header (value from
`ZFIR_NCRP_API_KEY` env var). If the env var is empty the endpoint
returns 503 so nobody accidentally runs it without setting the key.

Idempotent on `acknowledgement_no` — if NCRP retries the same
complaint we return the existing `complaint_id` with `duplicate=True`
rather than creating a second row. The Masking Application row is
created once, at first receive.
"""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.masked_application import MaskedApplication
from models.ncrp_complaint import NcrpComplaint
from models.ncrp_efir_answer import NcrpEfirAnswer, QUESTION_CODES
from models.ncrp_suspect_mobile import NcrpSuspectMobile
from models.ncrp_transaction import NcrpTransaction
from models.police_station import PoliceStation
from schemas.ncrp import NcrpComplaintPushRequest, NcrpComplaintPushResponse


router = APIRouter(prefix="/api/v1/ncrp", tags=["ncrp"])


async def require_ncrp_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Guard for the NCRP-facing endpoint. Constant-time compare so
    timing analysis can't shortcut the key. Returns 503 (not 401) if
    the server hasn't been configured with a key — better to fail loud
    than to look like an active-but-broken endpoint."""
    if not settings.NCRP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NCRP receiver not configured on this deployment.",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.NCRP_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key.",
        )


async def _resolve_ps_id(db: AsyncSession, ps_name: str | None) -> int | None:
    """Try to match NCRP's free-text PS name to a seed row. Best-effort
    exact match today — Phase 1c will add a fuzzier resolver + the
    triage screen for unresolved complaints."""
    if not ps_name:
        return None
    row = (
        await db.execute(
            select(PoliceStation.id).where(PoliceStation.name == ps_name.strip())
        )
    ).scalar_one_or_none()
    return int(row) if row is not None else None


@router.post(
    "/complaints",
    response_model=NcrpComplaintPushResponse,
    dependencies=[Depends(require_ncrp_api_key)],
)
async def receive_complaint(
    body: NcrpComplaintPushRequest,
    db: AsyncSession = Depends(get_db),
) -> NcrpComplaintPushResponse:
    # Idempotency — if NCRP retries, echo back the existing row.
    existing = (
        await db.execute(
            select(NcrpComplaint).where(
                NcrpComplaint.acknowledgement_no == body.acknowledgement_no
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return NcrpComplaintPushResponse(
            ok=True,
            complaint_id=existing.id,
            ps_id=existing.ps_id,
            ps_matched=existing.ps_id is not None,
            duplicate=True,
        )

    ps_id = await _resolve_ps_id(db, body.address.police_station)

    complaint = NcrpComplaint(
        acknowledgement_no=body.acknowledgement_no,
        category=body.category,
        call_start_at=body.call_start_at,

        complainant_name=body.complainant.name,
        complainant_gender=body.complainant.gender,
        complainant_dob=body.complainant.dob,
        complainant_mobile=body.complainant.mobile,
        complainant_email=body.complainant.email,
        complainant_relation_type=body.complainant.relation_type,
        complainant_relation_name=body.complainant.relation_name,

        address_house_no=body.address.house_no,
        address_street=body.address.street,
        address_colony=body.address.colony,
        address_city=body.address.city,
        address_tehsil=body.address.tehsil,
        address_country=body.address.country,
        address_state=body.address.state,
        address_district=body.address.district,
        address_ps_name=body.address.police_station,
        address_pincode=body.address.pincode,

        incident_occurred_at=body.incident_occurred_at,
        additional_information=body.additional_information,

        ps_id=ps_id,
        # Raw audit copy — includes anything the schema didn't
        # explicitly break out, so future extraction won't need
        # NCRP to re-push.
        raw_payload=body.model_dump(mode="json"),
    )
    db.add(complaint)
    await db.flush()   # need complaint.id before children go in

    for mobile in body.suspect_mobiles:
        if mobile.strip():
            db.add(NcrpSuspectMobile(complaint_id=complaint.id, mobile=mobile.strip()))

    for t in body.transactions:
        db.add(NcrpTransaction(
            complaint_id=complaint.id,
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

    for a in body.efir_answers:
        code = a.question_code if a.question_code in QUESTION_CODES else "unknown"
        db.add(NcrpEfirAnswer(
            complaint_id=complaint.id,
            question_code=code,
            question_text=a.question_text,
            answer=a.answer,
        ))

    # One MaskedApplication per complaint, in RECEIVED state — only if
    # we know which PS to anchor it to. Unmatched complaints wait for
    # triage (Phase 1c screen).
    if ps_id is not None:
        db.add(MaskedApplication(
            complaint_id=complaint.id,
            ps_id=ps_id,
            status="RECEIVED",
        ))

    await db.commit()

    return NcrpComplaintPushResponse(
        ok=True,
        complaint_id=complaint.id,
        ps_id=ps_id,
        ps_matched=ps_id is not None,
        duplicate=False,
    )
