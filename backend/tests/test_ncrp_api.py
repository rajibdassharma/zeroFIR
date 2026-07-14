"""API 1 (NCRP → zeroFIR) receive-endpoint tests.

Uses aiosqlite so the suite runs without MySQL. Same shape as the
Phase 0 tests — ASGI transport, no live server.

Coverage:
  1. Missing X-API-Key                                   → 401
  2. Wrong X-API-Key                                     → 401
  3. Server config missing key                           → 503
  4. Happy path: NCRP data normalises + PoliceITV2Data
     row auto-seeded when PS name matches               → 200
  5. Unknown PS name → complaint stored, ps_id=NULL,
     no PoliceITV2Data row yet                          → 200
  6. Duplicate acknowledgement_no                        → 200, duplicate=True
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import database
from config import settings
from database import Base, get_db as _original_get_db
import models  # noqa: F401 — registers all models on Base.metadata
from models.ncrp_data import NcrpData
from models.ncrp_efir_answer import NcrpEfirAnswer
from models.ncrp_suspect_mobile import NcrpSuspectMobile
from models.ncrp_transaction import NcrpTransaction
from models.police_it_v2_data import PoliceITV2Data
from models.police_station import PoliceStation


API_KEY = "test-ncrp-api-key-1234567890"


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
async def sqlite_db(monkeypatch):
    """Swap the real MySQL engine for an aiosqlite in-memory one for
    this test. Uses a fresh engine per test to keep state isolated."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    test_sessionmaker = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "async_session", test_sessionmaker)

    async def _override_get_db():
        async with test_sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()

    from zero_fir import app
    app.dependency_overrides[_original_get_db] = _override_get_db

    yield test_sessionmaker

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest.fixture
async def seed_ps(sqlite_db):
    async with sqlite_db() as session:
        ps = PoliceStation(
            name="Bengaluru City East CEN PS",
            code="BLR-C-E-CEN",
            is_active=True,
        )
        session.add(ps)
        await session.commit()
        return ps.id


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setattr(settings, "NCRP_API_KEY", API_KEY)
    return API_KEY


def sample_payload(
    ack: str = "30811240050021",
    ps_name: str = "Bengaluru City East CEN PS",
) -> dict:
    return {
        "acknowledgement_no": ack,
        "category": "Online Financial Fraud",
        "call_start_at": "2026-07-10T09:37:00",
        "complainant": {
            "name": "Test Complainant",
            "gender": "M",
            "dob": "1990-01-01",
            "mobile": "9999999999",
            "email": "test@example.com",
        },
        "address": {
            "house_no": "12A",
            "street": "MG Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "district": "Bengaluru City",
            "police_station": ps_name,
            "pincode": "560001",
        },
        "incident_place": "Own residence / Home",
        "additional_information": "Received suspicious call claiming KYC update.",
        "has_suspect_account_details": False,
        "suspect_mobiles": ["8888888888", "7777777777"],
        "transactions": [
            {
                "sub_category": "UPI", "bank_wallet": "HDFC",
                "account_id": "1234567890", "transaction_id": "TXN001",
                "transaction_date": "2026-07-09", "approx_time": "09:37 PM",
                "amount": "1050000.00",
            },
            {"sub_category": "UPI", "bank_wallet": "SBI", "amount": "50000.00"},
        ],
        "efir_answers": [
            {
                "question_code": "amount_10_lakh_or_above",
                "question_text": "Total fraud amount is ₹10 lakh or above?",
                "answer": True,
            },
        ],
    }


async def _post(payload, headers):
    from zero_fir import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.post("/api/v1/ncrp/complaints", json=payload, headers=headers)


# ── Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_api_key_rejected(sqlite_db, api_key):
    r = await _post(sample_payload(), headers={})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_wrong_api_key_rejected(sqlite_db, api_key):
    r = await _post(sample_payload(), headers={"X-API-Key": "nope"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_endpoint_disabled_when_key_unset(sqlite_db, monkeypatch):
    monkeypatch.setattr(settings, "NCRP_API_KEY", "")
    r = await _post(sample_payload(), headers={"X-API-Key": "anything"})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_happy_path_seeds_ncrp_and_v2(sqlite_db, seed_ps, api_key):
    r = await _post(sample_payload(), headers={"X-API-Key": API_KEY})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["ps_matched"] is True
    assert body["ps_id"] == seed_ps
    assert body["duplicate"] is False
    ack_no = body["acknowledgement_no"]
    assert ack_no == "30811240050021"

    async with sqlite_db() as s:
        n = (await s.execute(
            select(NcrpData).where(NcrpData.acknowledgement_no == ack_no)
        )).scalar_one()
        assert n.complainant_name == "Test Complainant"
        assert n.ps_id == seed_ps

        # Children keyed on ack_no.
        assert (await s.execute(
            select(func.count()).select_from(NcrpSuspectMobile)
            .where(NcrpSuspectMobile.acknowledgement_no == ack_no)
        )).scalar_one() == 2

        assert (await s.execute(
            select(func.count()).select_from(NcrpTransaction)
            .where(NcrpTransaction.acknowledgement_no == ack_no)
        )).scalar_one() == 2

        assert (await s.execute(
            select(func.count()).select_from(NcrpEfirAnswer)
            .where(NcrpEfirAnswer.acknowledgement_no == ack_no)
        )).scalar_one() == 1

        # PoliceITV2Data row auto-seeded.
        v2 = (await s.execute(
            select(PoliceITV2Data).where(PoliceITV2Data.acknowledgement_no == ack_no)
        )).scalar_one()
        assert v2.status == "RECEIVED"
        assert v2.ps_id == seed_ps


@pytest.mark.asyncio
async def test_unknown_ps_still_seeds_v2_with_null_ps(sqlite_db, seed_ps, api_key):
    """Even when the PS name doesn't resolve, we still seed a V2 row
    (with ps_id = NULL) so the workflow has a home and the operator
    can fix the PS on the /complaints/{ack_no}/v2-draft edit."""
    payload = sample_payload(ps_name="Nowhere CEN PS")
    r = await _post(payload, headers={"X-API-Key": API_KEY})
    assert r.status_code == 200
    body = r.json()
    assert body["ps_matched"] is False
    assert body["ps_id"] is None

    ack_no = body["acknowledgement_no"]
    async with sqlite_db() as s:
        n = (await s.execute(
            select(NcrpData).where(NcrpData.acknowledgement_no == ack_no)
        )).scalar_one()
        assert n.ps_id is None

        v2 = (await s.execute(
            select(PoliceITV2Data).where(PoliceITV2Data.acknowledgement_no == ack_no)
        )).scalar_one()
        assert v2.ps_id is None
        assert v2.status == "RECEIVED"


@pytest.mark.asyncio
async def test_duplicate_ack_no_returns_existing(sqlite_db, seed_ps, api_key):
    r1 = await _post(sample_payload(), headers={"X-API-Key": API_KEY})
    assert r1.status_code == 200
    ack_no_1 = r1.json()["acknowledgement_no"]

    r2 = await _post(sample_payload(), headers={"X-API-Key": API_KEY})
    assert r2.status_code == 200
    body = r2.json()
    assert body["duplicate"] is True
    assert body["acknowledgement_no"] == ack_no_1

    async with sqlite_db() as s:
        n = (await s.execute(select(func.count()).select_from(NcrpData))).scalar_one()
        assert n == 1
