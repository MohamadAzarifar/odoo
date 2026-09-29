import logging
import secrets
import requests

from odoo import api, fields, models, _
from odoo.api import NewId

_logger = logging.getLogger(__name__)


class Obox(models.Model):
    _name = "obox.obox"
    _description = "Obox"

    active = fields.Boolean(default=True)
    name = fields.Char('Name', required=True)
    serial_number = fields.Char(string="Serial Number", required=True)
    local_ip = fields.Char(string="Local IP", readonly=True)
    token = fields.Char(readonly=True, required=True)
    services = fields.Json()
    external_websocket_channel = fields.Char(
        string="Websocket Channel for the device", compute="_compute_websocket_channel"
    )
    internal_websocket_channel = fields.Char(
        string="Websocket Channel within Odoo", compute="_compute_websocket_channel"
    )
    state = fields.Selection(
        [("01_pairing", "Pairing"), ("02_paired", "Paired")],
        string="State",
        default="01_pairing",
        readonly=True,
    )
    remote_debug_enabled = fields.Boolean()

    # Queue states
    pending_queue_count = fields.Integer(
        string="Pending Count", compute="_compute_pending_queue_ids", readonly=True
    )
    pending_queue_ids = fields.Many2many(
        "obox.queue",
        string="Pending Actions",
        compute="_compute_pending_queue_ids",
        readonly=True,
    )
    finished_queue_ids = fields.Many2many(
        "obox.queue",
        string="Finished Actions",
        compute="_compute_pending_queue_ids",
        readonly=True,
    )

    device_ids = fields.One2many("obox.device", "obox_id")
    device_count = fields.Integer(compute='_compute_device_count')

    _unique_serial_number = models.Constraint(
        "unique (serial_number)",
        "An Obox must have a unique serial number.",
    )

    def _compute_device_count(self):
        for record in self:
            record.device_count = len(record.device_ids)

    def _compute_websocket_channel(self):
        for record in self:
            record.external_websocket_channel = f"obox_{record.token}"
            record.internal_websocket_channel = f"odoo_{record.token}"

    def _compute_pending_queue_ids(self):
        for record in self:
            if isinstance(record.id, NewId):
                record.pending_queue_count = 0
                continue

            actions = self.env["obox.queue"].search([
                "|",
                ("obox_id", "=", record.id),
                ("obox_id", "=", False),
            ])

            pending_actions = actions.filtered(lambda a: a.status == "pending")
            finished_actions = actions.filtered(lambda a: a.status == "done")
            record.pending_queue_ids = pending_actions
            record.pending_queue_count = len(pending_actions)
            record.finished_queue_ids = finished_actions

    def action_open_queue(self):
        self.ensure_one()
        return {
            "name": _("Queue"),
            "view_mode": "list,form",
            "res_model": "obox.queue",
            "type": "ir.actions.act_window",
            "domain": [
                "|",
                ("obox_id", "=", self.id),
                ("obox_id", "=", False),
            ],
        }

    def action_check_websocket(self):
        """
        This will launch a "PING" action to the device, which will be
        processed by the device if it's connected.
        The device will initiate a request to the customer database.
        """
        self.env["obox.queue"].create({
            "action_type": "test",
            "obox_id": self.id,
            "payload": {"url": "/odoo/health", "payload": {}, "method": "GET"},
        })
        return True

    def action_restart_obox(self):
        self.env["obox.queue"].create({
            "action_type": "restart",
            "obox_id": self.id,
            "payload": {"url": "/odoo/restart", "payload": {}, "method": "GET"},
        })
        return True

    def action_disconnect_obox(self):
        self.env["obox.queue"].create({
            "action_type": "disconnect",
            "obox_id": self.id,
            "payload": {"url": "/odoo/disconnect", "payload": {}, "method": "GET"},
        })
        return True

    def action_discover_devices(self):
        self.env["obox.queue"].create({
            "action_type": "discover_devices",
            "obox_id": self.id,
            "payload": {"url": "/odoo/discover_devices", "payload": {}, "method": "GET"},
        })
        return True

    def action_enable_remote_debug(self, token: str):
        self.env["obox.queue"].create({
            "action_type": "remote_debug",
            "obox_id": self.id,
            "payload": {"url": f"/sos/v1/enable?token={token}", "payload": {}, "method": "GET"},
        })
        return True

    def action_disable_remote_debug(self):
        self.env["obox.queue"].create({
            "action_type": "remote_debug",
            "obox_id": self.id,
            "payload": {"url": "/sos/v1/disable", "payload": {}, "method": "GET"},
        })
        return True

    def dispatch_new_action(self):
        for record in self:
            if record.external_websocket_channel:
                record.env["bus.bus"]._sendone(
                    record.external_websocket_channel, "ACTION", ""
                )

    def get_next_actions(self):
        self.ensure_one()
        return self.env["obox.queue"].get_next_actions(self)

    @api.model
    def connect_offline(self, ip_address, serial_number):
        icp_sudo = self.env["ir.config_parameter"].sudo()
        token = secrets.token_hex()
        serial_number = serial_number.strip().upper()
        db_url = icp_sudo.get_base_url()
        db_uuid = icp_sudo.get_str("database.uuid")
        obox = self.search(
            [("serial_number", "=", serial_number)], limit=1
        )
        if not obox:
            obox = self.create({"name": f"Obox {serial_number}", "serial_number": serial_number, "token": token})
        else:
            obox.write({"token": token, "active": True, "state": "01_pairing"})
        connect_url = f"http://{ip_address}/odoo/connect?db_url={db_url}&db_uuid={db_uuid}&token={token}"
        return {"id": obox.id, "url": connect_url}

    @api.model
    def pair_obox(self, pairing_code):
        try:
            icp_sudo = self.env["ir.config_parameter"].sudo()
            token = secrets.token_hex()
            response = requests.post(
                "https://iot-proxy.odoo.com/odoo-enterprise/iot/connect-db",
                json={
                    "params": {
                        "pairing_code": pairing_code,
                        "database_url": icp_sudo.get_base_url(),
                        "token": token,
                        "db_uuid": icp_sudo.get_str("database.uuid"),
                        "enterprise_code": icp_sudo.get_str("database.enterprise_code"),
                    },
                },
                timeout=5,
            )

            response.raise_for_status()
            json = response.json()

            # Typically occurs when the used pairing code wasn't found on iot proxy
            error = json.get("error")
            if error:
                _logger.warning(
                    "Error when using pairing code %s. IoT Proxy responded with an error message: %s",
                    pairing_code,
                    error,
                )
                return

            result = json.get("result")
            if result and result[0]:
                serial_number = result[0]["serial_number"]
                box = self.with_context(active_test=False).search(
                    [("serial_number", "=", serial_number)], limit=1
                )
                if not box:
                    box = self.create({"name": "Obox " + serial_number, "serial_number": serial_number, "token": token})
                else:
                    box.update({"token": token, "active": True, "state": "01_pairing"})

                return box.id
            else:
                _logger.warning(
                    "Failed to connect the Obox with pairing code %s: %s",
                    pairing_code,
                    json,
                )
        except (requests.exceptions.RequestException, ValueError):
            _logger.exception(
                "Failed to use the provided pairing code %s to connect an Obox",
                pairing_code,
            )
