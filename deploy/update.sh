#!/usr/bin/env bash
# ============================================================================
# zeroFIR — INCREMENTAL UPDATE deploy. Idempotent, self-verifying.
#
# What it does:
#   1. git pull on the source tree
#   2. Install/upgrade pip deps
#   3. Pre-deploy MySQL backup via backup-db.sh
#   4. Run migrations (Phase 1+; empty registry in Phase 0)
#   5. Build the frontend (npm install + npm run build)
#   6. Sync backend/ + frontend/dist/ → /opt/zerofir/
#   7. Restart zerofir-backend systemd service
#   8. Self-verify: service active, /health responding
#
# Usage on the server:
#   cd <source> && git pull && sudo bash deploy/update.sh
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNTIME=/opt/zerofir
SVC=zerofir-backend

echo "================================================================"
echo "  zeroFIR incremental update"
echo "  SOURCE : $SOURCE"
echo "  RUNTIME: $RUNTIME"
echo "================================================================"

# ── 1. Pull latest source ────────────────────────────────────────────
echo
echo "=== 1. git pull on $SOURCE ==="
cd "$SOURCE"
git pull
echo "    HEAD: $(git log -1 --oneline)"

# ── 2. Install / upgrade Python deps ─────────────────────────────────
echo
echo "=== 2. Install pip dependencies ==="
sudo -u zerofir bash -c "
    cd $RUNTIME/backend
    venv/bin/pip install --quiet --upgrade -r $SOURCE/backend/requirements.txt
"
echo "    Done."

# ── 3. Pre-deploy DB backup ──────────────────────────────────────────
echo
echo "=== 3. Pre-deploy DB backup ==="
sudo -u zerofir bash "$SOURCE/deploy/backup-db.sh"

# ── 4. Run migrations (Phase 1+) ─────────────────────────────────────
echo
echo "=== 4. Run additive DB migrations (empty in Phase 0) ==="
sudo cp -r "$SOURCE/backend/migrations" "$RUNTIME/backend/"
sudo chown -R zerofir:zerofir "$RUNTIME/backend/migrations"
# echo "    (Phase 1+ migrations get added here as they land)"
# Example once we have migrations:
# sudo -u zerofir bash -c "
#     cd $RUNTIME/backend
#     venv/bin/python -m migrations.001_add_master_data
# "

# ── 5. Build the frontend ────────────────────────────────────────────
echo
echo "=== 5. Build frontend ==="
cd "$SOURCE/frontend"
npm install --silent
npm run build

# ── 6. Sync code from source to runtime ──────────────────────────────
echo
echo "=== 6. Sync backend + frontend dist → $RUNTIME ==="
sudo cp -r "$SOURCE/backend" "$RUNTIME/"
sudo mkdir -p "$RUNTIME/frontend"
sudo cp -r "$SOURCE/frontend/dist" "$RUNTIME/frontend/"
sudo chown -R zerofir:zerofir "$RUNTIME/backend" "$RUNTIME/frontend"

# ── 7. Restart backend ───────────────────────────────────────────────
echo
echo "=== 7. Restart backend service ==="
sudo systemctl restart "$SVC"
sleep 2
sudo systemctl is-active "$SVC"

# ── 8. Self-verify ───────────────────────────────────────────────────
echo
echo "=== 8. Self-verify ==="
if curl -sk --max-time 5 https://localhost/health | grep -q '"ok"'; then
    echo "    ✓ /health responding via nginx"
elif curl -s --max-time 5 http://127.0.0.1:8002/health | grep -q '"ok"'; then
    echo "    ✓ /health responding via direct backend (nginx may serve a different host)"
else
    echo "    ✗ /health check failed"
    exit 1
fi

echo
echo "================================================================"
echo "  ✓ Incremental update complete."
echo "================================================================"
