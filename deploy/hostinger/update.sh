#!/usr/bin/env bash
# Atualiza o site no VPS (rode como root no servidor).
# Por padrão usa a branch com headers de segurança + Open Graph.
set -euo pipefail
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
BRANCH="${BRANCH:-cursor/security-headers-og-d63c}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/sites-available/igreja}"

cd "$APP_DIR"
sudo -u www-data git fetch origin
sudo -u www-data git checkout "$BRANCH"
sudo -u www-data git reset --hard "origin/$BRANCH"
sudo -u www-data .venv/bin/pip install -r requirements.txt

# Reinício limpo (evita "Address already in use" na porta 8000)
systemctl stop igreja-ceadrei || true
killall -9 gunicorn 2>/dev/null || true
pkill -9 -f 'gunicorn.*app:app' 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true
# Mata qualquer processo que ainda esteja na 8000
if command -v ss >/dev/null 2>&1; then
  ss -lntp 2>/dev/null | awk '/:8000/ {print}' | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u | while read -r pid; do
    kill -9 "$pid" 2>/dev/null || true
  done
fi
sleep 2
systemctl start igreja-ceadrei
sleep 2
# Se ainda falhar por porta ocupada, tenta mais uma vez
if ! ss -lntp 2>/dev/null | grep -q ':8000'; then
  fuser -k 8000/tcp 2>/dev/null || true
  sleep 1
  systemctl restart igreja-ceadrei
  sleep 2
fi
systemctl --no-pager --full status igreja-ceadrei | head -25
ss -lntp | grep 8000 || true

# Garante sitemap/robots/favicon + headers de segurança no Nginx ativo
if [[ -f "$NGINX_CONF" ]]; then
  NGINX_CONF="$NGINX_CONF" APP_DIR="$APP_DIR" python3 - <<'PY'
from pathlib import Path
import os
import re

path = Path(os.environ["NGINX_CONF"])
app_dir = os.environ["APP_DIR"]
text = path.read_text()
changed = False

seo_snippet = f"""
    location = /sitemap.xml {{
        alias {app_dir}/seo/sitemap.xml;
        default_type application/xml;
        add_header Cache-Control "public, max-age=3600" always;
        add_header X-Content-Type-Options "nosniff" always;
    }}

    location = /robots.txt {{
        alias {app_dir}/seo/robots.txt;
        default_type text/plain;
        add_header Cache-Control "public, max-age=3600" always;
        add_header X-Content-Type-Options "nosniff" always;
    }}

    location = /favicon.ico {{
        alias {app_dir}/static/images/emblema.png;
        default_type image/png;
        expires 30d;
        add_header Cache-Control "public" always;
    }}

"""

if "location = /sitemap.xml" not in text:
    text = text.replace("    location / {", seo_snippet + "    location / {", 1)
    changed = True
elif "location = /favicon.ico" not in text:
    favicon = f"""    location = /favicon.ico {{
        alias {app_dir}/static/images/emblema.png;
        default_type image/png;
        expires 30d;
        add_header Cache-Control "public" always;
    }}

"""
    text = text.replace("    location = /robots.txt {", favicon + "    location = /robots.txt {", 1)
    changed = True

security_lines = [
    'add_header X-Content-Type-Options "nosniff" always;',
    'add_header X-Frame-Options "SAMEORIGIN" always;',
    'add_header Referrer-Policy "strict-origin-when-cross-origin" always;',
    'add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=(), usb=()" always;',
    (
        'add_header Content-Security-Policy "default-src \'self\'; base-uri \'self\'; '
        "object-src 'none'; frame-ancestors 'self'; form-action 'self'; "
        "img-src 'self' data: blob: https://images.unsplash.com; media-src 'self' blob:; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "connect-src 'self' https://cdn.jsdelivr.net; "
        "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com\" always;"
    ),
]

if "Content-Security-Policy" not in text:
    insert = "\n".join(f"    {line}" for line in security_lines) + "\n"
    needle = "client_max_body_size"
    if needle in text:
        parts = text.split(needle)
        out = [parts[0]]
        for chunk in parts[1:]:
            nl = chunk.find("\n")
            if nl == -1:
                out.append(needle + chunk)
            else:
                out.append(needle + chunk[: nl + 1] + insert + chunk[nl + 1 :])
        text = "".join(out)
        changed = True

if "listen 443" in text and "Strict-Transport-Security" not in text:
    hsts = '    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;\n'

    def add_hsts(m: re.Match[str]) -> str:
        block = m.group(0)
        if "Strict-Transport-Security" in block:
            return block
        return block + hsts

    text2 = re.sub(r"listen\s+443[^\n]*\n", add_hsts, text)
    if text2 != text:
        text = text2
        changed = True

if "sendfile on" not in text and "client_max_body_size 120M;" in text:
    text = text.replace(
        "client_max_body_size 120M;",
        "client_max_body_size 120M;\n\n    sendfile on;\n    tcp_nopush on;\n    gzip off;",
        1,
    )
    changed = True

if changed:
    path.write_text(text)
    print("Nginx: sitemap/favicon/headers de segurança atualizados.")
else:
    print("Nginx: já estava com SEO/headers.")
PY
  nginx -t && systemctl reload nginx
fi

echo "OK — site atualizado na branch $BRANCH"
echo "Confira: https://igrejaceasdrei.com.br/_versao"
echo "Headers: curl -sI https://igrejaceasdrei.com.br/ | grep -Ei 'strict-transport|content-security|x-frame|x-content|referrer-policy|permissions-policy'"
