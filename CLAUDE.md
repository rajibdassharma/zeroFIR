# Project: zeroFIR (Karnataka State Police)

Zero FIR tracking — FIRs registered under BNSS §173(1) at a PS
outside the crime's jurisdiction and subsequently transferred to
the jurisdictional PS. Tech stack + UI/UX ported from CyberFraud.

See @SPEC.md for product scope, @Architecture.md for system design,
@PLAN.md for the phased roadmap, @database.md for schema
conventions.

## Deployment Context

- **Shared Ubuntu 24.04** VM with CyberFraud on KSWAN.
- **Source**: `/opt/scrb/zeroFIR/` (from the SCRBChatBot repo, or
  standalone git checkout — TBD).
- **Runtime**: `/opt/zerofir/`.
- **Backups**: `/opt/zerofir/backups/`.
- **Backend**: `zerofir-backend.service` — gunicorn + uvicorn on
  127.0.0.1:8002.
- **Backups**: `zerofir-backup.timer` + `.service`, 02:00 IST daily.
- **Nginx**: SSL termination + static SPA serving + `/api/*` proxy.
  Extends the existing CyberFraud nginx config with a second server
  block / path.
- **DB**: `ZFIR_DB_NAME=zerofir`, root/password from `.env`.
- **Env prefix**: `ZFIR_`.

---

## Repo structure

```
/backend                    # FastAPI (Python, port 8002)
  zero_fir.py               # App entry — CORS, router mounting, lifespan
  config.py                 # Pydantic Settings (env prefix: ZFIR_)
                            # fail-loud on missing/default/short JWT_SECRET
  database.py               # SQLAlchemy async engine + session factory
  seed.py                   # Bootstrap super_admin + master data (Phase 1+)
  /auth
    security.py             # JWT + bcrypt (passlib, bcrypt pinned <4.1)
  /api
    deps.py                 # get_current_user, require_role dependencies
    routes_health.py        # /health, /api/v1/features
    routes_auth.py          # login, /me
  /models
    __init__.py             # Registers every model on Base.metadata
    user.py                 # User (placeholder roles from CyberFraud)
  /schemas
    __init__.py
    auth.py                 # Login req/resp, token payloads
  /utils
    friendly_errors.py      # Plain-English 422 rendering (port from CyberFraud)
  /migrations               # Hand-rolled async Python (Phase 1+)
  /tests                    # pytest + httpx.AsyncClient
  requirements.txt

/frontend                   # React 19 + Vite SPA (port 5173 dev)
  /src/pages                # LandingPage, LoginPage
  /src/lib/api              # client.ts, auth.ts
  /src/lib/stores           # auth-store.ts (Zustand)
  /src/components/auth      # LoginForm (Phase 1+ dropdown chain)
  /src/assets               # ksp_logo.png (copy from CyberFraud)
  package.json
  vite.config.ts

/deploy                     # Ubuntu deploy scripts (per project conventions)
  update.sh                 # One-liner incremental deploy, self-verifies
  rotate-jwt-secret.sh      # JWT secret rotation on prod
  backup-db.sh              # Nightly MySQL dump
  install-backup.sh         # One-time backup automation install
  zerofir-backend.service   # systemd unit
  zerofir-backup.service    # systemd unit
  zerofir-backup.timer      # systemd timer
  nginx.conf                # Reference nginx config
  README.md                 # Operator docs

.env.example                # Copy to backend/.env
```

---

## Essential commands

```bash
# ── Backend ──────────────────────────────────────────────────
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# copy .env.example → .env, set ZFIR_JWT_SECRET (openssl rand -hex 32)

# Bootstrap master data + a super_admin (Phase 1+)
python seed.py

# Run tests
pytest -q

# Start dev server
uvicorn zero_fir:app --host 0.0.0.0 --port 8002 --reload

# ── Frontend ──────────────────────────────────────────────────
cd frontend && npm install && npm run dev   # port 5173
```

**Prerequisites**: MySQL 8+, Python 3.10+, Node.js 18+.

---

## Stack

Same as CyberFraud, verbatim:

- **Backend**: FastAPI 0.115+, SQLAlchemy 2.0 async + asyncmy,
  Pydantic v2 + pydantic-settings, JWT (HS256) via python-jose,
  passlib[bcrypt] + `bcrypt>=4.0.1,<4.1` pinned, pytest + httpx.
- **Frontend**: React 19 (strict TypeScript), Vite, Tailwind CSS,
  Zustand, React Router 7, Sonner, Lucide React.
- **Infra**: MySQL 8, Nginx, Gunicorn + Uvicorn, systemd.

---

## Naming conventions

- Backend files: snake_case (`routes_auth.py`, `zero_fir.py`).
- Frontend pages: PascalCase (`LoginPage.tsx`).
- API routes: kebab-case (`/api/v1/zero-firs`).
- DB tables: snake_case plural (`zero_firs`, `zero_fir_events`).
- Env vars: `ZFIR_` prefix + SCREAMING_SNAKE.
- Roles: snake_case (`super_admin`, `admin`, `unit_user`).
- Deployment paths on Ubuntu: `/opt/zerofir/` runtime.

---

## Architecture rules

**Role-based access** (Phase 1 will finalise the role list)
- Every route declares required role via `require_role(...)`.

**Append-only audit log**
- `zero_fir_events` table (Phase 1+). Never `UPDATE` or `DELETE` —
  all "changes" become new event rows.

**Master-data scoping**
- Prison staff: own `prison_id` only. Police staff: own `ps_id`.
- Super admin: cross-PS oversight.

---

## Environment variables

- Env file: `backend/.env`
- Prefix: `ZFIR_`
- NEVER commit `.env`

| Variable | Purpose | Default |
|---|---|---|
| `ZFIR_DB_HOST` | MySQL host | `localhost` |
| `ZFIR_DB_PORT` | MySQL port | `3306` |
| `ZFIR_DB_USER` | MySQL user | `root` |
| `ZFIR_DB_PASSWORD` | MySQL password | (empty) |
| `ZFIR_DB_NAME` | MySQL database | `zerofir` |
| `ZFIR_JWT_SECRET` | JWT signing secret — backend refuses to start if missing/default/<32 chars | **REQUIRED** (`openssl rand -hex 32`) |
| `ZFIR_JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ZFIR_JWT_EXPIRE_MINUTES` | Token expiry | `480` (8h) |
| `ZFIR_CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |
| `ZFIR_DISABLE_DOCS` | Hide /docs + /openapi.json | `false` (set true on prod) |

---

## Git workflow

- Commit prefix: `zeroFIR: <description>`
- Never commit `.env`, `__pycache__/`, `node_modules/`, `frontend/dist/`
- Never commit real complainant data, filings, or attachments
- Repo name on GitHub: `zeroFIR` (matches folder name)

---

## Things Claude often gets wrong on this project

- Do NOT use raw SQL — SQLAlchemy ORM only.
- Do NOT use sync DB sessions — all DB access is async (`AsyncSession`).
- Do NOT `UPDATE`/`DELETE` on `zero_fir_events`. Append-only.
- Do NOT default `ZFIR_JWT_SECRET`. Fail-loud from day one.
- Do NOT drift bcrypt past 4.0.x — pinned `<4.1` from day one.
- Do NOT create new models without adding them to `models/__init__.py`.
- Do NOT create new routes without mounting in `zero_fir.py`.
- Do NOT push to GitHub without local pytest passing + boot verified.
- Do NOT collide with CyberFraud on the shared host — different port
  (8002), different DB (`zerofir`), different systemd unit name.
