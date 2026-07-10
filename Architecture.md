# Architecture — zeroFIR

## System Overview

Same shape as CyberFraud — single-page React SPA, FastAPI backend,
MySQL, deployed on the shared KSP Ubuntu box alongside CyberFraud.

```
              KSWAN (internal, KSP)
                     │
       ┌─────────────▼─────────────┐
       │   React 19 SPA            │
       │   Vite (port 5173 dev)    │
       │   Tailwind + Zustand      │
       └─────────────┬─────────────┘
                     │  /api/* proxy
       ┌─────────────▼─────────────┐
       │   Nginx (prod)            │
       │   SSL + static + proxy    │
       └─────────────┬─────────────┘
                     │
       ┌─────────────▼─────────────┐
       │   FastAPI (port 8002)     │
       │   Gunicorn + Uvicorn      │
       └──┬────────────────┬───────┘
          │                │
   ┌──────▼────┐    ┌──────▼──────────┐
   │  MySQL 8+ │    │ File storage    │
   │  zerofir  │    │ /opt/zerofir/   │
   └───────────┘    │   uploads/      │
                    └─────────────────┘
```

**Coexistence with CyberFraud on the same host:**

| Service | Port | Runtime path | DB name |
|---|---|---|---|
| cyberfraud-backend | 8000 | /opt/cyberfraud/ | cyber_fraud_dsr |
| zerofir-backend | **8002** | **/opt/zerofir/** | **zerofir** |

Nginx serves each on its own hostname / path; MySQL server hosts
both DBs. Backups + JWT rotation are scoped per-service.

---

## Authentication & Authorization

### JWT Token Flow

Identical to CyberFraud. Backend refuses to boot if
`ZFIR_JWT_SECRET` is missing, matches the placeholder default, or is
shorter than 32 chars (day-one hardening — no repeat of the
CyberFraud silent-insecure regression).

```json
{
  "sub": "user_id",
  "role": "super_admin | admin | unit_user",
  "unit_id": 12,
  "ps_id": 34
}
```

- Algorithm: HS256
- Expiry: 480 minutes (8 hours), configurable via `ZFIR_JWT_EXPIRE_MINUTES`
- Password hashing: bcrypt via passlib; `bcrypt>=4.0.1,<4.1` pinned
  in requirements.txt from day one (avoids passlib's "trapped"
  traceback we hit on CyberFraud).

### Role-Based Access

**Pending user specification.** Placeholder identical to CyberFraud
(`super_admin`, `admin`, `unit_user`). Real role model lands in
Phase 1 once the user defines it.

---

## Database Schema

**Master data** (mirrors CyberFraud):
- `units` — Karnataka districts.
- `police_stations` — 44 CEN PSes seeded from the same
  `All District CEN_PS.xlsx` source as CyberFraud.
- `users` — with `role`, `unit_id`, `ps_id`.

**Domain tables (pending specification, Phase 1+):**
- `zero_firs` — the FIR record.
- `zero_fir_transfers` — one row per transfer event / acknowledgement.
- `zero_fir_events` — append-only audit log (same pattern as
  eParole `application_events`).
- Copy-marking + report-target lookup tables.

Uniqueness, cascade behaviour, and audit-log immutability follow
the CyberFraud conventions codified in `database.md`.

---

## API Reference

**Phase 0 skeleton:**

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | Liveness probe |
| GET | `/api/v1/features` | none | Facade / feature flags |
| POST | `/api/v1/auth/login` | none | Login → JWT |
| GET | `/api/v1/auth/me` | Bearer | Current user |

**Phase 1+ (pending):**
- `/api/v1/units/public`, `/api/v1/police-stations/public` —
  login-dropdown source (CyberFraud shape).
- `/api/v1/zero-firs/*` — CRUD on the FIR record.
- `/api/v1/transfers/*` — the transfer workflow.
- `/api/v1/reports/*.pdf` — signed PDF exports.

---

## Production Deployment

- **OS:** shared with CyberFraud — Ubuntu 24.04 on KSWAN.
- **Reverse proxy:** nginx (extend existing config with a new server
  block or path).
- **ASGI server:** Gunicorn + Uvicorn workers.
- **Process manager:** systemd — `zerofir-backend.service`.
- **DB:** MySQL 8+ — new database `zerofir`.
- **Env prefix:** `ZFIR_`.
- **Ports:** 8002 (uvicorn); frontend built to `dist/` and served
  by nginx.

### systemd units

- `zerofir-backend.service` — gunicorn on 127.0.0.1:8002
- `zerofir-backup.service` + `.timer` — 02:00 IST nightly backup

### Deploy scripts (mirror CyberFraud shape)

- `deploy/update.sh` — one-liner incremental deploy, self-verifies.
- `deploy/rotate-jwt-secret.sh` — same pattern as CyberFraud's.
- `deploy/backup-db.sh` + `install-backup.sh`.
- `deploy/nginx.conf` — reference config.
