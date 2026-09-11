#!/usr/bin/env bash
# Diagnóstico e reparo de fotos (líderes) + verificação da mesa de som.
# Uso (root na VPS):
#   sudo bash /var/www/igreja-ceadrei/deploy/hostinger/reparar-midia-som.sh
set -u
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
DATA_DIR="${DATA_DIR:-/var/data/igreja-ceadrei}"

echo "==== 1) DATA_DIR e uploads ===="
echo "DATA_DIR=$DATA_DIR"
ls -la "$DATA_DIR" 2>/dev/null | head -20 || echo "AVISO: DATA_DIR não existe"
ls -la "$APP_DIR/static/uploads" 2>/dev/null | head -30 || true
echo "-- link lideres --"
ls -la "$APP_DIR/static/uploads/lideres" 2>/dev/null || true
ls -la "$DATA_DIR/uploads/lideres" 2>/dev/null | head -20 || true

echo
echo "==== 2) Repara links/espelho de uploads ===="
cd "$APP_DIR"
sudo -u www-data bash -lc "cd '$APP_DIR' && DATA_DIR='$DATA_DIR' .venv/bin/python - <<'PY'
import os
os.environ['DATA_DIR'] = '$DATA_DIR'
import persistencia
import lideres_midia
root = persistencia.preparar()
print('preparar OK', root)
# Re-espelha todas as fotos custom de líderes
lideres_midia.init_db()
n = 0
for p in lideres_midia.listar_perfis():
    if p.get('custom'):
        nome = (p.get('foto') or '').split('/')[-1]
        if nome:
            persistencia.espelhar_arquivo_upload('lideres', nome)
            n += 1
            print('espelhou', p['id'], nome)
print('fotos custom reparadas:', n)
PY
"

echo
echo "==== 3) Mesa de som (som.db) ===="
for candidato in \
  "$DATA_DIR/som.db" \
  "$APP_DIR/data/som.db" \
  "$DATA_DIR/backups/som.db" \
  "$DATA_DIR/som.db.bak" \
  "$DATA_DIR/som.db.old"
do
  if [[ -f "$candidato" ]]; then
    echo "-- $candidato ($(stat -c%s "$candidato") bytes, mtime $(stat -c%y "$candidato"))"
    sudo -u www-data bash -lc "cd '$APP_DIR' && .venv/bin/python - <<PY
import sqlite3
c=sqlite3.connect('$candidato')
try:
  cab=c.execute('select coalesce(sum(custo_unitario*quantidade),0) from cabos').fetchone()[0]
  cai=c.execute('select coalesce(sum(custo_unitario*quantidade),0) from caixas').fetchone()[0]
  equ=c.execute('select coalesce(sum(custo_unitario*quantidade),0) from equipamentos').fetchone()[0]
  print(f'  patrimonio={cab+cai+equ:.2f} (cabos={cab:.2f} caixas={cai:.2f} equip={equ:.2f})')
except Exception as e:
  print('  erro leitura:', e)
  print('  tabelas:', c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall())
PY
"
  fi
done

echo
echo "==== 4) Reinicia app (aplica reparo) ===="
systemctl restart igreja-ceadrei || true
sleep 2
curl -fsS --max-time 5 http://127.0.0.1:8000/_versao || echo "app ainda não respondeu"
echo
echo "Pronto. Abra /admin/galeria#lideres e /som/admin (Ctrl+F5)."
echo "Se o patrimônio continuar ~106670, o som.db atual é o padrão (seed)."
echo "Procure um backup com total próximo de 30000 na lista acima."
