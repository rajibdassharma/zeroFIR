"""Shared persistence helpers for NCRP complaint data.

Two callers use the same normalise-and-persist logic:
  1. `POST /api/v1/ncrp/complaints` (API 1, X-API-Key guarded) —
     NCRP pushes a complaint from its side.
  2. `POST /api/v1/complaints` (call-centre operator, JWT guarded) —
     a KSP call-centre operator takes a phone call and enters the
     same fields.

Both paths write to `ncrp_data` (and its children) and also seed a
matching `police_it_v2_data` row (workflow starts in status
`RECEIVED`). The two tables share `acknowledgement_no` as PK so
they're always 1:1.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ncrp_data import NcrpData
from models.ncrp_efir_answer import NcrpEfirAnswer, QUESTION_CODES
from models.ncrp_suspect_account import NcrpSuspectAccount
from models.ncrp_suspect_mobile import NcrpSuspectMobile
from models.ncrp_transaction import NcrpTransaction
from models.police_it_v2_data import PoliceITV2Data
from models.police_station import PoliceStation
from schemas.ncrp import NcrpComplaintPushRequest


async def resolve_ps_id(db: AsyncSession, ps_name: str | None) -> int | None:
    """Match the operator-selected PS name (from the dropdown) to a
    PS row. Since the frontend always picks from the seeded list,
    resolution should never fail in practice — a null return means
    the caller sent a value that isn't in police_stations."""
    if not ps_name:
        return None
    row = (
        await db.execute(
            select(PoliceStation.id).where(PoliceStation.name == ps_name.strip())
        )
    ).scalar_one_or_none()
    return int(row) if row is not None else None


async def create_complaint_from_payload(
    db: AsyncSession, body: NcrpComplaintPushRequest
) -> tuple[NcrpData, int | None, bool]:
    """Idempotent create by `acknowledgement_no`.

    Returns `(ncrp_row, ps_id, duplicate)`:
    - `ncrp_row` — the ORM instance (existing row if duplicate).
    - `ps_id` — resolved PS id (may be None if the name didn't match).
    - `duplicate` — True if the ack_no was already on file, in which
      case no new rows were inserted.

    Caller must `commit()` — this function only stages the changes
    so the caller can wrap them in whatever transaction shape it
    needs.
    """
    existing = (
        await db.execute(
            select(NcrpData).where(
                NcrpData.acknowledgement_no == body.acknowledgement_no
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing, existing.ps_id, True

    ps_id = await resolve_ps_id(db, body.address.police_station)

    ncrp = NcrpData(
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

        incident_place=body.incident_place,
        additional_information=body.additional_information,
        has_suspect_account_details=body.has_suspect_account_details,

        ps_id=ps_id,
    )
    db.add(ncrp)
    await db.flush()   # PK acknowledgement_no is set on ncrp; children can FK it

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

    # Seed the police_it_v2_data row so workflow state has a home
    # from moment zero. Section 1-6 fields are all nullable — the
    # frontend PATCHes them via /complaints/{ack_no}/v2-draft.
    db.add(PoliceITV2Data(
        acknowledgement_no=ncrp.acknowledgement_no,
        ps_id=ps_id,
        status="RECEIVED",
    ))

    return ncrp, ps_id, False
