# Odoo deployment (Linux server)

Production layout on the server. Do not store passwords or SSH keys in this file.

## Layout

| Path | Purpose |
|------|---------|
| `/opt/odoo` | Git clone (`origin` = `git@github.com:MohamadAzarifar/odoo.git`) |
| `/opt/odoo/.venv` | Python virtualenv |
| `/opt/odoo/odoo.conf` | Local config (not in `origin/20.0`) |
| `/opt/odoo/docker-compose.yml` | Postgres only (not in `origin/20.0`) |
| `/opt/odoo/deploy.sh` | Pull `20.0` + restart Odoo (not in `origin/20.0`) |
| `/etc/systemd/system/odoo.service` | systemd unit |
| `/etc/nginx/sites-available/odoo` | Reverse proxy, port 80 → Odoo |

Branch used for every deploy: **`20.0`**.

The server clone is a shallow checkout (`--depth 1`) of `https://github.com/MohamadAzarifar/odoo.git`. `git pull --ff-only origin 20.0` works against that remote.

`addons_path` currently: `addons` only (`my-addons` / enterprise later).

## Prerequisites (first-time)

- Docker Engine + Compose plugin
- Python ≥ 3.12, `python3-venv`, `git`
- Build deps for wheels (`build-essential`, `libpq-dev`, etc.)
- Read-only GitHub deploy key on the server, registered on the repo
- System user `odoo` owning `/opt/odoo`

## First-time setup (summary)

Automated path (as root on the server), after a GitHub deploy key is registered:

```bash
# copy scripts/server-bootstrap.sh to the server, then:
DEPLOY_KEY_READY=1 bash server-bootstrap.sh
```

Manual checklist:

1. Install packages and create user `odoo` / `/opt/odoo`.
2. Add a GitHub deploy key; clone `-b 20.0 --single-branch` into `/opt/odoo`.
3. Write server-local `docker-compose.yml` (Postgres 16, user/db matching `odoo.conf`) and `docker compose up -d`.
4. Create venv and `pip install -r requirements.txt`.
5. Write `odoo.conf` (`db_*`, `addons_path = addons`, `http_port = 8069`, `http_interface = 0.0.0.0`).
6. Install and enable `odoo.service`; start Odoo.
7. Create database `main` once (`-i base --stop-after-init`), then set admin login.
8. Allow TCP **8069** on the host firewall if enabled.

## Redeploy

On the server:

```bash
/opt/odoo/deploy.sh
```

That script:

1. `git fetch` / `checkout 20.0` / `pull --ff-only origin 20.0` as user `odoo`
2. `systemctl restart odoo`
3. Prints `systemctl status odoo`

Manual equivalent:

```bash
cd /opt/odoo
sudo -u odoo git fetch origin
sudo -u odoo git checkout 20.0
sudo -u odoo git pull --ff-only origin 20.0
sudo systemctl restart odoo
```

If `requirements.txt` changed, also:

```bash
sudo -u odoo /opt/odoo/.venv/bin/pip install -r /opt/odoo/requirements.txt
sudo systemctl restart odoo
```

## Service commands

```bash
sudo systemctl status odoo
sudo systemctl restart odoo
sudo journalctl -u odoo -f
cd /opt/odoo && sudo docker compose ps
```

## Notes

- `docker-compose.yml`, `odoo.conf`, and `deploy.sh` are **server-local**; they are not on `origin/20.0`.
- Public HTTP is **port 80** via Nginx. Odoo listens on **8069**. `odoo.conf` has `proxy_mode = True`.
- Nginx site: `/etc/nginx/sites-available/odoo`. `/` and `/websocket` are proxied to `127.0.0.1:8069`.
- Outbound from the `odoo` user is denied except destinations listed in `/etc/odoo/outbound-allow.conf`. Apply or refresh with `systemctl start odoo-egress.service` (timer refreshes DNS every 30 minutes).
