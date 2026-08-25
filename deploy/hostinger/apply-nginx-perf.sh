#!/usr/bin/env bash
# Rode no VPS (como root ou com sudo). Não altera SSL/Certbot.
set -euo pipefail

SITE="${SITE_FILE:-/etc/nginx/sites-available/igreja}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/nginx.conf}"
STAMP="$(date +%Y%m%d%H%M)"

cp "$SITE" "${SITE}.bak-${STAMP}"
cp "$NGINX_CONF" "${NGINX_CONF}.bak-${STAMP}"

# Gzip completo (no Ubuntu costuma vir comentado)
sed -i \
  -e 's/# gzip_vary on;/gzip_vary on;/' \
  -e 's/# gzip_proxied any;/gzip_proxied any;/' \
  -e 's/# gzip_comp_level 6;/gzip_comp_level 6;/' \
  -e 's/# gzip_types .*/gzip_types text\/plain text\/css application\/json application\/javascript text\/xml application\/xml image\/svg+xml;/' \
  "$NGINX_CONF"

# Cache 30 dias em /static/ (só adiciona se ainda não existir expires no bloco)
if ! grep -A6 'location /static/' "$SITE" | grep -q 'expires'; then
  sed -i '/location \/static\/ {/a\        expires 30d;\n        add_header Cache-Control "public, immutable";' "$SITE"
fi

nginx -t
systemctl reload nginx
echo "OK: gzip + cache /static/ aplicados. Backups: *.bak-${STAMP}"
