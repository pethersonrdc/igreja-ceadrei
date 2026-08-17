#!/usr/bin/env bash
# Atualiza o site no VPS (rode como root no servidor).
set -euo pipefail
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
BRANCH="${BRANCH:-main}"
cd "$APP_DIR"
sudo -u www-data git fetch origin
sudo -u www-data git checkout "$BRANCH"
sudo -u www-data git pull origin "$BRANCH"
sudo -u www-data .venv/bin/pip install -r requirements.txt
systemctl restart igreja-ceadrei
systemctl --no-pager --full status igreja-ceadrei | head -20
echo "OK — site atualizado."
