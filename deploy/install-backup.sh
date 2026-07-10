#!/usr/bin/env bash
# ============================================================================
# zeroFIR — one-time install of the nightly backup automation.
# Same shape as CyberFraud's install-backup.sh.
# ============================================================================

set -euo pipefail

SOURCE_REPO=/opt/zerofir-src   # adjust to actual source path
SOURCE_DEPLOY=$SOURCE_REPO/deploy
RUNTIME_BASE=/opt/zerofir
RUNTIME_DEPLOY=$RUNTIME_BASE/deploy
BACKUP_DIR=$RUNTIME_BASE/backups
SERVICE=zerofir-backup.service
TIMER=zerofir-backup.timer

echo "============================================================"
echo "  zeroFIR — install nightly MySQL backup automation"
echo "============================================================"

echo "=== 1. git pull on $SOURCE_REPO ==="
cd "$SOURCE_REPO"
sudo git pull
echo "    HEAD: $(git log -1 --oneline)"

for f in backup-db.sh zerofir-backup.service zerofir-backup.timer; do
    [ -f "$SOURCE_DEPLOY/$f" ] || { echo "ERROR: $SOURCE_DEPLOY/$f missing" >&2; exit 1; }
done

echo
echo "=== 2. Sync deploy/ → $RUNTIME_DEPLOY ==="
sudo cp -r "$SOURCE_DEPLOY" "$RUNTIME_BASE/"
sudo chown -R zerofir:zerofir "$RUNTIME_DEPLOY"

echo
echo "=== 3. Ensure backup directory exists ==="
sudo mkdir -p "$BACKUP_DIR"
sudo chown zerofir:zerofir "$BACKUP_DIR"
sudo chmod 750 "$BACKUP_DIR"

echo
echo "=== 4. Make backup-db.sh executable ==="
sudo chmod +x "$RUNTIME_DEPLOY/backup-db.sh"

echo
echo "=== 5. Install systemd unit files ==="
sudo cp "$RUNTIME_DEPLOY/zerofir-backup.service" /etc/systemd/system/
sudo cp "$RUNTIME_DEPLOY/zerofir-backup.timer"   /etc/systemd/system/

echo
echo "=== 6. daemon-reload + enable --now $TIMER ==="
sudo systemctl daemon-reload
sudo systemctl enable --now "$TIMER"

echo
echo "=== 7. Verify timer is scheduled ==="
systemctl list-timers "$TIMER" --no-pager

echo
echo "=== 8. Trigger one manual backup as a smoke test ==="
sudo systemctl start "$SERVICE"
sleep 3
for i in {1..30}; do
    STATE=$(systemctl show -p ActiveState --value "$SERVICE")
    SUBSTATE=$(systemctl show -p SubState --value "$SERVICE")
    case "$SUBSTATE" in dead|exited|failed) break ;; esac
    sleep 2
done
echo "    ActiveState=$STATE  SubState=$SUBSTATE"
sudo journalctl -u "$SERVICE" -n 30 --no-pager

echo
echo "=== 9. Backup files on disk ==="
sudo -u zerofir ls -lh "$BACKUP_DIR" || true

if [ "$SUBSTATE" = "failed" ]; then
    echo "✗ Manual backup FAILED"; exit 2
fi

echo
echo "============================================================"
echo "  ✓ Nightly backup installed."
echo "============================================================"
