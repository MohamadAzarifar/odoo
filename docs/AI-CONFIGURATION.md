# Odoo AI configuration runbook

How to enable Enterprise AI on a deployment **without** Odoo IAP (`ai.api.odoo.com`).
LLM traffic goes through **`modir_ai_provider`** to an OpenAI-compatible API you control.

Do **not** store API keys or passwords in this file. Set them only in the database / Settings UI.

Related: [DEPLOYMENT.md](DEPLOYMENT.md) (server layout, Postgres, egress service).

---

## Rules (non-negotiable)

1. **No Odoo cloud AI.** Do not allow `ai.api.odoo.com`, `iap-scraper.odoo.com`, or rely on Odoo IAP credits for chat/embeddings.
2. **Custom provider only.** Use `my-addons/modir_ai_provider` with Base URL, API key, chat model, and embedding model.
3. **Egress allowlist.** The `odoo` OS user may only reach destinations in `/etc/odoo/outbound-allow.conf`. Add the provider hostname; keep Odoo IAP hosts commented out.
4. **No IAP SOCKS tunnel for AI.** Do not use `scripts/ai-iap-tunnel.sh` or `odoo.service.d/proxy.conf` for AI. Those were interim workarounds before the custom provider.
5. **pgvector required.** Enterprise AI needs PostgreSQL with the `vector` extension (image `pgvector/pgvector:pg16`).
6. **Enterprise addons on path.** `addons_path` must include `enterprise-addons` (before community `addons`).

---

## Architecture

```text
Odoo Enterprise AI (ai / ai_agentic / ai_mcp)
        │
        ▼  (monkey-patched IAP entry points)
modir_ai_provider
        │
        ▼  HTTPS (egress-allowed host only)
OpenAI-compatible API  (e.g. https://…/v1/chat/completions)
```

- Sync routes (`1/get_completions_sync`, embeddings) call the provider HTTP API directly.
- Async agent chat (`1/get_completions`) runs the model, then continues the `ai.session` **in-process** (no HTTP self-callback to `/ai/completion_result_ready`). Self-webhooks against the same Odoo workers can deadlock and leave the UI stuck on **Thinking**.

Config parameters (Settings → **AI Provider**):

| Parameter | Purpose |
|-----------|---------|
| `modir_ai.base_url` | OpenAI-compatible base, e.g. `https://api.example.com/v1` |
| `modir_ai.api_key` | Bearer token |
| `modir_ai.chat_model` | Chat model id |
| `modir_ai.embedding_model` | Embedding model id (**1536 dimensions** — Odoo `ai.embedding` vector size) |

---

## Prerequisites checklist

- [ ] Odoo 20 with `enterprise-addons` and valid Enterprise DB
- [ ] `addons_path` includes `my-addons`, `enterprise-addons`, `addons`
- [ ] Postgres image **`pgvector/pgvector:pg16`** (not stock `postgres:16`)
- [ ] Extension `vector` on the app database
- [ ] `/etc/odoo/outbound-allow.conf` + `odoo-egress.service` (see deployment runbook)
- [ ] Provider URL reachable from the server (test as user `odoo`)

### Switch Postgres to pgvector (if still on `postgres:16`)

On the server (data volume is reused; stop Odoo first):

```bash
systemctl stop odoo
cd /opt/odoo
# edit docker-compose.yml: image: pgvector/pgvector:pg16
# If docker pull fails on IPv6, temporarily prefer IPv4, then restore.
docker compose pull db
docker compose up -d db
# wait until ready:
docker exec odoo-postgres pg_isready -U odoo
docker exec odoo-postgres psql -U odoo -d main -c 'CREATE EXTENSION IF NOT EXISTS vector;'
docker exec odoo-postgres psql -U odoo -d main -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"
systemctl start odoo
```

Repo templates already use `pgvector/pgvector:pg16` in `docker-compose.yml` and `scripts/server-bootstrap.sh`.

---

## Install Enterprise AI + custom provider

### 1. Update apps list and install modules

Stop the long-running service so `-i` can take the DB, then:

```bash
systemctl stop odoo
sudo -u odoo /opt/odoo/.venv/bin/python /opt/odoo/odoo-bin \
  -c /opt/odoo/odoo.conf -d main \
  -i ai_agentic,modir_ai_provider \
  --stop-after-init
systemctl start odoo
```

Notes:

- `ai_agentic` pulls in base `ai` and related deps; `ai_mcp` often auto-installs with `ai`.
- `ai_auto_install` only auto-enables AI when `pgvector` is available; without the extension, AI stays uninstalled.
- Confirm:

```bash
docker exec odoo-postgres psql -U odoo -d main -c "
SELECT name, state FROM ir_module_module
WHERE name IN ('ai','ai_agentic','ai_mcp','modir_ai_provider')
ORDER BY name;"
```

Expect all listed as **`installed`**.

### 2. Configure the provider

**UI:** Settings → **AI Provider** → set Base URL, API Key, Chat Model, Embedding Model → Save.

**Or shell** (Odoo 20 uses `set_str` / `get_str`, not `set_param`):

```bash
systemctl stop odoo
sudo -u odoo /opt/odoo/.venv/bin/python /opt/odoo/odoo-bin shell \
  -c /opt/odoo/odoo.conf -d main --no-http <<'PY'
ICP = env['ir.config_parameter'].sudo()
ICP.set_str('modir_ai.base_url', 'https://YOUR_HOST/.../v1')
ICP.set_str('modir_ai.api_key', 'YOUR_KEY')
ICP.set_str('modir_ai.chat_model', 'YOUR_CHAT_MODEL')
ICP.set_str('modir_ai.embedding_model', 'openai/text-embedding-3-small')  # must be 1536-dim
env.cr.commit()
print('ok', bool(ICP.get_str('modir_ai.base_url')), ICP.get_str('modir_ai.chat_model'))
PY
systemctl start odoo
```

Example shape used in production (values are placeholders — use your own secrets):

- Base URL: `https://ai.liara.ir/api/<project-id>/v1`
- Chat model: e.g. `anthropic/claude-opus-5.5`
- Embedding: e.g. `openai/text-embedding-3-small`

### 3. Egress: allow provider host only (for AI)

Edit `/etc/odoo/outbound-allow.conf` (repo template: `scripts/outbound-allow.conf`):

```text
127.0.0.1
::1

# Provider hostname from modir_ai.base_url
ai.liara.ir

# Keep Odoo IAP commented
# ai.api.odoo.com
# iap.odoo.com
# iap-services.odoo.com
# iap-scraper.odoo.com
```

Apply:

```bash
systemctl restart odoo-egress.service
# Prefer restart over start — an already-active oneshot may not re-run on start alone.
journalctl -u odoo-egress.service -n 10 --no-pager
```

Verify as the Odoo user:

```bash
sudo -u odoo curl -4 -sS -o /dev/null -w "%{http_code}\n" --connect-timeout 15 https://YOUR_PROVIDER_HOST/
```

### 4. Remove obsolete IAP proxy (if present)

```bash
rm -f /etc/systemd/system/odoo.service.d/proxy.conf
systemctl daemon-reload
systemctl restart odoo
# Ensure no leftover SOCKS on the server:
ss -ltn | grep 1080 || echo 'no socks listener'
```

---

## Smoke tests

### Provider HTTP (from the server)

```bash
# Replace URL / key / model
curl -4 -sS -o /dev/null -w "models:%{http_code}\n" \
  -H "Authorization: Bearer YOUR_KEY" \
  "https://YOUR_BASE/v1/models"

curl -4 -sS -w "\nchat:%{http_code}\n" \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"YOUR_CHAT_MODEL","messages":[{"role":"user","content":"Say OK"}],"max_tokens":16}' \
  "https://YOUR_BASE/v1/chat/completions"
```

### Through Odoo (patched IAP entry points)

```bash
systemctl stop odoo
sudo -u odoo /opt/odoo/.venv/bin/python /opt/odoo/odoo-bin shell \
  -c /opt/odoo/odoo.conf -d main --no-http <<'PY'
from odoo.addons.ai.utils.ai_utils import call_odoo_ai
from odoo.addons.modir_ai_provider import provider as p
print('configured', p.is_configured(env), 'host', p.provider_host(env))
res = call_odoo_ai(env, '1/get_completions_sync', {
    'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': 'Reply with exactly: OK'}]}],
    'instructions': 'Be brief.',
    'tools': [],
}, timeout=90)
print('CHAT', res['result']['content'][0].get('text', '')[:80])
emb = call_odoo_ai(env, '1/get_embeddings', {
    'input': [{'title': 't', 'content': 'hello'}],
    'model': env['ir.config_parameter'].sudo().get_str('modir_ai.embedding_model'),
    'mode': 'document',
}, timeout=60)
print('EMB dims', len(emb['embeddings'][0]))
print('default_emb', call_odoo_ai(env, '1/get_default_embedding_model', {}))
PY
systemctl start odoo
```

Expect chat text, embedding length **1536**, and log line:

`modir_ai_provider: patched Odoo AI IAP entry points (IAP disabled)`

### UI

1. Open **AI → Agents**.
2. Open an agent chat; send a short message.
3. Confirm the reply appears and **Thinking** clears when finished.
4. Optional: MCP module exposes `/mcp` (API key with MCP scope). Native MCP still depends on Enterprise AI being installed; model calls for agents use the custom provider.

---

## Known fixes already in the tree

These landed while enabling AI on the first production host; they should already be in the repo used for deploys:

| Issue | Fix |
|-------|-----|
| Opening an agent crashed with `updateActionState` on undefined `props` | Guard in `addons/mail/.../discuss_app_model.js` and `enterprise-addons/ai_agentic/.../discuss_client_action_patch.js` |
| Error dialog “Copy” failed on HTTP (`clipboard` undefined) | Guard in `addons/web/.../error_dialogs.js` |
| Agent chat stuck on **Thinking** after tools/replies | `modir_ai_provider` delivers async completions in-process (no self-HTTP webhook) |
| Clipboard helpers broke tours on HTTP | Guard in `addons/web_tour/.../tour_helpers_clipboard.js` |

After pulling JS/Python fixes on a live host, clear asset attachments and restart:

```bash
docker exec odoo-postgres psql -U odoo -d main -c \
  "DELETE FROM ir_attachment WHERE name LIKE '%assets_web%' OR url LIKE '%/web/assets/%';"
systemctl restart odoo
```

Hard-refresh the browser (Ctrl/Cmd+Shift+R).

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| AI / Agents missing in Apps | `enterprise-addons` on `addons_path`? Update Apps List? `pgvector` installed? |
| `ai_*` modules uninstalled | `CREATE EXTENSION vector;` then install `ai_agentic` |
| “Custom AI provider is not configured” | Settings → AI Provider (or `modir_ai.*` params) |
| Provider timeouts from Odoo | Hostname in `outbound-allow.conf`? `systemctl restart odoo-egress`? `sudo -u odoo curl` to host? |
| Embeddings / RAG fail | Embedding model set? Vectors must be **1536** dims (padding/truncation is last resort) |
| Transcription / realtime | Not supported by `modir_ai_provider` (raises a clear error) |
| Stuck **Thinking** / `loop_state = waiting_model` | Confirm in-process delivery code is deployed; reset stuck rows if needed: `UPDATE ai_session SET loop_state='ready' WHERE loop_state <> 'ready';` |
| Logs show webhook timeouts to `127.0.0.1:8069` | Old provider build — upgrade `modir_ai_provider` to in-process delivery |
| Docker Hub pull fails (IPv6) | Prefer IPv4 for the pull, then restore IPv6 if required |

Useful log filter:

```bash
journalctl -u odoo -f | grep -iE 'modir_ai|ai\.session|get_completions'
```

---

## Deploy order (new environment)

1. Base Odoo per [DEPLOYMENT.md](DEPLOYMENT.md) with **pgvector** Postgres and Enterprise on `addons_path`.
2. `CREATE EXTENSION vector` on the app DB.
3. Install `ai_agentic` + `modir_ai_provider`.
4. Set provider settings (URL / key / models) — secrets only in DB.
5. Allow provider host in `/etc/odoo/outbound-allow.conf`; restart `odoo-egress`.
6. Ensure no IAP SOCKS proxy drop-in.
7. Run smoke tests; open **AI → Agents** in the UI.

---

## Module reference

| Path | Role |
|------|------|
| `my-addons/modir_ai_provider/` | Custom provider bridge + Settings UI |
| `enterprise-addons/ai/` | Base Enterprise AI |
| `enterprise-addons/ai_agentic/` | AI app (Agents menu) |
| `enterprise-addons/ai_mcp/` | Native MCP server (`/mcp`) |
| `enterprise-addons/ai_auto_install/` | Auto-installs `ai` when pgvector exists |
| `scripts/outbound-allow.conf` | Template for egress allowlist |
| `scripts/ai-iap-tunnel.sh` | **Obsolete** for AI — do not use |
