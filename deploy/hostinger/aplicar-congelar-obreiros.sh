#!/usr/bin/env bash
# Aplica o fix que PARA os "Ob." de voltarem + limpa a lista agora.
# Uso (root na VPS):
#   sudo bash /var/www/igreja-ceadrei/deploy/hostinger/aplicar-congelar-obreiros.sh
set -u
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
DATA_DIR="${DATA_DIR:-/var/data/igreja-ceadrei}"
BRANCH="${BRANCH:-cursor/base-dados-congelar-d63c}"
EXPECTED_BUILD="base-dados-limpar-ob-20260911"

echo "==== Deploy branch $BRANCH ===="
export BRANCH
bash "$APP_DIR/deploy/hostinger/atualizar-seguro.sh" || {
  # Se o script ainda não existe nesta cópia, faz o mínimo na mão
  cd "$APP_DIR"
  sudo -u www-data git fetch origin
  sudo -u www-data git checkout "$BRANCH"
  sudo -u www-data git reset --hard "origin/$BRANCH"
  systemctl restart igreja-ceadrei || true
  sleep 3
}

echo
echo "==== Limpa Ob.* no banco agora ===="
if [[ -f "$APP_DIR/deploy/hostinger/estruturar-base.sh" ]]; then
  bash "$APP_DIR/deploy/hostinger/estruturar-base.sh" --limpar-ob || true
else
  sudo -u www-data bash -lc "cd '$APP_DIR' && DATA_DIR='$DATA_DIR' .venv/bin/python - <<'PY'
import os, sqlite3, json
from pathlib import Path
os.environ['DATA_DIR'] = '$DATA_DIR'
db = Path('$DATA_DIR') / 'pastores.db'
if not db.is_file():
    print('sem pastores.db em', db)
    raise SystemExit(0)
conn = sqlite3.connect(db)
n = conn.execute(\"DELETE FROM obreiros WHERE nome LIKE 'Ob.%'\").rowcount
nomes = [r[0] for r in conn.execute('SELECT nome FROM obreiros ORDER BY nome COLLATE NOCASE')]
(Path('$DATA_DIR')/'obreiros_lista.json').write_text(
    json.dumps({'obreiros': nomes}, ensure_ascii=False, indent=2)+'\\n', encoding='utf-8')
conn.commit()
print('removidos_Ob=', n, 'restantes=', len(nomes))
conn.close()
PY
"
  systemctl restart igreja-ceadrei || true
  sleep 2
fi

echo
echo "==== Conferência ===="
VER=$(curl -fsS --max-time 5 http://127.0.0.1:8000/_versao || true)
echo "$VER"
echo
if echo "$VER" | grep -q "$EXPECTED_BUILD"; then
  echo "OK: build $EXPECTED_BUILD no ar."
  echo "Abra a escala de obreiros com Ctrl+F5."
  exit 0
fi
echo "AINDA NÃO é $EXPECTED_BUILD. Rode de novo ou confira a branch:"
echo "  cd $APP_DIR && sudo -u www-data git branch --show-current && sudo -u www-data git log -1 --oneline"
exit 1
