#!/usr/bin/env bash
# Automatic PostgreSQL backup script
# Recommended cron: 0 3 * * * /opt/raspisanie/Raspisanie/scripts/backup.sh >> /var/log/vksit-backup.log 2>&1

set -euo pipefail

BACKUP_DIR="/opt/raspisanie/backups"
RETAIN_DAYS=14
COMPOSE_FILE="/opt/raspisanie/Raspisanie/docker-compose.prod.yml"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/vksit_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup → ${BACKUP_FILE}"

docker compose -f "$COMPOSE_FILE" exec -T database \
    pg_dump -U schedule_user schedule_saas \
    | gzip > "$BACKUP_FILE"

echo "[$(date)] Backup complete: $(du -sh "$BACKUP_FILE" | cut -f1)"

# Remove backups older than RETAIN_DAYS
find "$BACKUP_DIR" -name "vksit_*.sql.gz" -mtime +"$RETAIN_DAYS" -delete
echo "[$(date)] Old backups removed (kept last ${RETAIN_DAYS} days)"
