#!/usr/bin/env bash
# OBSOLETE for AI: Enterprise AI now uses my-addons/modir_ai_provider
# (Settings → AI Provider). Do not use this tunnel for Odoo IAP.
#
# Kept only as an emergency egress helper for unrelated HTTPS needs.
# Prefer adding specific hosts to /etc/odoo/outbound-allow.conf instead.
#
# Usage (legacy):
#   ./scripts/ai-iap-tunnel.sh

set -euo pipefail

echo "WARNING: ai-iap-tunnel.sh is obsolete for Odoo AI (use modir_ai_provider)." >&2
echo "Continuing would open a SOCKS tunnel at 127.0.0.1:1080 on the server." >&2

SSH_KEY="${SSH_KEY:-$HOME/.ssh/odoo_server_62}"
ODOO_HOST="${ODOO_HOST:-root@62.60.198.100}"
REMOTE_SOCKS="${REMOTE_SOCKS:-127.0.0.1:1080}"

exec ssh -i "$SSH_KEY" \
  -o IdentitiesOnly=yes \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -o IPQoS=none \
  -N -R "$REMOTE_SOCKS" \
  "$ODOO_HOST"
