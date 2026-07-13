"""Phase 0 seed — creates the DB (if missing), all tables, and one
bootstrap super_admin so the login flow can be exercised end-to-end
before Phase 1's real master-data seed lands.

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
from models.district import District
from models.police_station import PoliceStation
from models.user import User
from seed_data import CEN_POLICE_STATIONS, DISTRICTS


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
        # ── 1. Districts ──────────────────────────────────────────
        print(f"Seeding {len(DISTRICTS)} districts ...")
        district_by_name: dict[str, District] = {}
        for name, code in DISTRICTS:
            d = District(name=name, code=code, is_active=True)
            session.add(d)
            district_by_name[name] = d
        await session.flush()   # populates d.id for each row

        # ── 2. Police Stations ─────────────────────────────────────
        print(f"Seeding {len(CEN_POLICE_STATIONS)} CEN police stations ...")
        ps_by_code: dict[str, PoliceStation] = {}
        for ps_name, ps_code, district_name in CEN_POLICE_STATIONS:
            district = district_by_name.get(district_name)
            if district is None:
                raise RuntimeError(
                    f"Seed data error: PS '{ps_name}' references unknown "
                    f"district '{district_name}'. Fix seed_data.py."
                )
            ps = PoliceStation(
                name=ps_name,
                code=ps_code,
                district_id=district.id,
                is_active=True,
            )
            session.add(ps)
            ps_by_code[ps_code] = ps
        await session.flush()

        # ── 3. Bootstrap super_admin ──────────────────────────────
        creds: list[tuple[str, str, str, str]] = []   # (username, pwd, role, ps_code)
        super_pwd = generate_strong_password()
        session.add(User(
            username="super_admin",
            hashed_password=hash_password(super_pwd),
            full_name="System Bootstrap Admin",
            role="super_admin",
            is_active=True,
            must_change_password=True,
        ))
        creds.append(("super_admin", super_pwd, "super_admin", ""))

        # ── 4. One placeholder `admin` user per CEN PS ────────────
        # Gives every PS a working login on day one. Real users get
        # provisioned by the super_admin from the UI in Phase 1b.
        print(f"Seeding {len(ps_by_code)} PS admin users ...")
        for ps_code, ps in ps_by_code.items():
            username = f"admin_{ps_code.lower().replace('-', '_')}"
            pwd = generate_strong_password()
            session.add(User(
                username=username,
                hashed_password=hash_password(pwd),
                full_name=f"{ps.name} Admin",
                role="admin",
                unit_id=ps.district_id,
                ps_id=ps.id,
                is_active=True,
                must_change_password=True,
            ))
            creds.append((username, pwd, "admin", ps_code))

        await session.commit()

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        creds_path = Path(__file__).parent / f"seed_credentials_bootstrap_{stamp}.csv"
        with creds_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["username", "password", "role", "ps_code", "must_change_on_first_login"])
            for row in creds:
                w.writerow([*row, "yes"])

        print("=" * 70)
        print(f"  Seeded {len(DISTRICTS)} districts + {len(ps_by_code)} PSes.")
        print(f"  Bootstrap credentials → {creds_path}")
        print("  DISTRIBUTE SECURELY per PS, then DELETE this file.")
        print("  Every user MUST change password on first login.")
        print("=" * 70)

    await engine.dispose()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true", help="Skip confirmation and drop-all immediately.")
    args = ap.parse_args()
    asyncio.run(seed(fresh=args.fresh))
