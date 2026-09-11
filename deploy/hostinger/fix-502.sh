#!/usr/bin/env bash
# Recupera o site do 502 sem apagar dados.
# Uso (root na VPS):
#   sudo bash /var/www/igreja-ceadrei/deploy/hostinger/fix-502.sh
set -u
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
BRANCH="${BRANCH:-cursor/portal-admin-tema-d63c}"
SERVICE_NAME="igreja-ceadrei"
SERVICE_SRC="$APP_DIR/deploy/hostinger/igreja-ceadrei.service"

echo "==== 1) Diagnóstico ===="
echo "-- serviços --"
systemctl is-active igreja 2>/dev/null || true
systemctl is-active "$SERVICE_NAME" 2>/dev/null || true
echo "-- porta 8000 --"
ss -lntp | grep 8000 || echo "NADA na 8000"

echo
echo "==== 2) safe.directory + código mais recente ===="
git config --global --add safe.directory "$APP_DIR" 2>/dev/null || true
sudo -u www-data git config --global --add safe.directory "$APP_DIR" 2>/dev/null || true
cd "$APP_DIR"
sudo -u www-data git fetch origin
sudo -u www-data git checkout "$BRANCH"
sudo -u www-data git reset --hard "origin/$BRANCH"
sudo -u www-data .venv/bin/pip install -r requirements.txt >/tmp/portal-pip.log 2>&1 || true

echo
echo "==== 3) Teste de import (mostra o erro real se houver) ===="
if ! sudo -u www-data bash -lc "cd '$APP_DIR' && .venv/bin/python -c 'from app import app; import app as m; print(\"import OK\", getattr(m, \"APP_BUILD\", \"?\"))'"; then
  echo
  echo "FALHA no import — o Gunicorn não sobe enquanto isto falhar."
  echo "Copie o erro vermelho acima e envie."
  # Mesmo assim tenta limpar porta/conflito abaixo; se o import falhar, start também falha.
fi

echo
echo "==== 4) Desliga serviço antigo (/opt) ===="
systemctl stop igreja 2>/dev/null || true
systemctl disable igreja 2>/dev/null || true
if [[ -f /etc/systemd/system/igreja.service ]]; then
  mv -f /etc/systemd/system/igreja.service /etc/systemd/system/igreja.service.bak
  echo "igreja.service movido para .bak"
fi

echo
echo "==== 5) Reinstala unit + assets embutidos ===="
if [[ -f "$SERVICE_SRC" ]]; then
  cp -f "$SERVICE_SRC" /etc/systemd/system/igreja-ceadrei.service
  systemctl daemon-reload
  systemctl enable igreja-ceadrei
  echo "Unit reinstalada de $SERVICE_SRC"
else
  echo "AVISO: não achei $SERVICE_SRC"
fi

mkdir -p static/images static/css static/images/portal
sudo -u www-data bash -lc "cd '$APP_DIR' && .venv/bin/python -c 'from portal_login_assets import ensure_portal_login_files; ensure_portal_login_files(\"static\"); print(\"assets OK\")'" \
  || echo "AVISO: ensure_portal_login_files falhou (rotas em memória ainda cobrem)"
chown -R www-data:www-data static/css/portal-login.css static/css/portal-hub.css static/images/fundo-portal-login.jpg static/images/portal 2>/dev/null || true

echo
echo "==== 6) Limpa porta e sobe Gunicorn ===="
systemctl stop igreja-ceadrei 2>/dev/null || true
systemctl reset-failed igreja-ceadrei 2>/dev/null || true
killall -9 gunicorn 2>/dev/null || true
pkill -9 -f 'gunicorn.*app:app' 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true
sleep 2
systemctl start igreja-ceadrei
sleep 3

if ! ss -lntp | grep -q ':8000'; then
  echo "Porta 8000 ainda fechada — restart..."
  fuser -k 8000/tcp 2>/dev/null || true
  sleep 1
  systemctl restart igreja-ceadrei
  sleep 3
fi

echo
echo "==== 7) Resultado ===="
systemctl --no-pager --full status igreja-ceadrei | head -35 || true
echo "-- porta --"
ss -lntp | grep 8000 || echo "NADA na 8000"
echo "-- curl local --"
if curl -fsS --max-time 5 http://127.0.0.1:8000/_versao; then
  echo
  echo "OK: app respondeu. Abra https://igrejaceasdrei.com.br/"
  echo "Portal: https://igrejaceasdrei.com.br/portal/login  (Ctrl+F5)"
  exit 0
fi

echo
echo "AINDA FALHOU. Logs:"
journalctl -u igreja-ceadrei -n 80 --no-pager || true
exit 1
