#!/usr/bin/env bash
# Atualiza o site no VPS (rode como root no servidor).
# Por padrão usa a branch do Cadastro/ônibus (export + famílias).
set -euo pipefail
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
# Branch com Cadastro/ônibus + Inscrições das famílias
BRANCH="${BRANCH:-cursor/onibus-export-deploy-d63c}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/sites-available/igreja}"

cd "$APP_DIR"
sudo -u www-data git fetch origin
sudo -u www-data git checkout "$BRANCH"
sudo -u www-data git reset --hard "origin/$BRANCH"
sudo -u www-data .venv/bin/pip install -r requirements.txt

# Reinício limpo (evita Gunicorn antigo na porta 8000)
systemctl stop igreja-ceadrei || true
killall -9 gunicorn 2>/dev/null || true
pkill -9 -f 'gunicorn.*app:app' 2>/dev/null || true
sleep 1
systemctl start igreja-ceadrei
sleep 2
systemctl --no-pager --full status igreja-ceadrei | head -20

# Garante sitemap/robots no Nginx ativo (arquivo "igreja")
if [[ -f "$NGINX_CONF" ]] && ! grep -q 'location = /sitemap.xml' "$NGINX_CONF"; then
  python3 - <<PY
from pathlib import Path
path = Path("$NGINX_CONF")
text = path.read_text()
snippet = """
    location = /sitemap.xml {
        alias $APP_DIR/seo/sitemap.xml;
        default_type application/xml;
        add_header Cache-Control "public, max-age=3600";
    }

    location = /robots.txt {
        alias $APP_DIR/seo/robots.txt;
        default_type text/plain;
        add_header Cache-Control "public, max-age=3600";
    }

"""
if "location = /sitemap.xml" not in text:
    text = text.replace("    location / {", snippet + "    location / {")
    path.write_text(text)
    print("Nginx: locations de sitemap/robots adicionadas.")
PY
  nginx -t && systemctl reload nginx
fi

echo "OK — site atualizado na branch $BRANCH"
echo "Confira: https://igrejaceasdrei.com.br/_versao"
echo "E depois: https://igrejaceasdrei.com.br/cadastro/onibus"
