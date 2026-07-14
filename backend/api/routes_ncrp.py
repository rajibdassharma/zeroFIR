"""NCRP-side receiving routes.

**API 1** — `POST /api/v1/ncrp/complaints` — NCRP pushes a complaint
here. Authenticated via shared static `X-API-Key` header (value from
`ZFIR_NCRP_API_KEY` env var). If the env var is empty the endpoint
returns 503 so nobody accidentally runs it without setting the key.

Idempotent on `acknowledgement_no` — if NCRP retries the same
complaint we return the existing ack with `duplicate=True` rather
than creating a second row. The `police_it_v2_data` row is seeded
once, at first receive.
"""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from schemas.ncrp import NcrpComplaintPushRequest, NcrpComplaintPushResponse
from services.ncrp_persistence import create_complaint_from_payload


router = APIRouter(prefix="/api/v1/ncrp", tags=["ncrp"])


async def require_ncrp_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Guard for the NCRP-facing endpoint. Constant-time compare so
    timing analysis can't shortcut the key. Returns 503 (not 401) if
    the server hasn't been configured with a key — better to fail
    loud than to look like an active-but-broken endpoint."""
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


@router.post(
    "/complaints",
    response_model=NcrpComplaintPushResponse,
    dependencies=[Depends(require_ncrp_api_key)],
)
async def receive_complaint(
    body: NcrpComplaintPushRequest,
    db: AsyncSession = Depends(get_db),
) -> NcrpComplaintPushResponse:
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
