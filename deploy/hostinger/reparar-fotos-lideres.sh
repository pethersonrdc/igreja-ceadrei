#!/usr/bin/env bash
# Repara fotos dos líderes (espelho real static + restart).
# Uso (root na VPS):
#   sudo bash /var/www/igreja-ceadrei/deploy/hostinger/reparar-fotos-lideres.sh
set -u
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
DATA_DIR="${DATA_DIR:-/var/data/igreja-ceadrei}"

echo "==== 1) DATA_DIR / uploads/lideres ===="
echo "DATA_DIR=$DATA_DIR"
ls -la "$DATA_DIR/uploads/lideres" 2>/dev/null | head -40 || echo "sem pasta DATA_DIR/uploads/lideres"
echo
echo "static/uploads/lideres (antes):"
ls -la "$APP_DIR/static/uploads/lideres" 2>/dev/null | head -20 || true

echo
echo "==== 2) Remove symlink quebrado e espelha arquivos ===="
cd "$APP_DIR"
sudo -u www-data bash -lc "cd '$APP_DIR' && DATA_DIR='$DATA_DIR' .venv/bin/python - <<'PY'
import os
os.environ['DATA_DIR'] = '$DATA_DIR'
import persistencia
import lideres_midia
root = persistencia.preparar()
print('preparar OK', root)
persistencia.garantir_espelho_real('lideres')
lideres_midia.init_db()
n = 0
for p in lideres_midia.listar_perfis():
    print(p['id'], 'custom=', p.get('custom'), 'foto_url=', p.get('foto_url'), 'foto=', p.get('foto'))
    if p.get('custom'):
        nome = (p.get('foto') or '').split('/')[-1]
        if nome:
            persistencia.espelhar_arquivo_upload('lideres', nome)
            n += 1
print('espelhados:', n)
PY
"

echo
echo "static/uploads/lideres (depois):"
ls -la "$APP_DIR/static/uploads/lideres" 2>/dev/null | head -30 || true

echo
echo "==== 3) Restart ===="
systemctl restart igreja-ceadrei || true
sleep 2
curl -fsS --max-time 5 http://127.0.0.1:8000/_versao || echo "app ainda não respondeu"
echo
# testa rota midia se soubermos um arquivo
ARQ=$(ls -1 "$DATA_DIR/uploads/lideres" 2>/dev/null | head -1 || true)
if [[ -n "${ARQ:-}" ]]; then
  echo "Teste /midia/uploads/lideres/$ARQ"
  curl -sI --max-time 5 "http://127.0.0.1:8000/midia/uploads/lideres/$ARQ" | head -5
fi
echo
echo "Pronto. Abra /admin/galeria#lideres e /eventos (Ctrl+F5)."
