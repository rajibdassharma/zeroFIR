#!/usr/bin/env bash
# ============================================================================
# zeroFIR — nightly MySQL backup.
# Runs as the `zerofir` OS user via the timer at 02:15 IST.
# Writes a gzipped mysqldump into /opt/zerofir/backups/ with 14-day retention.
# ============================================================================

set -euo pipefail
set -o pipefail

ENV_FILE=/opt/zerofir/backend/.env
BACKUP_DIR=/opt/zerofir/backups
RETENTION_DAYS=14

if [ ! -r "$ENV_FILE" ]; then
    echo "ERROR: cannot read $ENV_FILE" >&2
    exit 1
fi

DB_HOST=$(grep -E '^ZFIR_DB_HOST='     "$ENV_FILE" | tail -1 | cut -d'=' -f2- || true)
DB_PORT=$(grep -E '^ZFIR_DB_PORT='     "$ENV_FILE" | tail -1 | cut -d'=' -f2- || true)
DB_USER=$(grep -E '^ZFIR_DB_USER='     "$ENV_FILE" | tail -1 | cut -d'=' -f2- || true)
DB_PASS=$(grep -E '^ZFIR_DB_PASSWORD=' "$ENV_FILE" | tail -1 | cut -d'=' -f2- || true)
DB_NAME=$(grep -E '^ZFIR_DB_NAME='     "$ENV_FILE" | tail -1 | cut -d'=' -f2- || true)

: "${DB_HOST:=localhost}"
: "${DB_PORT:=3306}"
: "${DB_USER:=root}"
: "${DB_NAME:=zerofir}"

if [ -z "$DB_PASS" ]; then
    echo "ERROR: ZFIR_DB_PASSWORD not found in $ENV_FILE" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"
chmod 750 "$BACKUP_DIR"

TIMESTAMP=$(date +'%Y-%m-%d_%H%M')
OUTFILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "[backup-db] $(date -Iseconds) — dumping $DB_NAME → $OUTFILE"

MYSQL_PWD="$DB_PASS" mysqldump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --user="$DB_USER" \
    --single-transaction \
    --routines \
    --triggers \
    --quick \
    --hex-blob \
    "$DB_NAME" \
  | gzip --best > "$OUTFILE"

chmod 640 "$OUTFILE"

SIZE=$(stat -c '%s' "$OUTFILE")
if [ "$SIZE" -lt 1024 ]; then
    echo "ERROR: backup file $OUTFILE is suspiciously small ($SIZE bytes)" >&2
    exit 2
fi
echo "[backup-db] OK — wrote $OUTFILE ($SIZE bytes)"

PRUNED=$(find "$BACKUP_DIR" -maxdepth 1 -type f -name "${DB_NAME}_*.sql.gz" -mtime +${RETENTION_DAYS} -print -delete | wc -l)
echo "[backup-db] pruned $PRUNED file(s) older than ${RETENTION_DAYS} days"

echo "[backup-db] current backups:"
ls -lh "$BACKUP_DIR" | tail -n +2 | sort -k9
