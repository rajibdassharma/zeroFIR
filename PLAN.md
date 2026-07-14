# Implementation Plan — zeroFIR

## Project Status: Phase 1b.1 code complete — awaiting local verification (2026-07-13)

Phase 0 landed 2026-07-08 (commit `d0b80dc`). Phase 1 scope locked
2026-07-10 after user shared the NCRP→zeroFIR→V2 process flow and
the V2 FIR entry screens. Phase 1 splits into three sub-phases so
we ship end-to-end value quickly.

Fresh green-field. Tech stack, deploy shape, and UI/UX carried over
from CyberFraud verbatim per kickoff decision (2026-07-08). Domain
model (roles, workflow states, tables) will be locked in Phase 1
after the user provides the detailed spec.

---

## Phasing

| Phase | Scope | Status |
|---|---|---|
| 0 | Scaffolding — backend + frontend + deploy skeleton | ✓ (2026-07-08 `d0b80dc`) |
| 1a | Master data + NCRP ingestion (API 1 receiver) + Masking App shell (Complaints inbox + detail view) | ✓ pushed 2026-07-10 (8f28e08) |
| 1b.1 | Save-as-draft FIR entry — sections 1 (PS Details), 2 (Summary), 3 (Acts & Sections), 4 (Time), 5 (Place), 6 (Complainant); tabbed form mirroring CyberFraud CaseEntryPage | code complete — awaiting local verification |
| 1b.2 | Sections 7 (Accused), 8 (Victims), 9 (Property) — repeating child grids with drill-in | pending |
| 1b.3 | Sections 10 (Action Taken), 11 (Signature), 14 (Other Details) + threshold + jurisdiction auto-decisions + final submit path + API 2 push | pending |
| 1c | API 3 pull (Notice + Lien), API 5 push (registered FIR), sections 12/13/15 (dispatch/PC-HC/SHO signature), transfer-to-CRIMAC path | pending |
| 2 | Dashboards + reports (PDF) — per-PS Zero FIR counts, threshold breakdowns, transfer SLA aging | pending |
| 3 | Production hardening + VAPT | pending |

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
