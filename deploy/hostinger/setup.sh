#!/usr/bin/env bash
# Setup do site IGREJA CEASDREI em VPS Hostinger (Ubuntu).
# Rode COMO ROOT no servidor:
#   curl -fsSL ... | bash
# ou:
#   git clone ... && bash deploy/hostinger/setup.sh

set -euo pipefail

APP_USER="${APP_USER:-www-data}"
APP_DIR="${APP_DIR:-/var/www/igreja-ceadrei}"
DATA_DIR="${DATA_DIR:-/var/data/igreja-ceadrei}"
REPO_URL="${REPO_URL:-https://github.com/pethersonrdc/igreja-ceadrei.git}"
BRANCH="${BRANCH:-main}"
DOMAIN="${DOMAIN:-igrejaceasdrei.com.br}"

echo "==> Pacotes"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx git curl

echo "==> Pastas"
mkdir -p "$APP_DIR" "$DATA_DIR" "$DATA_DIR/uploads"
chown -R "$APP_USER:$APP_USER" "$DATA_DIR"

echo "==> Código ($BRANCH)"
if [[ -d "$APP_DIR/.git" ]]; then
  cd "$APP_DIR"
  sudo -u "$APP_USER" git fetch origin
  sudo -u "$APP_USER" git checkout "$BRANCH"
  sudo -u "$APP_USER" git pull origin "$BRANCH"
else
  rm -rf "$APP_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
  chown -R "$APP_USER:$APP_USER" "$APP_DIR"
fi

cd "$APP_DIR"

echo "==> Python venv + dependências"
sudo -u "$APP_USER" python3 -m venv .venv
sudo -u "$APP_USER" .venv/bin/pip install --upgrade pip
sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt

echo "==> Arquivo .env"
ENV_FILE="$APP_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  SECRET="$(openssl rand -hex 24)"
  cat > "$ENV_FILE" <<EOF
SECRET_KEY=$SECRET
ADMIN_PASSWORD=ceasdrei
DATA_DIR=$DATA_DIR
EOF
  chown "$APP_USER:$APP_USER" "$ENV_FILE"
  chmod 640 "$ENV_FILE"
else
  # Garante DATA_DIR
  if ! grep -q '^DATA_DIR=' "$ENV_FILE"; then
    echo "DATA_DIR=$DATA_DIR" >> "$ENV_FILE"
  fi
fi

# Carrega env no systemd via EnvironmentFile
echo "==> systemd"
install -m 644 "$APP_DIR/deploy/hostinger/igreja-ceadrei.service" /etc/systemd/system/igreja-ceadrei.service
# Ajusta caminhos se customizados
sed -i "s|/var/www/igreja-ceadrei|$APP_DIR|g" /etc/systemd/system/igreja-ceadrei.service
sed -i "s|/var/data/igreja-ceadrei|$DATA_DIR|g" /etc/systemd/system/igreja-ceadrei.service

systemctl daemon-reload
systemctl enable igreja-ceadrei
systemctl restart igreja-ceadrei

echo "==> Nginx"
install -m 644 "$APP_DIR/deploy/hostinger/nginx.conf" /etc/nginx/sites-available/igreja-ceadrei
sed -i "s|igrejaceasdrei.com.br|$DOMAIN|g" /etc/nginx/sites-available/igreja-ceadrei
sed -i "s|/var/www/igreja-ceadrei|$APP_DIR|g" /etc/nginx/sites-available/igreja-ceadrei
ln -sfn /etc/nginx/sites-available/igreja-ceadrei /etc/nginx/sites-enabled/igreja-ceadrei
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo
echo "==> Pronto"
echo "App:      $APP_DIR"
echo "DATA_DIR: $DATA_DIR  (posts/fotos ficam aqui — não somem no update)"
echo "Domínio:  $DOMAIN  (aponte o DNS A para este IP)"
echo
echo "Status:   systemctl status igreja-ceadrei --no-pager"
echo "Logs:     journalctl -u igreja-ceadrei -f"
echo
echo "Atualizar depois:"
echo "  cd $APP_DIR && sudo -u $APP_USER git pull origin $BRANCH && sudo -u $APP_USER .venv/bin/pip install -r requirements.txt && systemctl restart igreja-ceadrei"
