#!/usr/bin/env bash
# Atualização SEGURA: puxa código e sobe o site sem ficar em 502.
#
# Uso (root) — escolha UMA forma:
#   sudo bash /var/www/igreja-ceadrei/deploy/hostinger/atualizar-seguro.sh cursor/pastores-aniversario-data-d63c
#   sudo BRANCH=cursor/pastores-aniversario-data-d63c bash /var/www/igreja-ceadrei/deploy/hostinger/atualizar-seguro.sh
#
# Atenção: "BRANCH=... sudo bash ..." NÃO funciona — o sudo apaga a variável.
set -u
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
git config --global --add safe.directory "$APP_DIR" 2>/dev/null || true
cd "$APP_DIR"

# 1º argumento OU BRANCH= (depois do sudo) OU branch atual no servidor
if [[ "${1:-}" != "" ]]; then
  BRANCH="$1"
elif [[ "${BRANCH:-}" != "" ]]; then
  :
else
  BRANCH="$(sudo -u www-data git -C "$APP_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo cursor/base-dados-congelar-d63c)"
fi

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
# styles.css no VPS às vezes fica skip-worktree e o reset não atualiza.
# Grava como root: www-data não consegue sobrescrever se o arquivo for de outro dono.
sudo -u www-data git update-index --no-skip-worktree static/css/styles.css 2>/dev/null || true
sudo -u www-data git update-index --no-assume-unchanged static/css/styles.css 2>/dev/null || true
chown www-data:www-data "$APP_DIR/static/css/styles.css" 2>/dev/null || true
chmod 644 "$APP_DIR/static/css/styles.css" 2>/dev/null || true
if git -C "$APP_DIR" show HEAD:static/css/styles.css > "$APP_DIR/static/css/styles.css"; then
  chown www-data:www-data "$APP_DIR/static/css/styles.css" 2>/dev/null || true
  echo "styles.css atualizado"
else
  echo "AVISO: não atualizei styles.css"
fi
for arquivo in static/css/cadastro-desktop.css static/css/inscricao-desktop.css; do
  if git -C "$APP_DIR" cat-file -e "HEAD:$arquivo" 2>/dev/null; then
    git -C "$APP_DIR" show "HEAD:$arquivo" > "$APP_DIR/$arquivo"
    chown www-data:www-data "$APP_DIR/$arquivo" 2>/dev/null || true
    echo "$arquivo atualizado"
  fi
done
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
