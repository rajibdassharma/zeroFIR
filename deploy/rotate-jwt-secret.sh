#!/usr/bin/env bash
# ============================================================================
# zeroFIR — rotate JWT signing secret (ZFIR_JWT_SECRET).
# Same shape as CyberFraud's rotate-jwt-secret.sh — backs up .env,
# replaces the line, restarts the backend, self-verifies.
# ============================================================================

set -euo pipefail

ENV_FILE=/opt/zerofir/backend/.env
SVC=zerofir-backend
ENV_OWNER=zerofir
ENV_GROUP=zerofir

echo "================================================================"
echo "  zeroFIR — rotate JWT signing secret"
echo "  .env : $ENV_FILE"
echo "  svc  : $SVC"
echo "================================================================"

[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found" >&2; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "ERROR: openssl not installed" >&2; exit 1; }
[ "$EUID" -eq 0 ] || { echo "ERROR: must run as root (use sudo)" >&2; exit 1; }

TS=$(date +'%Y%m%d_%H%M%S')
BAK="${ENV_FILE}.bak.${TS}"
cp -p "$ENV_FILE" "$BAK"
echo "=== 1. Backed up .env → $BAK"

NEW_SECRET=$(openssl rand -hex 32)
echo "=== 2. Generated 64-char hex secret"

if grep -q '^ZFIR_JWT_SECRET=' "$ENV_FILE"; then
    sed -i "s|^ZFIR_JWT_SECRET=.*|ZFIR_JWT_SECRET=${NEW_SECRET}|" "$ENV_FILE"
    echo "=== 3. Replaced existing ZFIR_JWT_SECRET line"
else
    echo "ZFIR_JWT_SECRET=${NEW_SECRET}" >> "$ENV_FILE"
    echo "=== 3. Appended ZFIR_JWT_SECRET to .env"
fi

chown "${ENV_OWNER}:${ENV_GROUP}" "$ENV_FILE"
chmod 600 "$ENV_FILE"

echo
echo "=== 4. Restart $SVC"
systemctl restart "$SVC"
sleep 2

echo
echo "=== 5. Self-verify"
if systemctl is-active "$SVC" >/dev/null; then
    echo "    ✓ $SVC is active"
else
    echo "    ✗ $SVC failed to start. Recent journal:"
    journalctl -u "$SVC" -n 30 --no-pager
    echo "ROLLBACK:  sudo cp $BAK $ENV_FILE && sudo systemctl restart $SVC"
    exit 2
fi

if curl -sk --max-time 5 https://localhost/health | grep -q '"ok"'; then
    echo "    ✓ /health responding via nginx"
elif curl -s --max-time 5 http://127.0.0.1:8002/health | grep -q '"ok"'; then
    echo "    ✓ /health responding via direct backend"
else
    echo "    ✗ /health check failed"
    journalctl -u "$SVC" -n 30 --no-pager
    echo "ROLLBACK:  sudo cp $BAK $ENV_FILE && sudo systemctl restart $SVC"
    exit 3
fi

echo
echo "================================================================"
echo "  ✓ JWT secret rotated."
echo
echo "  CAPTURE THIS NOW:"
echo "    ZFIR_JWT_SECRET=${NEW_SECRET}"
echo
echo "  All existing user sessions are now INVALID."
echo "  Old .env backup: $BAK"
echo "================================================================"
