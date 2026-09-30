#!/bin/bash
# First-time Odoo 20.0 bootstrap for /opt/odoo on Ubuntu/Debian.
# Run as root on the server. Does not print or embed GitHub tokens.
set -euo pipefail

# Public clone URL so pulls work without a GitHub deploy key.
REPO="${REPO:-https://github.com/MohamadAzarifar/odoo.git}"
BRANCH="${BRANCH:-20.0}"
ODOO_HOME="${ODOO_HOME:-/opt/odoo}"
ADMIN_PASSWD="${ADMIN_PASSWD:?Set ADMIN_PASSWD}"
DB_NAME="${DB_NAME:-main}"
ADMIN_LOGIN="${ADMIN_LOGIN:?Set ADMIN_LOGIN}"
ADMIN_USER_PASS="${ADMIN_USER_PASS:?Set ADMIN_USER_PASS}"

export DEBIAN_FRONTEND=noninteractive

# Docker's apt repo can 403 after install; packages are already present.
if command -v docker >/dev/null 2>&1; then
  rm -f /etc/apt/sources.list.d/docker.list
fi

echo "==> Installing packages"
apt-get update -y
apt-get install -y \
  ca-certificates curl gnupg git \
  python3 python3-venv python3-dev \
  build-essential libpq-dev libldap2-dev libsasl2-dev libssl-dev \
  libxml2-dev libxslt1-dev libjpeg-dev zlib1g-dev libmagic1 \
  ufw

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installing Docker"
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
fi

echo "==> Creating odoo user"
id -u odoo >/dev/null 2>&1 || useradd --system --home-dir "$ODOO_HOME" --create-home --shell /bin/bash odoo
mkdir -p "$ODOO_HOME"
chown odoo:odoo "$ODOO_HOME"

if [ ! -d "$ODOO_HOME/.git" ]; then
  echo "==> Cloning $REPO ($BRANCH) into $ODOO_HOME"
  rm -rf /tmp/odoo-clone
  sudo -u odoo git clone --depth 1 -b "$BRANCH" --single-branch "$REPO" /tmp/odoo-clone
  shopt -s dotglob nullglob
  for item in /tmp/odoo-clone/* /tmp/odoo-clone/.[!.]* /tmp/odoo-clone/..?*; do
    [ -e "$item" ] || continue
    base=$(basename "$item")
    case "$base" in .|..) continue ;; esac
    rm -rf "$ODOO_HOME/$base"
    mv "$item" "$ODOO_HOME/"
  done
  rm -rf /tmp/odoo-clone
  chown -R odoo:odoo "$ODOO_HOME"
fi

echo "==> Writing docker-compose.yml"
cat > "$ODOO_HOME/docker-compose.yml" <<'YML'
services:
  db:
    image: postgres:16
    container_name: odoo-postgres
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo
    volumes:
      - odoo-db-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  odoo-db-data:
YML
chown odoo:odoo "$ODOO_HOME/docker-compose.yml"
cd "$ODOO_HOME"
docker compose up -d

echo "==> Python venv + requirements"
if [ ! -d "$ODOO_HOME/.venv" ]; then
  sudo -u odoo python3 -m venv "$ODOO_HOME/.venv"
fi
sudo -u odoo "$ODOO_HOME/.venv/bin/pip" install -U pip wheel
sudo -u odoo "$ODOO_HOME/.venv/bin/pip" install -r "$ODOO_HOME/requirements.txt"

echo "==> odoo.conf"
cat > "$ODOO_HOME/odoo.conf" <<CONF
[options]
admin_passwd = ${ADMIN_PASSWD}
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
addons_path = addons
http_port = 8069
http_interface = 0.0.0.0
CONF
chown odoo:odoo "$ODOO_HOME/odoo.conf"
chmod 640 "$ODOO_HOME/odoo.conf"

echo "==> systemd unit"
cat > /etc/systemd/system/odoo.service <<'UNIT'
[Unit]
Description=Odoo 20
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=odoo
Group=odoo
WorkingDirectory=/opt/odoo
ExecStart=/opt/odoo/.venv/bin/python /opt/odoo/odoo-bin -c /opt/odoo/odoo.conf
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable odoo

echo "==> deploy.sh"
cat > "$ODOO_HOME/deploy.sh" <<'DEP'
#!/bin/bash
set -euo pipefail
cd /opt/odoo
sudo -u odoo git fetch origin
sudo -u odoo git checkout 20.0
sudo -u odoo git pull --ff-only origin 20.0
systemctl restart odoo
systemctl --no-pager status odoo
DEP
chmod 755 "$ODOO_HOME/deploy.sh"

echo "==> Firewall (allow 22 and 8069)"
ufw allow OpenSSH || true
ufw allow 8069/tcp || true
ufw --force enable || true

echo "==> Waiting for Postgres"
for i in $(seq 1 30); do
  if docker exec odoo-postgres pg_isready -U odoo >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "==> Bootstrap database ${DB_NAME}"
systemctl stop odoo || true
sudo -u odoo "$ODOO_HOME/.venv/bin/python" "$ODOO_HOME/odoo-bin" -c "$ODOO_HOME/odoo.conf" \
  -d "$DB_NAME" -i base --stop-after-init --without-demo=all

echo "==> Set admin login/password"
sudo -u odoo "$ODOO_HOME/.venv/bin/python" "$ODOO_HOME/odoo-bin" shell -c "$ODOO_HOME/odoo.conf" -d "$DB_NAME" <<PY
admin = env.ref('base.user_admin')
admin.login = '${ADMIN_LOGIN}'
admin.password = '${ADMIN_USER_PASS}'
env.cr.commit()
print('admin updated:', admin.login)
PY

systemctl start odoo
sleep 3
systemctl --no-pager status odoo || true
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8069/web/database/selector || true
echo "==> Done. Open http://$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):8069"
