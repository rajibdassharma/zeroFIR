"""Outbound placeholders — where the real NCRP + Police IT V2 pushes
will live once the integration is wired.

For now both functions:
  1. Log a structured line so operations can grep for outbound events.
  2. Stamp the corresponding timestamp on the PoliceITV2Data row.
  3. Return normally (no HTTP call, no retry, no failure).

Once the receiving APIs are available these two functions get real
`httpx.AsyncClient` calls, retry-with-backoff, and structured error
handling. Callers already `await` them so upgrading in place won't
require changes anywhere else.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ncrp_data import NcrpData
from models.police_it_v2_data import PoliceITV2Data


logger = logging.getLogger(__name__)


def _now_naive() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)


async def push_ncrp_data(db: AsyncSession, ack_no: str) -> None:
    """Placeholder for the NCRP outbound push (envisioned as API 2 /
    API 5 in the KarnatakazeroFIR deck). Real implementation will POST
    the normalised NCRP payload back to NCRP so their citizen
    dashboard reflects the FIR state.

    Caller is responsible for `commit()`."""
    ncrp = (
        await db.execute(
            select(NcrpData).where(NcrpData.acknowledgement_no == ack_no)
        )
    ).scalar_one_or_none()
    if ncrp is None:
        raise ValueError(f"NCRP data row missing for ack {ack_no!r} — cannot push.")

    logger.info(
        "[OUTBOUND-NCRP placeholder] would push ack=%s complainant=%r to NCRP",
        ack_no, ncrp.complainant_name,
    )

    v2 = (
        await db.execute(
            select(PoliceITV2Data).where(PoliceITV2Data.acknowledgement_no == ack_no)
        )
    ).scalar_one_or_none()
    if v2 is not None:
        v2.efir_pushed_at = _now_naive()


async def push_police_it_v2_data(db: AsyncSession, ack_no: str) -> None:
    """Placeholder for the Police IT V2 outbound push. Real
    implementation will POST the FIR-additional bundle (Sections 1-6)
    so V2 raises the actual Zero FIR record on their side.

    Caller is responsible for `commit()`."""
    v2 = (
        await db.execute(
            select(PoliceITV2Data).where(PoliceITV2Data.acknowledgement_no == ack_no)
        )
    ).scalar_one_or_none()
    if v2 is None:
        raise ValueError(f"PoliceITV2Data row missing for ack {ack_no!r} — cannot push.")

    logger.info(
        "[OUTBOUND-V2 placeholder] would push ack=%s ps_id=%s to Police IT V2",
        ack_no, v2.ps_id,
    )

    # `registered_pushed_at` reserved for the final API 5 push (once
    # V2 confirms the FIR is registered). For the submit-time push we
    # stamp `efir_pushed_at` on the NCRP side and no dedicated column
    # here yet — will add when we split "submitted-to-V2" vs
    # "registered-in-V2" in Phase 1b.3.
