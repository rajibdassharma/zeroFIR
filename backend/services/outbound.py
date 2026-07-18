"""Outbound integration placeholders — one function per arrow in
the KarnatakazeroFIR process flow.

Each function:
  1. Fetches the data we'd send (so it also exercises the DB path).
  2. Builds a payload snapshot (`payload_dict`) that mirrors what the
     real HTTP call will send when NCRP + V2 + CRIMAC endpoints exist.
  3. Logs a structured line (`[OUTBOUND-<TARGET>] …`) so ops can grep.
  4. Records an `outbound_events` row (`status='placeholder'`) so the
     "Sent Messages" tab on the detail page can render every event
     chronologically with full payload inspection.
  5. Stamps the relevant timestamp on `police_it_v2_data` when the
     event corresponds to one of the tracked milestones.

When real integrations land the swap is local — replace the
`logger.info` + `_record_event(status='placeholder')` with a real
`httpx.AsyncClient` call, capture the response, and record with
`status='success'` / `'failed'`. Callers, status transitions, and
UI don't change.

Caller always owns `db.commit()` — these helpers only stage inserts
so a whole workflow step (e.g. `submit_complaint`) can commit atomically.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ncrp_data import NcrpData
from models.ncrp_transaction import NcrpTransaction
from models.outbound_event import OutboundEvent
from models.police_it_v2_data import PoliceITV2Data
from models.police_station import PoliceStation


logger = logging.getLogger(__name__)


def _now_naive() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)


async def _record_event(
    db: AsyncSession,
    *,
    ack_no: str,
    target_system: str,
    event_type: str,
    direction: str = "outbound",
    payload: dict[str, Any] | None = None,
    response: dict[str, Any] | None = None,
    notes: str | None = None,
    status: str = "placeholder",
) -> None:
    """Stage an OutboundEvent row. Caller commits."""
    db.add(OutboundEvent(
        acknowledgement_no=ack_no,
        direction=direction,
        target_system=target_system,
        event_type=event_type,
        status=status,
        payload=payload,
        response=response,
        notes=notes,
    ))


async def _get_ps_name(db: AsyncSession, ps_id: int | None) -> str | None:
    if ps_id is None:
        return None
    return (
        await db.execute(
            select(PoliceStation.name).where(PoliceStation.id == ps_id)
        )
    ).scalar_one_or_none()


async def _fetch_pair(
    db: AsyncSession, ack_no: str,
) -> tuple[NcrpData, PoliceITV2Data]:
    """Load the (ncrp, v2) row pair — most outbound functions need both."""
    ncrp = (
        await db.execute(
            select(NcrpData).where(NcrpData.acknowledgement_no == ack_no)
        )
    ).scalar_one_or_none()
    if ncrp is None:
        raise ValueError(f"NCRP data row missing for ack {ack_no!r}.")
    v2 = (
        await db.execute(
            select(PoliceITV2Data).where(PoliceITV2Data.acknowledgement_no == ack_no)
        )
    ).scalar_one_or_none()
    if v2 is None:
        raise ValueError(f"PoliceITV2Data row missing for ack {ack_no!r}.")
    return ncrp, v2


# ═════════════════════════════════════════════════════════════════
# ── Arrow 1 — Masking App → NCRP: Push Complaint Data ──────────
# ═════════════════════════════════════════════════════════════════


async def push_complaint_to_ncrp(db: AsyncSession, ack_no: str) -> None:
    """Initial NCRP push on Submit — mirrors what the real API call
    would send back to NCRP so the citizen dashboard reflects that
    the complaint has moved into the Masking App."""
    ncrp, v2 = await _fetch_pair(db, ack_no)
    ps_name = await _get_ps_name(db, v2.ps_id)
    payload = {
        "acknowledgement_no": ack_no,
        "category": ncrp.category,
        "complainant_name": ncrp.complainant_name,
        "complainant_mobile": ncrp.complainant_mobile,
        "receiving_ps_name": ps_name,
        "received_at": ncrp.received_at.isoformat() if ncrp.received_at else None,
    }
    logger.info("[OUTBOUND-NCRP] arrow 1 push_complaint_to_ncrp ack=%s", ack_no)
    await _record_event(
        db, ack_no=ack_no, target_system="NCRP",
        event_type="push_complaint_to_ncrp",
        payload=payload,
        notes="Arrow 1 — Masking App would POST complaint to NCRP.",
    )
    v2.efir_pushed_at = _now_naive()


# ═════════════════════════════════════════════════════════════════
# ── Arrow 2 — Masking App → KA CEN PS (Police IT V2): eFIR intake
# ═════════════════════════════════════════════════════════════════


async def push_v2_intake(db: AsyncSession, ack_no: str) -> None:
    """Push the FIR-additional bundle (Sections 1-6) into Police IT V2
    so V2 can raise the actual Zero FIR record."""
    ncrp, v2 = await _fetch_pair(db, ack_no)
    payload = {
        "acknowledgement_no": ack_no,
        "ps_id": v2.ps_id,
        "ps_details_ps_name": v2.ps_details_ps_name,
        "zero_fir_no": v2.zero_fir_no,
        "fir_summary_present": bool(v2.fir_summary),
        "crime_classification_major": v2.crime_classification_major,
        "crime_classification_minor": v2.crime_classification_minor,
    }
    logger.info("[OUTBOUND-V2] arrow 2 push_v2_intake ack=%s ps_id=%s", ack_no, v2.ps_id)
    await _record_event(
        db, ack_no=ack_no, target_system="POLICE_IT_V2",
        event_type="push_v2_intake",
        payload=payload,
        notes="Arrow 2 — Masking App would POST FIR-additional bundle to V2.",
    )


# ═════════════════════════════════════════════════════════════════
# ── Arrow 3 — KA CEN PS → NCRP: Push eFIR detail ───────────────
# ═════════════════════════════════════════════════════════════════


async def push_efir_detail_to_ncrp(db: AsyncSession, ack_no: str) -> None:
    """After the Zero FIR is created on the CEN PS side, ping NCRP so
    the citizen's tracking status shows 'eFIR created'."""
    ncrp, v2 = await _fetch_pair(db, ack_no)
    payload = {
        "acknowledgement_no": ack_no,
        "zero_fir_no": v2.zero_fir_no,
        "created_by_ps_id": v2.ps_id,
        "created_by_ps_name": await _get_ps_name(db, v2.ps_id),
        "status": "ZERO_FIR_CREATED",
    }
    logger.info("[OUTBOUND-NCRP] arrow 3 push_efir_detail_to_ncrp ack=%s", ack_no)
    await _record_event(
        db, ack_no=ack_no, target_system="NCRP",
        event_type="push_efir_detail_to_ncrp",
        payload=payload,
        notes="Arrow 3 — KA CEN PS would notify NCRP that eFIR was created.",
    )


# ═════════════════════════════════════════════════════════════════
# ── Arrow 4 — V2 → NCRP: Pull Notice + Lien details ────────────
# ═════════════════════════════════════════════════════════════════


async def pull_notice_lien_from_ncrp(db: AsyncSession, ack_no: str) -> None:
    """V2 pulls any bank Notice/Lien actions already recorded against
    the reported accounts. Placeholder response is an empty list."""
    ncrp, v2 = await _fetch_pair(db, ack_no)
    payload = {"acknowledgement_no": ack_no}
    placeholder_response = {"notices": [], "liens": []}
    logger.info("[OUTBOUND-NCRP] arrow 4 pull_notice_lien_from_ncrp ack=%s", ack_no)
    await _record_event(
        db, ack_no=ack_no, target_system="NCRP",
        event_type="pull_notice_lien_from_ncrp",
        direction="outbound",   # we initiate the GET
        payload=payload,
        response=placeholder_response,
        notes=(
            "Arrow 4 — V2 would GET Notice + Lien records from NCRP. "
            "Placeholder returns empty lists."
        ),
    )
    v2.notice_lien_pulled_at = _now_naive()


# ═════════════════════════════════════════════════════════════════
# ── Arrow 5 — Transfer to CRIMAC (jurisdiction ≠ Karnataka) ────
# ═════════════════════════════════════════════════════════════════


async def push_crimac_transfer(db: AsyncSession, ack_no: str) -> None:
    """When the incident is outside Karnataka, the case gets routed
    to the CRIMAC Portal instead of a KA jurisdictional PS."""
    ncrp, v2 = await _fetch_pair(db, ack_no)
    payload = {
        "acknowledgement_no": ack_no,
        "complainant_name": ncrp.complainant_name,
        "complainant_mobile": ncrp.complainant_mobile,
        "poi_state": v2.poi_state,
        "poi_district": v2.poi_district,
        "poi_police_station": v2.poi_police_station,
        "reason": "Incident outside Karnataka jurisdiction",
    }
    logger.info("[OUTBOUND-CRIMAC] arrow 5 push_crimac_transfer ack=%s state=%s",
                ack_no, v2.poi_state)
    await _record_event(
        db, ack_no=ack_no, target_system="CRIMAC",
        event_type="push_crimac_transfer",
        payload=payload,
        notes="Arrow 5 — Case transferred to CRIMAC Portal (non-KA jurisdiction).",
    )


# ═════════════════════════════════════════════════════════════════
# ── Arrow 6 — V2 → NCRP: Registered FIR details ────────────────
# ═════════════════════════════════════════════════════════════════


async def push_registered_fir_to_ncrp(db: AsyncSession, ack_no: str) -> None:
    """Final notification to NCRP once V2 has formally registered the
    FIR (i.e., complainant signed within 3 days). Stamps
    `registered_pushed_at` on the V2 row."""
    ncrp, v2 = await _fetch_pair(db, ack_no)
    payload = {
        "acknowledgement_no": ack_no,
        "zero_fir_no": v2.zero_fir_no,
        "v2_fir_no": v2.v2_fir_no,
        "registered_at": _now_naive().isoformat(),
        "ps_id": v2.ps_id,
    }
    logger.info("[OUTBOUND-NCRP] arrow 6 push_registered_fir_to_ncrp ack=%s", ack_no)
    await _record_event(
        db, ack_no=ack_no, target_system="NCRP",
        event_type="push_registered_fir_to_ncrp",
        payload=payload,
        notes="Arrow 6 — V2 would notify NCRP that FIR is formally registered.",
    )
    v2.registered_pushed_at = _now_naive()


# ═════════════════════════════════════════════════════════════════
# ── Below-threshold routing — Transfer to e-Lost Platform ──────
# ═════════════════════════════════════════════════════════════════


async def push_e_lost_transfer(db: AsyncSession, ack_no: str) -> None:
    """When the fraud amount is under the threshold the case gets
    routed to the e-Lost Platform (out of Zero-FIR scope)."""
    ncrp, _v2 = await _fetch_pair(db, ack_no)
    total = (
        await db.execute(
            select(func.coalesce(func.sum(NcrpTransaction.amount), 0))
            .where(NcrpTransaction.acknowledgement_no == ack_no)
        )
    ).scalar_one()
    payload = {
        "acknowledgement_no": ack_no,
        "complainant_name": ncrp.complainant_name,
        "complainant_mobile": ncrp.complainant_mobile,
        "total_fraud_amount": str(Decimal(str(total))),
        "reason": "Amount below Zero-FIR threshold",
    }
    logger.info("[OUTBOUND-E-LOST] push_e_lost_transfer ack=%s total=%s",
                ack_no, total)
    await _record_event(
        db, ack_no=ack_no, target_system="E_LOST",
        event_type="push_e_lost_transfer",
        payload=payload,
        notes="Below-threshold routing — Case sent to e-Lost Platform.",
    )
