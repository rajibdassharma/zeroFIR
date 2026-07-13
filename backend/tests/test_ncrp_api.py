"""API 1 (NCRP → zeroFIR) receive-endpoint tests.

Uses aiosqlite so the suite runs without MySQL. Same shape as the
Phase 0 tests — ASGI transport, no live server. `raw_payload` uses
SQLAlchemy's cross-dialect JSON type so it round-trips on SQLite.

Coverage:
  1. Missing X-API-Key → 401
  2. Wrong X-API-Key → 401
  3. Server config missing key → 503
  4. Happy path: complaint normalises + auto-creates Masking App
     when PS name matches.
  5. Unknown PS name → complaint stored, ps_id=NULL, no Masking App
     yet.
  6. Duplicate acknowledgement_no → 200, duplicate=True, no new row.
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
from models.district import District
from models.masked_application import MaskedApplication
from models.ncrp_complaint import NcrpComplaint
from models.ncrp_efir_answer import NcrpEfirAnswer
from models.ncrp_suspect_mobile import NcrpSuspectMobile
from models.ncrp_transaction import NcrpTransaction
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

    # Routes captured `Depends(get_db)` at import time — they hold a
    # reference to the ORIGINAL function. Overriding the module attr
    # wouldn't reach them; the dependency-injection override does.
    from zero_fir import app
    app.dependency_overrides[_original_get_db] = _override_get_db

    yield test_sessionmaker

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest.fixture
async def seed_ps(sqlite_db):
    """Seed one district + one CEN PS so the API 1 happy path has a
    real target to resolve to."""
    async with sqlite_db() as session:
        district = District(name="Bengaluru City", code="BLR-C", is_active=True)
        session.add(district)
        await session.flush()
        ps = PoliceStation(
            name="Bengaluru City East CEN PS",
            code="BLR-C-E-CEN",
            district_id=district.id,
            is_active=True,
        )
        session.add(ps)
        await session.commit()
        return ps.id


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setattr(settings, "NCRP_API_KEY", API_KEY)
    return API_KEY


def sample_payload(ack: str = "30811240050021", ps_name: str = "Bengaluru City East CEN PS") -> dict:
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
        "incident_occurred_at": "Yesterday between 6-9 PM",
        "additional_information": "Received suspicious call claiming KYC update.",
        "suspect_mobiles": ["8888888888", "7777777777"],
        "transactions": [
            {
                "sub_category": "UPI",
                "bank_wallet": "HDFC",
                "account_id": "1234567890",
                "transaction_id": "TXN001",
                "transaction_date": "2026-07-09",
                "approx_time": "09:37 PM",
                "amount": "1050000.00",
            },
            {
                "sub_category": "UPI",
                "bank_wallet": "SBI",
                "amount": "50000.00",
            },
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
async def test_happy_path_normalises_and_creates_masked_app(sqlite_db, seed_ps, api_key):
    r = await _post(sample_payload(), headers={"X-API-Key": API_KEY})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["ps_matched"] is True
    assert body["ps_id"] == seed_ps
    assert body["duplicate"] is False
    complaint_id = body["complaint_id"]

    async with sqlite_db() as s:
        # Complaint row
        c = (await s.execute(
            select(NcrpComplaint).where(NcrpComplaint.id == complaint_id)
        )).scalar_one()
        assert c.acknowledgement_no == "30811240050021"
        assert c.complainant_name == "Test Complainant"
        assert c.ps_id == seed_ps
        assert c.raw_payload["complainant"]["name"] == "Test Complainant"

        # Children
        mobiles_count = (await s.execute(
            select(func.count()).select_from(NcrpSuspectMobile)
            .where(NcrpSuspectMobile.complaint_id == complaint_id)
        )).scalar_one()
        assert mobiles_count == 2

        txn_count = (await s.execute(
            select(func.count()).select_from(NcrpTransaction)
            .where(NcrpTransaction.complaint_id == complaint_id)
        )).scalar_one()
        assert txn_count == 2

        ans_count = (await s.execute(
            select(func.count()).select_from(NcrpEfirAnswer)
            .where(NcrpEfirAnswer.complaint_id == complaint_id)
        )).scalar_one()
        assert ans_count == 1

        # Masking Application auto-created
        ma = (await s.execute(
            select(MaskedApplication)
            .where(MaskedApplication.complaint_id == complaint_id)
        )).scalar_one()
        assert ma.status == "RECEIVED"
        assert ma.ps_id == seed_ps


@pytest.mark.asyncio
async def test_unknown_ps_stores_complaint_without_masked_app(sqlite_db, seed_ps, api_key):
    payload = sample_payload(ps_name="Nowhere CEN PS")
    r = await _post(payload, headers={"X-API-Key": API_KEY})
    assert r.status_code == 200
    body = r.json()
    assert body["ps_matched"] is False
    assert body["ps_id"] is None

    async with sqlite_db() as s:
        c = (await s.execute(
            select(NcrpComplaint).where(NcrpComplaint.id == body["complaint_id"])
        )).scalar_one()
        assert c.ps_id is None

        ma_count = (await s.execute(
            select(func.count()).select_from(MaskedApplication)
            .where(MaskedApplication.complaint_id == body["complaint_id"])
        )).scalar_one()
        assert ma_count == 0


@pytest.mark.asyncio
async def test_duplicate_ack_no_returns_existing(sqlite_db, seed_ps, api_key):
    r1 = await _post(sample_payload(), headers={"X-API-Key": API_KEY})
    assert r1.status_code == 200
    complaint_id_1 = r1.json()["complaint_id"]

    r2 = await _post(sample_payload(), headers={"X-API-Key": API_KEY})
    assert r2.status_code == 200
    body = r2.json()
    assert body["duplicate"] is True
    assert body["complaint_id"] == complaint_id_1

    # Table should still hold exactly one complaint row.
    async with sqlite_db() as s:
        n = (await s.execute(
            select(func.count()).select_from(NcrpComplaint)
        )).scalar_one()
        assert n == 1
