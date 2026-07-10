# zeroFIR

Karnataka State Police — Zero FIR tracking platform.

Tracks FIRs registered under BNSS §173(1) at a police station outside
the crime's jurisdiction and subsequently transferred to the
jurisdictional PS. Same tech stack + UI/UX as CyberFraud.

See:
- **[SPEC.md](SPEC.md)** — product scope
- **[Architecture.md](Architecture.md)** — system design
- **[PLAN.md](PLAN.md)** — phased roadmap
- **[database.md](database.md)** — schema conventions
- **[CLAUDE.md](CLAUDE.md)** — Claude Code context

## Status

Phase 0 (scaffolding) complete. Role model + Zero FIR workflow spec
pending from the user before Phase 1.

## Local dev

```bash
# Backend
cd backend
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# *nix:    source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
python -c "import secrets; print(f'ZFIR_JWT_SECRET={secrets.token_hex(32)}')" >> .env
python seed.py                        # Phase 1+ will populate master data
uvicorn zero_fir:app --host 0.0.0.0 --port 8002 --reload

# Frontend
cd frontend && npm install && npm run dev   # http://localhost:5173

# Tests
cd backend && pytest
```

## Prod deploy

See [deploy/README.md](deploy/README.md).
