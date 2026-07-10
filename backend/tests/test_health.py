"""Health + features endpoint smoke tests."""
import pytest
from httpx import ASGITransport, AsyncClient

from zero_fir import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "service": "zeroFIR"}


@pytest.mark.asyncio
async def test_features_returns_json():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/v1/features")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
