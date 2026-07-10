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
from models.user import User


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
        pwd = generate_strong_password()
        session.add(User(
            username="super_admin",
            hashed_password=hash_password(pwd),
            full_name="System Bootstrap Admin",
            role="super_admin",
            is_active=True,
            must_change_password=True,
        ))
        await session.commit()

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        creds_path = Path(__file__).parent / f"seed_credentials_bootstrap_{stamp}.csv"
        with creds_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["username", "password", "role", "must_change_on_first_login"])
            w.writerow(["super_admin", pwd, "super_admin", "yes"])

        print("=" * 70)
        print("  Bootstrap super_admin created.")
        print(f"  Credentials → {creds_path}")
        print("  DISTRIBUTE SECURELY, then DELETE this file.")
        print("  super_admin MUST change password on first login.")
        print("=" * 70)

    await engine.dispose()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true", help="Skip confirmation and drop-all immediately.")
    args = ap.parse_args()
    asyncio.run(seed(fresh=args.fresh))
