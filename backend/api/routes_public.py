"""Public master-data routes — feed the login user dropdown + the
FIR entry form's static dropdowns.

No auth required. Exposes only non-sensitive fields (username, role;
never PII, hashed passwords, or counts).
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.police_station import PoliceStation
from models.user import User
from schemas.master_data import PoliceStationPublic, UserOptionPublic
from seed_data import (
    ACTS_MASTER,
    CASTE_OPTIONS,
    COMPLAINANT_ROLE_OPTIONS,
    CRIME_MAJOR_HEAD_OPTIONS,
    CRIME_MINOR_HEAD_OPTIONS,
    DIRECTION_OPTIONS,
    FIR_CASE_TYPE_OPTIONS,
    GRAVITY_OPTIONS,
    INCIDENT_PLACE_OPTIONS,
    INDIAN_STATES,
    MODE_OF_COMPLAINT_OPTIONS,
    OFFENCE_TYPE_OPTIONS,
    RELATION_TO_VICTIM_OPTIONS,
    RELIGION_OPTIONS,
    UID_TYPE_OPTIONS,
)


router = APIRouter(prefix="/api/v1", tags=["public"])


@router.get("/police-stations/public", response_model=List[PoliceStationPublic])
async def list_police_stations(db: AsyncSession = Depends(get_db)):
    """All 44 CEN PSes — feeds the NCRP-entry Address tab's PS
    dropdown. Ordered by name for scannability."""
    rows = (
        await db.execute(
            select(PoliceStation)
            .where(PoliceStation.is_active.is_(True))
            .order_by(PoliceStation.name)
        )
    ).scalars().all()
    return [PoliceStationPublic(id=r.id, name=r.name) for r in rows]


@router.get("/users/call-center/public", response_model=List[UserOptionPublic])
async def list_call_center_users(db: AsyncSession = Depends(get_db)):
    """Feeds the login-page User-ID dropdown. Only the 40 call-centre
    operators — no other users exist in this application."""
    rows = (
        await db.execute(
            select(User)
            .where(User.role == "call_center", User.is_active.is_(True))
            .order_by(User.username)
        )
    ).scalars().all()
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No Call-Centre operators configured — run seed.py.",
        )
    return [UserOptionPublic(username=r.username, role=r.role) for r in rows]


@router.get("/fir-master/dropdowns/public")
async def fir_master_dropdowns():
    """One-shot bundle of every static dropdown the FIR entry form
    needs. Keeps the frontend from making 8 separate calls on load."""
    return {
        "acts": [{"code": c, "name": n} for c, n in ACTS_MASTER],
        "mode_of_complaint": list(MODE_OF_COMPLAINT_OPTIONS),
        "fir_case_type": list(FIR_CASE_TYPE_OPTIONS),
        "offence_type": list(OFFENCE_TYPE_OPTIONS),
        "gravity": list(GRAVITY_OPTIONS),
        "direction": list(DIRECTION_OPTIONS),
        "uid_type": list(UID_TYPE_OPTIONS),
        "relation_to_victim": list(RELATION_TO_VICTIM_OPTIONS),
        "complainant_role": list(COMPLAINANT_ROLE_OPTIONS),
        "indian_states": list(INDIAN_STATES),
        "incident_place": list(INCIDENT_PLACE_OPTIONS),
        "crime_major_head": list(CRIME_MAJOR_HEAD_OPTIONS),
        "crime_minor_head": list(CRIME_MINOR_HEAD_OPTIONS),
        "religion": list(RELIGION_OPTIONS),
        "caste": list(CASTE_OPTIONS),
    }
