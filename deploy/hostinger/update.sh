#!/usr/bin/env bash
# Atualiza o site no VPS (rode como root no servidor).
set -euo pipefail
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
DATA_DIR="${DATA_DIR:-/var/data/igreja-ceadrei}"
BRANCH="${BRANCH:-main}"
DOMAIN="${DOMAIN:-igrejaceasdrei.com.br}"
NGINX_SITE="${NGINX_SITE:-/etc/nginx/sites-available/igreja-ceadrei}"
SERVICE_FILE="${SERVICE_FILE:-/etc/systemd/system/igreja-ceadrei.service}"

cd "$APP_DIR"
sudo -u www-data git fetch origin
sudo -u www-data git checkout "$BRANCH"
sudo -u www-data git pull origin "$BRANCH"
sudo -u www-data .venv/bin/pip install -r requirements.txt

# Reaplica o unit do Gunicorn (timeout de upload de vídeo).
install -m 644 "$APP_DIR/deploy/hostinger/igreja-ceadrei.service" "$SERVICE_FILE"
sed -i "s|/var/www/igreja-ceadrei|$APP_DIR|g" "$SERVICE_FILE"
sed -i "s|/var/data/igreja-ceadrei|$DATA_DIR|g" "$SERVICE_FILE"
systemctl daemon-reload

# Ajusta limites no Nginx já instalado, sem apagar o HTTPS do Certbot.
if [[ -f "$NGINX_SITE" ]]; then
  if grep -qE 'client_max_body_size[[:space:]]+' "$NGINX_SITE"; then
    sed -i -E 's/client_max_body_size[[:space:]]+[0-9]+[MmKkGg]?;/client_max_body_size 1200M;/' "$NGINX_SITE"
  else
    sed -i "/server_name /a\\    client_max_body_size 1200M;" "$NGINX_SITE"
  fi
  if grep -qE 'client_body_timeout[[:space:]]+' "$NGINX_SITE"; then
    sed -i -E 's/client_body_timeout[[:space:]]+[0-9]+s;/client_body_timeout 600s;/' "$NGINX_SITE"
  else
    sed -i "/client_max_body_size/a\\    client_body_timeout 600s;" "$NGINX_SITE"
  fi
  if grep -qE 'proxy_read_timeout[[:space:]]+' "$NGINX_SITE"; then
    sed -i -E 's/proxy_read_timeout[[:space:]]+[0-9]+s;/proxy_read_timeout 600s;/' "$NGINX_SITE"
  else
    sed -i "/proxy_pass /a\\        proxy_read_timeout 600s;" "$NGINX_SITE"
  fi
  if grep -qE 'proxy_send_timeout[[:space:]]+' "$NGINX_SITE"; then
    sed -i -E 's/proxy_send_timeout[[:space:]]+[0-9]+s;/proxy_send_timeout 600s;/' "$NGINX_SITE"
  else
    sed -i "/proxy_read_timeout/a\\        proxy_send_timeout 600s;" "$NGINX_SITE"
  fi
  nginx -t
  systemctl reload nginx
fi

systemctl restart igreja-ceadrei
systemctl --no-pager --full status igreja-ceadrei | head -20
echo "OK — site atualizado (uploads de vídeo até 1 GB / 10 min de envio)."
