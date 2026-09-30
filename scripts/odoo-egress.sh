#!/bin/bash
# Apply /etc/odoo/outbound-allow.conf as an nftables egress filter for the odoo user.
set -euo pipefail

CONF="${ODOO_EGRESS_CONF:-/etc/odoo/outbound-allow.conf}"
ODOO_UID="$(id -u odoo)"

if [[ ! -f "$CONF" ]]; then
  echo "missing $CONF" >&2
  exit 1
fi

mapfile -t entries < <(grep -E -v '^[[:space:]]*(#|$)' "$CONF" | awk '{print $1}')

declare -a v4=()
declare -a v6=()
v4+=("127.0.0.0/8")
v6+=("::1")

add_addr() {
  local addr="$1"
  if [[ "$addr" == *:* ]]; then
    v6+=("$addr")
  else
    v4+=("$addr")
  fi
}

for entry in "${entries[@]}"; do
  if [[ "$entry" == "127.0.0.1" || "$entry" == "::1" ]]; then
    continue
  fi
  if [[ "$entry" == */* || "$entry" =~ ^[0-9.]+$ || "$entry" == *:* ]]; then
    add_addr "$entry"
    continue
  fi
  resolved=0
  while read -r addr _; do
    [[ -n "${addr:-}" ]] || continue
    add_addr "$addr"
    resolved=1
  done < <(getent ahosts "$entry" | awk '{print $1}' | sort -u)
  if [[ "$resolved" -eq 0 ]]; then
    echo "warning: could not resolve $entry" >&2
  fi
done

mapfile -t v4 < <(printf '%s\n' "${v4[@]}" | sort -u)
mapfile -t v6 < <(printf '%s\n' "${v6[@]}" | sort -u)

join_by_comma() {
  local IFS=,
  echo "$*"
}

nft delete table inet odoo_out 2>/dev/null || true
nft add table inet odoo_out
nft add set inet odoo_out allow4 "{ type ipv4_addr; flags interval; }"
nft add set inet odoo_out allow6 "{ type ipv6_addr; flags interval; }"
nft add element inet odoo_out allow4 "{ $(join_by_comma "${v4[@]}") }"
if ((${#v6[@]})); then
  nft add element inet odoo_out allow6 "{ $(join_by_comma "${v6[@]}") }"
fi
nft add chain inet odoo_out output "{ type filter hook output priority 0; policy accept; }"
nft add rule inet odoo_out output "meta skuid != ${ODOO_UID} accept"
nft add rule inet odoo_out output "ip daddr @allow4 accept"
nft add rule inet odoo_out output "ip6 daddr @allow6 accept"
nft add rule inet odoo_out output drop

echo "odoo egress allowlist applied (${#v4[@]} ipv4, ${#v6[@]} ipv6)"
