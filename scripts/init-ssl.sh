#!/usr/bin/env bash
# First-time SSL certificate issuance via Let's Encrypt / Certbot
# Run ONCE on the server before starting the full stack with HTTPS.
#
# Usage: ./scripts/init-ssl.sh your@email.com raspisanie.vksit.ru

set -euo pipefail

EMAIL="${1:?Usage: $0 <email> <domain>}"
DOMAIN="${2:?Usage: $0 <email> <domain>}"
COMPOSE_FILE="$(dirname "$0")/../docker-compose.prod.yml"

echo "==> Starting nginx (HTTP-only) for ACME challenge..."
docker compose -f "$COMPOSE_FILE" up -d nginx

echo "==> Requesting certificate for ${DOMAIN}..."
docker compose -f "$COMPOSE_FILE" run --rm certbot \
    certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" -d "www.${DOMAIN}"

echo "==> Certificate obtained. Reloading nginx..."
docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload

echo "==> Done! HTTPS is active for ${DOMAIN}."
echo "    Add the following cron job for automatic renewal:"
echo "    0 3 * * * $(realpath "$(dirname "$0")/backup.sh") >> /var/log/vksit-backup.log 2>&1"
echo "    Certbot renews automatically via the certbot service in docker-compose."
