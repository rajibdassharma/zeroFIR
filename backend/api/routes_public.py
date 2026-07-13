"""Public master-data routes — feed the login dropdown chain.

No auth required. Only exposes the minimal, non-sensitive fields the
login form needs (id + name + role), never PII, hashed passwords, or
counts. Same shape the CyberFraud login page uses.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.district import District
from models.police_station import PoliceStation
from models.user import User
from schemas.master_data import DistrictPublic, PoliceStationPublic, UserOptionPublic


router = APIRouter(prefix="/api/v1", tags=["public"])


@router.get("/districts/public", response_model=List[DistrictPublic])
async def list_districts(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(District)
            .where(District.is_active.is_(True))
            .order_by(District.name)
        )
    ).scalars().all()
    return [DistrictPublic(id=r.id, name=r.name) for r in rows]


@router.get(
    "/districts/{district_id}/police-stations/public",
    response_model=List[PoliceStationPublic],
)
async def list_police_stations(
    district_id: int,
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(PoliceStation)
            .where(
                PoliceStation.district_id == district_id,
                PoliceStation.is_active.is_(True),
            )
            .order_by(PoliceStation.name)
        )
    ).scalars().all()
    return [
        PoliceStationPublic(id=r.id, name=r.name, district_id=r.district_id)
        for r in rows
    ]


@router.get(
    "/police-stations/{ps_id}/users/public",
    response_model=List[UserOptionPublic],
)
async def list_users_for_ps(ps_id: int, db: AsyncSession = Depends(get_db)):
    """Users assigned to a specific PS (feeds the User-ID dropdown on
    the login page). super_admin never appears here — they log in via
    /districts/public → 'super_admin' path handled by the frontend."""
    rows = (
        await db.execute(
            select(User)
            .where(User.ps_id == ps_id, User.is_active.is_(True))
            .order_by(User.username)
        )
    ).scalars().all()
    return [UserOptionPublic(username=r.username, role=r.role) for r in rows]


@router.get("/users/super-admins/public", response_model=List[UserOptionPublic])
async def list_super_admins(db: AsyncSession = Depends(get_db)):
    """The 'super_admin' path bypasses District→PS. Returns just the
    active super-admin usernames — no passwords, no PII."""
    rows = (
        await db.execute(
            select(User)
            .where(User.role == "super_admin", User.is_active.is_(True))
            .order_by(User.username)
        )
    ).scalars().all()
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No super admins configured — run seed.py.",
        )
    return [UserOptionPublic(username=r.username, role=r.role) for r in rows]
