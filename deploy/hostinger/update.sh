#!/usr/bin/env bash
# Atualiza o site no VPS (rode como root no servidor).
set -euo pipefail
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
BRANCH="${BRANCH:-main}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/sites-available/igreja-ceadrei}"

cd "$APP_DIR"
sudo -u www-data git fetch origin
sudo -u www-data git checkout "$BRANCH"
sudo -u www-data git pull origin "$BRANCH"
sudo -u www-data .venv/bin/pip install -r requirements.txt
systemctl restart igreja-ceadrei
systemctl --no-pager --full status igreja-ceadrei | head -20

# Garante sitemap/robots pelo Nginx (não depende do Gunicorn)
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
else:
    print("Nginx: sitemap/robots já configurados.")
PY
  nginx -t
  systemctl reload nginx
fi

echo "OK — site atualizado."
