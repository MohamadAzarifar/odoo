# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.itorbit_website import hooks
    # Skip theme SCSS rewrite on upgrade — it can wipe /_custom/ attachments.
    hooks.setup_website(env, apply_theme=False)
