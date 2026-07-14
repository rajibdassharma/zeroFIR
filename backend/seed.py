"""Seed script — wipes + recreates the schema and provisions the
initial user roster.

State as of 2026-07-13:
- 44 CEN Police Stations (reference data only — no district scoping,
  no PS-user accounts).
- 40 Call-Centre operators (the only human users). Each gets a fresh
  16-char strong password written to a timestamped CSV. Distribute
  per operator, then delete.

Usage:
  python seed.py               # asks for confirmation before dropping
  python seed.py --fresh       # skips confirmation, drops immediately
"""
import argparse
import asyncio
import csv
import secrets
import string
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from auth.security import hash_password
from config import settings
from database import Base, engine, async_session
import models  # noqa: F401 — registers all models on Base.metadata
from models.police_station import PoliceStation
from models.user import User
from seed_data import CEN_POLICE_STATIONS


_PWD_CHARS_LOWER = string.ascii_lowercase
_PWD_CHARS_UPPER = string.ascii_uppercase
_PWD_CHARS_DIGIT = string.digits
_PWD_CHARS_SYM = "!@#$%^&*-_=+"
_PWD_ALL = _PWD_CHARS_LOWER + _PWD_CHARS_UPPER + _PWD_CHARS_DIGIT + _PWD_CHARS_SYM


def generate_strong_password(length: int = 16) -> str:
    chars = [
        secrets.choice(_PWD_CHARS_LOWER),
        secrets.choice(_PWD_CHARS_UPPER),
        secrets.choice(_PWD_CHARS_DIGIT),
        secrets.choice(_PWD_CHARS_SYM),
    ]
    chars += [secrets.choice(_PWD_ALL) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


async def create_database():
    # URL-encode the password — `@` in the password (e.g. Sandy@411)
    # otherwise gets parsed as a URL separator. CyberFraud lesson.
    pwd = quote_plus(settings.DB_PASSWORD)
    tmp_url = (
        f"mysql+asyncmy://{settings.DB_USER}:{pwd}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}"
    )
    tmp_engine = create_async_engine(tmp_url)
    async with tmp_engine.begin() as conn:
        await conn.execute(text(
            f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        ))
    await tmp_engine.dispose()


async def seed(fresh: bool):
    await create_database()

    if not fresh:
        print(f"[!] About to DROP ALL TABLES in `{settings.DB_NAME}` and reseed.")
        print("[!] This is safe for pre-prod but destroys all data.")
        confirm = input("    Type 'yes' to proceed: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            sys.exit(1)

    print(f"Dropping + recreating all tables in `{settings.DB_NAME}` ...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # ── 1. Police Stations (reference data) ───────────────────
        print(f"Seeding {len(CEN_POLICE_STATIONS)} CEN police stations ...")
        for ps_name, ps_code, _district_name in CEN_POLICE_STATIONS:
            session.add(PoliceStation(
                name=ps_name,
                code=ps_code,
                is_active=True,
            ))
        await session.flush()

        # ── 2. Call-Centre operators (only human role) ────────────
        # Centralised call-centre — 40 operators handle all Karnataka
        # complaints. No super_admin, no PS-user accounts (2026-07-13
        # scope decision).
        creds: list[tuple[str, str, str]] = []   # (username, password, role)
        CC_COUNT = 40
        print(f"Seeding {CC_COUNT} Call-Centre operators ...")
        for i in range(1, CC_COUNT + 1):
            username = f"cc_operator_{i:02d}"
            pwd = generate_strong_password()
            session.add(User(
                username=username,
                hashed_password=hash_password(pwd),
                full_name=f"Call-Centre Operator {i:02d}",
                role="call_center",
                is_active=True,
                must_change_password=True,
            ))
            creds.append((username, pwd, "call_center"))

        # ── 3. TEST USER (dev convenience) ────────────────────────
        # Fixed-credentials account for local exploration so you can
        # skip pulling a password from the CSV every reset. REMOVE
        # THIS BLOCK before deploying to production — a static
        # credential in seed code is a security incident waiting to
        # happen.
        TEST_USER = "test_user"
        TEST_PWD = "TestUser@2026"
        session.add(User(
            username=TEST_USER,
            hashed_password=hash_password(TEST_PWD),
            full_name="Test User (dev only)",
            role="call_center",
            is_active=True,
            must_change_password=False,   # skip the change-password gate for tests
        ))
        creds.append((TEST_USER, TEST_PWD, "call_center"))

        await session.commit()

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        creds_path = Path(__file__).parent / f"seed_credentials_bootstrap_{stamp}.csv"
        with creds_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["username", "password", "role", "must_change_on_first_login"])
            for row in creds:
                w.writerow([*row, "yes"])

        print("=" * 70)
        print(f"  Seeded {len(CEN_POLICE_STATIONS)} CEN PSes (reference data).")
        print(f"  Seeded {CC_COUNT} Call-Centre operators.")
        print(f"  Bootstrap credentials → {creds_path}")
        print("  DISTRIBUTE SECURELY to each operator, then DELETE this file.")
        print("  Every user MUST change password on first login.")
        print("-" * 70)
        print(f"  TEST USER (dev only): {TEST_USER} / {TEST_PWD}")
        print("  ★ Remove the TEST USER block from seed.py before going to prod.")
        print("=" * 70)

    await engine.dispose()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true", help="Skip confirmation and drop-all immediately.")
    args = ap.parse_args()
    asyncio.run(seed(fresh=args.fresh))
