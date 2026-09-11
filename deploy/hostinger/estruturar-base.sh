#!/usr/bin/env bash
# Estrutura e congela a base no Hostinger para edições não voltarem no restart.
# Uso (root na VPS):
#   sudo bash /var/www/igreja-ceadrei/deploy/hostinger/estruturar-base.sh
#   sudo bash /var/www/igreja-ceadrei/deploy/hostinger/estruturar-base.sh --limpar-ob
set -u
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
DATA_DIR="${DATA_DIR:-/var/data/igreja-ceadrei}"
LIMPAR_OB=0
for arg in "$@"; do
  case "$arg" in
    --limpar-ob|--limpar-Ob|--remover-ob) LIMPAR_OB=1 ;;
  esac
done

mkdir -p "$DATA_DIR" "$DATA_DIR/uploads" "$DATA_DIR/backups"
chown -R www-data:www-data "$DATA_DIR" || true

echo "==== 1) Mapa da base (DATA_DIR) ===="
echo "DATA_DIR=$DATA_DIR"
ls -la "$DATA_DIR" | head -40
echo
echo "Bancos SQLite:"
find "$DATA_DIR" -maxdepth 2 -name '*.db' -printf '%TY-%Tm-%Td %TH:%TM  %10s  %p\n' 2>/dev/null | sort
echo
echo "JSONs de lista/escala:"
find "$DATA_DIR" -maxdepth 1 -name '*.json' -printf '%TY-%Tm-%Td %TH:%TM  %10s  %p\n' 2>/dev/null | sort

echo
echo "==== 2) Serviço deve usar DATA_DIR ===="
if systemctl show-environment 2>/dev/null | grep -q '^DATA_DIR='; then
  systemctl show-environment | grep '^DATA_DIR='
elif [[ -f /etc/systemd/system/igreja-ceadrei.service ]]; then
  grep -E 'DATA_DIR|Environment' /etc/systemd/system/igreja-ceadrei.service || true
else
  echo "AVISO: confira Environment=DATA_DIR=$DATA_DIR no unit systemd"
fi

echo
echo "==== 3) Backup rápido dos DBs ===="
STAMP="$(date +%Y%m%d-%H%M%S)"
BK="$DATA_DIR/backups/snap-$STAMP"
mkdir -p "$BK"
cp -a "$DATA_DIR"/*.db "$BK/" 2>/dev/null || true
cp -a "$DATA_DIR"/*.json "$BK/" 2>/dev/null || true
echo "Backup em $BK"
ls -la "$BK" | head -30

echo
echo "==== 4) Obreiros (pastores.db) ===="
DB_PASTORES="$DATA_DIR/pastores.db"
if [[ ! -f "$DB_PASTORES" ]]; then
  echo "AVISO: $DB_PASTORES não existe"
else
  sudo -u www-data bash -lc "cd '$APP_DIR' && DATA_DIR='$DATA_DIR' .venv/bin/python - <<'PY'
import os, sqlite3, json
from pathlib import Path
os.environ['DATA_DIR'] = '$DATA_DIR'
db = Path('$DATA_DIR') / 'pastores.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT id, nome FROM obreiros ORDER BY nome COLLATE NOCASE').fetchall()
print(f'total_obreiros={len(rows)}')
ob = [r['nome'] for r in rows if str(r['nome']).startswith('Ob.')]
obr = [r['nome'] for r in rows if str(r['nome']).startswith('Obr.')]
print(f'prefixo_Ob={len(ob)}  prefixo_Obr={len(obr)}')
for n in ob:
    print('  Ob.:', n)
if $LIMPAR_OB:
    cur = conn.execute(\"DELETE FROM obreiros WHERE nome LIKE 'Ob.%'\")
    print(f'removidos_Ob={cur.rowcount}')
    nomes = [r['nome'] for r in conn.execute('SELECT nome FROM obreiros ORDER BY nome COLLATE NOCASE')]
    alvo = Path('$DATA_DIR') / 'obreiros_lista.json'
    alvo.write_text(json.dumps({'obreiros': nomes}, ensure_ascii=False, indent=2) + '\\n', encoding='utf-8')
    conn.commit()
    print('JSON atualizado:', alvo, 'nomes=', len(nomes))
else:
    print('Dica: rode com --limpar-ob para apagar todos os nomes Ob.* e atualizar o JSON.')
conn.close()
PY
"
fi

echo
echo "==== 5) Mesa de som (som.db) — procura ~30000 ===="
for candidato in \
  "$DATA_DIR/som.db" \
  "$APP_DIR/data/som.db" \
  "$DATA_DIR/backups"/som.db* \
  "$DATA_DIR/backups"/*/som.db \
  "$DATA_DIR/som.db.bak" \
  "$DATA_DIR/som.db.old"
do
  [[ -f "$candidato" ]] || continue
  echo "-- $candidato ($(stat -c%s "$candidato") bytes)"
  sudo -u www-data bash -lc "cd '$APP_DIR' && .venv/bin/python - <<PY
import sqlite3
c=sqlite3.connect('$candidato')
try:
  cab=c.execute('select coalesce(sum(custo_unitario*quantidade),0) from cabos').fetchone()[0]
  cai=c.execute('select coalesce(sum(custo_unitario*quantidade),0) from caixas').fetchone()[0]
  equ=c.execute('select coalesce(sum(custo_unitario*quantidade),0) from equipamentos').fetchone()[0]
  tot=cab+cai+equ
  print(f'  patrimonio={tot:.2f}')
  if 20000 <= tot <= 45000:
    print('  >>> candidato próximo de 30000 — copie para $DATA_DIR/som.db se for o correto')
except Exception as e:
  print('  erro:', e)
PY
"
done

echo
echo "==== 6) Congela links de upload + exporta listas atuais ===="
cd "$APP_DIR"
sudo -u www-data bash -lc "cd '$APP_DIR' && DATA_DIR='$DATA_DIR' .venv/bin/python - <<'PY'
import os
os.environ['DATA_DIR'] = '$DATA_DIR'
import persistencia
import pastores
import louvor
print('preparar', persistencia.preparar())
pastores.init_db()
pastores.exportar_obreiros_json()
pastores.exportar_escala_json()
louvor.init_db()
louvor.exportar_membros_json()
louvor.exportar_escala_json()
print('export OK →', os.environ['DATA_DIR'])
PY
"

echo
echo "==== 7) Reinicia app ===="
systemctl restart igreja-ceadrei || true
sleep 2
curl -fsS --max-time 5 http://127.0.0.1:8000/_versao || echo "app ainda não respondeu"
echo
echo "Pronto."
echo "- Dados oficiais ficam em: $DATA_DIR"
echo "- git reset/deploy NÃO deve apagar $DATA_DIR"
echo "- Após apagar Ob. no admin, o JSON em DATA_DIR é atualizado; com o código novo o git não recoloca."
echo "- Se ainda houver Ob. na lista: rode este script com --limpar-ob"
