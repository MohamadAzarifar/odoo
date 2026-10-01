#!/bin/bash
set -euo pipefail
systemctl stop odoo
echo === installing ===
sudo -u odoo /opt/odoo/.venv/bin/python /opt/odoo/odoo-bin -c /opt/odoo/odoo.conf -d main \
  -i artarad_web_persian_calendar,approvals,zvy_purchase --stop-after-init 2>&1 | tee /tmp/zvy_purchase_install.log | tail -120
echo === start ===
systemctl start odoo
sleep 6
systemctl is-active odoo
docker exec odoo-postgres psql -U odoo -d main -c "SELECT name, state FROM ir_module_module WHERE name IN ('zvy_purchase','artarad_web_persian_calendar','approvals','product','portal','mail','oe_license') ORDER BY 1;"
curl -s -o /dev/null -w "http80:%{http_code}\n" --max-time 20 http://127.0.0.1/web/login
grep -nE 'ERROR|Traceback|Critical|FAIL' /tmp/zvy_purchase_install.log | tail -30 || true
