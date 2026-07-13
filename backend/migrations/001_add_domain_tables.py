"""Migration 001 — add Phase 1a domain tables.

Idempotent: re-running is safe. Every check hits INFORMATION_SCHEMA
before touching DDL. Order matters because of the FKs:

  1. districts
  2. police_stations         (FK → districts)
  3. users_add_fk_columns    (add unit_id + ps_id FKs to existing users)
  4. ncrp_complaints         (FK → police_stations)
  5. ncrp_transactions       (FK → ncrp_complaints)
  6. ncrp_suspect_mobiles    (FK → ncrp_complaints)
  7. ncrp_efir_answers       (FK → ncrp_complaints)
  8. masked_applications     (FK → ncrp_complaints, police_stations, users)

Charset+collation on every table = utf8mb4 / utf8mb4_unicode_ci
(matches the DB default). New FK columns match their target column's
type exactly — no repeat of the CyberFraud FK-collation incident.

Run standalone:
    python migrations/001_add_domain_tables.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow `python migrations/001_...py` from the backend dir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from config import settings
from database import engine


# ── Helpers (idempotency checks) ─────────────────────────────────


async def _table_exists(conn: AsyncConnection, name: str) -> bool:
    row = await conn.execute(text(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = :s AND table_name = :t"
    ), {"s": settings.DB_NAME, "t": name})
    return row.scalar_one_or_none() is not None


async def _column_exists(conn: AsyncConnection, table: str, column: str) -> bool:
    row = await conn.execute(text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = :s AND table_name = :t AND column_name = :c"
    ), {"s": settings.DB_NAME, "t": table, "c": column})
    return row.scalar_one_or_none() is not None


async def _fk_exists(conn: AsyncConnection, table: str, constraint: str) -> bool:
    row = await conn.execute(text(
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_schema = :s AND table_name = :t "
        "  AND constraint_name = :c AND constraint_type = 'FOREIGN KEY'"
    ), {"s": settings.DB_NAME, "t": table, "c": constraint})
    return row.scalar_one_or_none() is not None


# ── DDL ──────────────────────────────────────────────────────────


DDL_DISTRICTS = """
CREATE TABLE districts (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_districts_name (name),
    UNIQUE KEY uq_districts_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

DDL_POLICE_STATIONS = """
CREATE TABLE police_stations (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) NOT NULL,
    district_id INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_police_stations_code (code),
    KEY ix_police_stations_district_id (district_id),
    CONSTRAINT fk_police_stations_district_id
        FOREIGN KEY (district_id) REFERENCES districts(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

DDL_NCRP_COMPLAINTS = """
CREATE TABLE ncrp_complaints (
    id VARCHAR(36) NOT NULL,
    acknowledgement_no VARCHAR(60) NOT NULL,
    category VARCHAR(120) NULL,
    call_start_at DATETIME NULL,

    complainant_name VARCHAR(200) NOT NULL,
    complainant_gender VARCHAR(20) NULL,
    complainant_dob DATE NULL,
    complainant_mobile VARCHAR(20) NOT NULL,
    complainant_email VARCHAR(200) NULL,
    complainant_relation_type VARCHAR(30) NULL,
    complainant_relation_name VARCHAR(200) NULL,

    address_house_no VARCHAR(100) NULL,
    address_street VARCHAR(200) NULL,
    address_colony VARCHAR(200) NULL,
    address_city VARCHAR(100) NULL,
    address_tehsil VARCHAR(100) NULL,
    address_country VARCHAR(100) NULL,
    address_state VARCHAR(100) NULL,
    address_district VARCHAR(100) NULL,
    address_ps_name VARCHAR(200) NULL,
    address_pincode VARCHAR(20) NULL,

    incident_occurred_at VARCHAR(500) NULL,
    additional_information TEXT NULL,

    ps_id INT NULL,

    raw_payload JSON NOT NULL,
    received_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_ncrp_complaints_ack (acknowledgement_no),
    KEY ix_ncrp_complaints_ps_id (ps_id),
    CONSTRAINT fk_ncrp_complaints_ps_id
        FOREIGN KEY (ps_id) REFERENCES police_stations(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

DDL_NCRP_TRANSACTIONS = """
CREATE TABLE ncrp_transactions (
    id VARCHAR(36) NOT NULL,
    complaint_id VARCHAR(36) NOT NULL,
    sub_category VARCHAR(120) NULL,
    bank_wallet VARCHAR(150) NULL,
    account_id VARCHAR(50) NULL,
    transaction_id VARCHAR(100) NULL,
    transaction_date DATE NULL,
    approx_time VARCHAR(20) NULL,
    amount DECIMAL(18, 2) NULL,
    reference_no VARCHAR(120) NULL,
    other VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY ix_ncrp_transactions_complaint_id (complaint_id),
    CONSTRAINT fk_ncrp_transactions_complaint_id
        FOREIGN KEY (complaint_id) REFERENCES ncrp_complaints(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

DDL_NCRP_SUSPECT_MOBILES = """
CREATE TABLE ncrp_suspect_mobiles (
    id VARCHAR(36) NOT NULL,
    complaint_id VARCHAR(36) NOT NULL,
    mobile VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY ix_ncrp_suspect_mobiles_complaint_id (complaint_id),
    CONSTRAINT fk_ncrp_suspect_mobiles_complaint_id
        FOREIGN KEY (complaint_id) REFERENCES ncrp_complaints(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

DDL_NCRP_EFIR_ANSWERS = """
CREATE TABLE ncrp_efir_answers (
    id VARCHAR(36) NOT NULL,
    complaint_id VARCHAR(36) NOT NULL,
    question_code VARCHAR(60) NOT NULL,
    question_text VARCHAR(500) NOT NULL,
    answer BOOLEAN NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY ix_ncrp_efir_answers_complaint_id (complaint_id),
    CONSTRAINT fk_ncrp_efir_answers_complaint_id
        FOREIGN KEY (complaint_id) REFERENCES ncrp_complaints(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

DDL_MASKED_APPLICATIONS = """
CREATE TABLE masked_applications (
    id VARCHAR(36) NOT NULL,
    complaint_id VARCHAR(36) NOT NULL,
    ps_id INT NOT NULL,
    picked_up_by INT NULL,
    picked_up_at DATETIME NULL,

    status VARCHAR(40) NOT NULL DEFAULT 'RECEIVED',

    total_fraud_amount DECIMAL(18, 2) NULL,
    above_threshold BOOLEAN NULL,
    threshold_at_decision DECIMAL(18, 2) NULL,
    within_karnataka_jurisdiction BOOLEAN NULL,

    zero_fir_no VARCHAR(50) NULL,
    v2_fir_no VARCHAR(50) NULL,
    fir_summary TEXT NULL,

    efir_pushed_at DATETIME NULL,
    notice_lien_pulled_at DATETIME NULL,
    registered_pushed_at DATETIME NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_masked_applications_complaint_id (complaint_id),
    KEY ix_masked_applications_ps_id (ps_id),
    KEY ix_masked_applications_status (status),
    CONSTRAINT fk_masked_applications_complaint_id
        FOREIGN KEY (complaint_id) REFERENCES ncrp_complaints(id),
    CONSTRAINT fk_masked_applications_ps_id
        FOREIGN KEY (ps_id) REFERENCES police_stations(id),
    CONSTRAINT fk_masked_applications_picked_up_by
        FOREIGN KEY (picked_up_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


# ── Runner ───────────────────────────────────────────────────────


async def _create_if_missing(conn: AsyncConnection, table: str, ddl: str) -> None:
    if await _table_exists(conn, table):
        print(f"  ✓ {table} already exists — skipping.")
        return
    print(f"  + creating {table} ...")
    await conn.execute(text(ddl))


async def _add_user_fks(conn: AsyncConnection) -> None:
    """`users.unit_id` and `users.ps_id` were nullable INT columns in
    Phase 0 with no FK. Phase 1a adds the FK constraints once the
    lookup tables exist. We only ALTER when a constraint is missing."""
    if not await _column_exists(conn, "users", "unit_id"):
        print("  + adding users.unit_id column ...")
        await conn.execute(text("ALTER TABLE users ADD COLUMN unit_id INT NULL"))
    if not await _column_exists(conn, "users", "ps_id"):
        print("  + adding users.ps_id column ...")
        await conn.execute(text("ALTER TABLE users ADD COLUMN ps_id INT NULL"))

    if not await _fk_exists(conn, "users", "fk_users_unit_id"):
        print("  + adding FK users.unit_id → districts.id ...")
        await conn.execute(text(
            "ALTER TABLE users ADD CONSTRAINT fk_users_unit_id "
            "FOREIGN KEY (unit_id) REFERENCES districts(id)"
        ))
    if not await _fk_exists(conn, "users", "fk_users_ps_id"):
        print("  + adding FK users.ps_id → police_stations.id ...")
        await conn.execute(text(
            "ALTER TABLE users ADD CONSTRAINT fk_users_ps_id "
            "FOREIGN KEY (ps_id) REFERENCES police_stations(id)"
        ))


async def run() -> None:
    print(f"Applying migration 001 to `{settings.DB_NAME}` ...")
    async with engine.begin() as conn:
        await _create_if_missing(conn, "districts", DDL_DISTRICTS)
        await _create_if_missing(conn, "police_stations", DDL_POLICE_STATIONS)
        await _add_user_fks(conn)
        await _create_if_missing(conn, "ncrp_complaints", DDL_NCRP_COMPLAINTS)
        await _create_if_missing(conn, "ncrp_transactions", DDL_NCRP_TRANSACTIONS)
        await _create_if_missing(conn, "ncrp_suspect_mobiles", DDL_NCRP_SUSPECT_MOBILES)
        await _create_if_missing(conn, "ncrp_efir_answers", DDL_NCRP_EFIR_ANSWERS)
        await _create_if_missing(conn, "masked_applications", DDL_MASKED_APPLICATIONS)
    print("Migration 001 complete.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
