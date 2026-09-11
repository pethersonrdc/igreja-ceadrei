#!/usr/bin/env bash
# Recupera o site do 502 sem apagar dados.
# Rode como root: sudo bash deploy/hostinger/fix-502.sh
set -u
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
SERVICE_NAME="igreja-ceadrei"
SERVICE_SRC="$APP_DIR/deploy/hostinger/igreja-ceadrei.service"

echo "==== 1) Diagnóstico ===="
echo "-- serviços --"
systemctl is-active igreja 2>/dev/null || true
systemctl is-active "$SERVICE_NAME" 2>/dev/null || true
echo "-- porta 8000 --"
ss -lntp | grep 8000 || echo "NADA na 8000"
echo "-- teste import Flask --"
sudo -u www-data bash -lc "cd '$APP_DIR' && .venv/bin/python -c 'from app import app; print(\"import OK\", getattr(__import__(\"app\"), \"APP_BUILD\", \"?\"))'" \
  || echo "FALHA no import do app (veja o erro acima)"

echo
echo "==== 2) Desliga serviço antigo (/opt) ===="
systemctl stop igreja 2>/dev/null || true
systemctl disable igreja 2>/dev/null || true
if [[ -f /etc/systemd/system/igreja.service ]]; then
  mv -f /etc/systemd/system/igreja.service /etc/systemd/system/igreja.service.bak
  echo "igreja.service movido para .bak"
fi

echo
echo "==== 3) Reinstala unit do app novo ===="
if [[ -f "$SERVICE_SRC" ]]; then
  cp -f "$SERVICE_SRC" /etc/systemd/system/igreja-ceadrei.service
  systemctl daemon-reload
  systemctl enable igreja-ceadrei
  echo "Unit reinstalada de $SERVICE_SRC"
else
  echo "AVISO: não achei $SERVICE_SRC"
fi

echo
echo "==== 3b) Garante assets do login ===="
cd "$APP_DIR"
mkdir -p static/images static/css
git fetch origin 2>/dev/null || true
git show "HEAD:static/images/fundo-portal-login.jpg" > static/images/fundo-portal-login.jpg || true
git show "HEAD:static/css/portal-login.css" > static/css/portal-login.css || true
chown www-data:www-data static/images/fundo-portal-login.jpg static/css/portal-login.css 2>/dev/null || true
ls -lh static/images/fundo-portal-login.jpg static/css/portal-login.css || true

echo
echo "==== 4) Limpa porta e sobe Gunicorn ===="
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
echo "==== 5) Resultado ===="
systemctl --no-pager --full status igreja-ceadrei | head -35 || true
echo "-- porta --"
ss -lntp | grep 8000 || echo "NADA na 8000"
echo "-- curl local --"
if curl -fsS --max-time 5 http://127.0.0.1:8000/_versao; then
  echo
  echo "OK: app respondeu. Abra https://igrejaceasdrei.com.br/"
  exit 0
fi

echo
echo "AINDA FALHOU. Logs:"
journalctl -u igreja-ceadrei -n 60 --no-pager || true
exit 1
