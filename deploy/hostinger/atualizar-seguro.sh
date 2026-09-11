#!/usr/bin/env bash
# Atualização SEGURA: puxa código e sobe o site sem ficar em 502.
# Uso (root): sudo bash /var/www/igreja-ceadrei/deploy/hostinger/atualizar-seguro.sh
set -u
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
# Se BRANCH não for passado, mantém a branch atual (não força portal-admin-tema).
# Ex.: BRANCH=cursor/base-dados-congelar-d63c sudo bash deploy/hostinger/atualizar-seguro.sh
git config --global --add safe.directory "$APP_DIR" 2>/dev/null || true
cd "$APP_DIR"
BRANCH="${BRANCH:-$(sudo -u www-data git -C "$APP_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo cursor/base-dados-congelar-d63c)}"

echo "==== 1) Código novo (branch=$BRANCH) ===="
sudo -u www-data git fetch origin
sudo -u www-data git checkout "$BRANCH"
sudo -u www-data git reset --hard "origin/$BRANCH"

echo "==== 2) Import ===="
if ! sudo -u www-data bash -lc "cd '$APP_DIR' && .venv/bin/python -c 'from app import app; import app as m; print(\"import OK\", getattr(m,\"APP_BUILD\",\"?\"))'"; then
  echo "IMPORT FALHOU — não vou reiniciar. Site antigo (se ainda up) permanece."
  exit 1
fi

echo "==== 3) Assets ===="
sudo -u www-data bash -lc "cd '$APP_DIR' && .venv/bin/python -c 'from portal_login_assets import ensure_portal_login_files; ensure_portal_login_files(\"static\"); print(\"assets OK\")'" || true

echo "==== 4) Restart seguro ===="
systemctl stop igreja 2>/dev/null || true
systemctl stop igreja-ceadrei 2>/dev/null || true
killall -9 gunicorn 2>/dev/null || true
pkill -9 -f 'gunicorn.*app:app' 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true
sleep 2
systemctl start igreja-ceadrei || systemctl restart igreja-ceadrei || true
sleep 3

if ! curl -fsS --max-time 5 http://127.0.0.1:8000/_versao; then
  echo
  echo "Ainda sem resposta — segunda tentativa..."
  systemctl restart igreja-ceadrei || true
  sleep 3
fi

echo
if curl -fsS --max-time 5 http://127.0.0.1:8000/_versao; then
  echo
  echo "OK. Abra https://igrejaceasdrei.com.br/portal/login (Ctrl+F5)"
  exit 0
fi

echo "FALHOU. Logs:"
journalctl -u igreja-ceadrei -n 50 --no-pager || true
exit 1
