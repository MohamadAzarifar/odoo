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
| `/etc/odoo/resources.conf` | CPU/RAM caps per component (Odoo, Postgres, Nginx) |
| `/usr/local/sbin/odoo-resources.sh` | Applies `resources.conf` (systemd + Compose + `odoo.conf`) |
| `/opt/odoo/docker-compose.override.yml` | Generated Postgres mem/cpu/shm limits |

Branch used for every deploy: **`20.0`**.

The server clone is a shallow checkout (`--depth 1`) of `https://github.com/MohamadAzarifar/odoo.git`. `git pull --ff-only origin 20.0` works against that remote.

`addons_path`: `my-addons`, `enterprise-addons`, `addons`.

Postgres image: **`pgvector/pgvector:pg16`** (required for Enterprise AI). Extension `vector` must exist on DB `main`.

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
3. Write server-local `docker-compose.yml` (`pgvector/pgvector:pg16`, user/db matching `odoo.conf`) and `docker compose up -d`.
4. Create venv and `pip install -r requirements.txt`.
5. Write `odoo.conf` (`db_*`, `addons_path` with `my-addons` + `enterprise-addons` + `addons`, `http_port = 8069`, `http_interface = 0.0.0.0`).
6. Install and enable `odoo.service`; start Odoo.
7. Create database `main` once (`-i base --stop-after-init`), then set admin login.
8. `CREATE EXTENSION vector;` on `main`, then install Enterprise AI (`-i ai_agentic`).
9. Allow TCP **8069** on the host firewall if enabled.

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
sudo systemctl start odoo-resources.service   # re-apply /etc/odoo/resources.conf
```

## Notes

- `docker-compose.yml`, `odoo.conf`, and `deploy.sh` are **server-local**; they are not on `origin/20.0`.
- Public HTTP is **port 80** via Nginx. Odoo listens on **8069**. `odoo.conf` has `proxy_mode = True`.
- Nginx site: `/etc/nginx/sites-available/odoo`. `/` → `127.0.0.1:8069`. With `workers > 0`, `/websocket` and `/longpolling` → gevent on **8072** (`odoo-resources` keeps that in sync).
- Outbound from the `odoo` user is denied except destinations listed in `/etc/odoo/outbound-allow.conf`. Apply with `systemctl restart odoo-egress.service` (timer refreshes DNS every 30 minutes).
- Enterprise AI uses **`modir_ai_provider`** (OpenAI-compatible URL / model / API key in **Settings → AI Provider**). It never calls `ai.api.odoo.com`. Provider host currently allowed: `ai.liara.ir` (see `/etc/odoo/outbound-allow.conf`).
- Do **not** use the old IAP SOCKS tunnel (`scripts/ai-iap-tunnel.sh` / `odoo.service.d/proxy.conf`) for AI.
- Resource caps live in `/etc/odoo/resources.conf` (defaults sized for **2 vCPU / ~4 GiB**: Odoo `MemoryMax=2G` + `workers=2`, Postgres `mem_limit=1g`, Nginx `MemoryMax=128M`). Edit that file, then `systemctl start odoo-resources.service`.
