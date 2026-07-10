"""Health + feature-flag endpoints."""
from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def health():
    return {"ok": True, "service": "zeroFIR"}


@router.get("/api/v1/features")
async def features():
    """Public — no auth. Frontend reads this on mount for future
    facade flags. Empty stub in Phase 0."""
    return {
        # Reserved for Phase 4+ (signed transfer receipts / eSign facade).
        # "esign_provider": settings.ESIGN_PROVIDER,
    }
