"""Auth routes — login + /me."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, CurrentUser
from auth.security import create_token, verify_password
from database import get_db
from models.user import User
from schemas.auth import LoginRequest, LoginResponse, MeResponse


router = APIRouter(prefix="/api/v1")


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = (
        await db.execute(select(User).where(User.username == body.username))
    ).scalar_one_or_none()

    # Do NOT leak whether the username exists — same message for every
    # kind of failure. Defence in depth against user enumeration.
    if user is None or not user.is_active or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_token(user_id=user.id, role=user.role)
    return LoginResponse(
        token=token,
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        must_change_password=bool(user.must_change_password),
    )


@router.get("/auth/me", response_model=MeResponse)
async def me(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (
        await db.execute(select(User).where(User.id == current.user_id))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return MeResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        full_name=user.full_name,
    )
