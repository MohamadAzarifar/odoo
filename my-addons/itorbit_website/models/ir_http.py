from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _match(cls, path):
        # Anonymous visits with no language cookie follow the website default
        # (Persian). English stays available at /en and via the language switcher.
        if request and path and not path.startswith(('/web', '/odoo', '/websocket', '/bus', '/longpolling')):
            try:
                website = request.env['website'].sudo().search([], limit=1)
                code = website.default_lang_id.code
                if code:
                    request.update_context(lang=code)
            except Exception:
                pass
        return super()._match(path)
