#!/usr/bin/env bash
# Atalho: termina o deploy do login do portal (safe.directory + pull + restart).
# Uso (root na VPS):
#   sudo bash /var/www/igreja-ceadrei/deploy/hostinger/aplicar-portal-login.sh
set -euo pipefail
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"

echo "==== safe.directory (corrige dubious ownership) ===="
git config --global --add safe.directory "$APP_DIR" || true
sudo -u www-data git config --global --add safe.directory "$APP_DIR" || true

echo "==== update completo ===="
bash "$APP_DIR/deploy/hostinger/update.sh"

echo
echo "==== conferência ===="
curl -fsS --max-time 8 http://127.0.0.1:8000/_versao || true
echo
curl -sI --max-time 8 http://127.0.0.1:8000/portal/assets/fundo.jpg | head -1 || true
curl -sI --max-time 8 http://127.0.0.1:8000/portal/assets/portal-login.css | head -1 || true
echo
echo "No browser (Ctrl+F5): https://igrejaceasdrei.com.br/portal/login"
echo "Build esperado em /_versao: portal-login-embed-20260911"
