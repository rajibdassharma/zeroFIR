# Implementation Plan — zeroFIR

## Project Status: Phase 0 in progress (2026-07-08)

Fresh green-field. Tech stack, deploy shape, and UI/UX carried over
from CyberFraud verbatim per kickoff decision (2026-07-08). Domain
model (roles, workflow states, tables) will be locked in Phase 1
after the user provides the detailed spec.

---

## Phasing

| Phase | Scope | Status |
|---|---|---|
| 0 | Scaffolding — backend + frontend + deploy skeleton | in progress |
| 1 | Master data + role model + login (per user spec) | pending spec |
| 2 | Zero FIR registration form + list + edit | pending spec |
| 3 | Transfer workflow + acknowledgement | pending spec |
| 4 | Copy marking + notifications | pending spec |
| 5 | Dashboard + reports (PDF) | pending spec |
| 6 | Production hardening + VAPT | pending spec |

Each phase = one focused PR. Phase 1 unblocks when the user provides:
- Final role list (or confirms CyberFraud shape).
- Workflow state machine (which state transitions, guarded by which
  role).
- Zero FIR field list — registering-PS, complainant, incident, sections.

---

## Phase 0 — Scaffolding

- ✓ Repo layout at `c:\VSCProjects\zeroFIR\`.
- ✓ Planning docs — SPEC.md, Architecture.md, PLAN.md, database.md,
  CLAUDE.md.
- ✓ Backend skeleton — FastAPI app boot, `ZFIR_` config, fail-loud
  JWT secret from day one, bcrypt pinned `<4.1`, health endpoint,
  DB init, tests.
- ✓ Placeholder User model with the three CyberFraud roles — will
  be replaced in Phase 1.
- ✓ Frontend skeleton — Vite + React 19 + Tailwind + Zustand, KSP
  branding, login page against the placeholder auth.
- ✓ Deploy scripts — `update.sh`, `rotate-jwt-secret.sh`,
  `backup-db.sh`, systemd unit files.
- ✓ MyProjectDashboard entry.

---

## Development Guidelines (inherited from CyberFraud, sharpened)

### Adding a new feature
1. Model: SQLAlchemy in `models/`, register in `models/__init__.py`.
2. Schema: Pydantic in `schemas/`.
3. Route: handler in `api/`, mount in `zero_fir.py`.
4. Types: TypeScript in `frontend/src/types/index.ts`.
5. API client: typed fetch in `frontend/src/lib/api/`.
6. Page: React component in `frontend/src/pages/`.
7. Router: route in `frontend/src/App.tsx`.
8. Sidebar: nav link when relevant.

### Adding a new role
1. Add to the role enum in `models/user.py`.
2. Add the `require_role(...)` dependency in `api/deps.py`.
3. Add role-scoped seeding in `seed.py`.
4. Add role-scoped queue endpoint / dashboard tile if applicable.

---

## Things to explicitly NOT do (lessons from CyberFraud)

- Do NOT default `ZFIR_JWT_SECRET` to a placeholder string on prod.
  Fail-loud from day one.
- Do NOT let bcrypt drift past 4.0.x. Pin `<4.1` from day one.
- Do NOT put usernames on the login form as free text. Dropdown from
  day one (District → PS → User ID cascade — same as CyberFraud).
- Do NOT write `UPDATE`/`DELETE` routes for the audit-log table
  (`zero_fir_events`) — append-only is the guarantee.
- Do NOT expose FastAPI's default `/docs` on prod.
  `ZFIR_DISABLE_DOCS=true`.
- Do NOT create `.env`, passwords CSVs, or production data
  Excel/PDF files in the repo.
- Do NOT push to GitHub without local pytest passing + boot verified.
