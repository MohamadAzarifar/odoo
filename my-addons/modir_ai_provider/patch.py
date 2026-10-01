# -*- coding: utf-8 -*-
"""Monkey-patch Odoo AI IAP entry points to use the custom provider."""
from __future__ import annotations

import logging

from odoo import api, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

_patched = False


def apply_patches():
    global _patched
    if _patched:
        return
    try:
        from odoo.addons.ai.utils import ai_utils
        from odoo.addons.ai.models import ai_session, ai_embedding, mail_call_artifact
        from odoo.addons.ai.controllers import ai as ai_controller
    except ImportError:
        _logger.warning('modir_ai_provider: ai module not available, skip patch')
        return

    from odoo.addons.modir_ai_provider import provider as modir_provider

    def call_odoo_ai(env, route, params=None, add_iap_token=True, timeout=60):
        # Always intercept — never contact Odoo IAP while this module is installed.
        return modir_provider.handle_route(env, route, params or {}, timeout=timeout)

    def call_odoo_ai_transport(connection, route, params, timeout=30, *, raise_user_error=True):
        dbname = (params or {}).get('webhook_dbname')
        if not dbname:
            raise UserError('Custom AI provider: missing database for AI transport.')
        try:
            with Registry(dbname).cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                return modir_provider.handle_route(env, route, params or {}, timeout=timeout)
        except Exception:
            _logger.exception(
                'modir_ai_provider: transport bridge failed for db=%s route=%s',
                dbname, route,
            )
            raise

    ai_utils.call_odoo_ai = call_odoo_ai
    ai_utils.call_odoo_ai_transport = call_odoo_ai_transport

    # Rebind names already imported by reference in other modules.
    ai_session.call_odoo_ai = call_odoo_ai
    ai_session.call_odoo_ai_transport = call_odoo_ai_transport
    ai_embedding.call_odoo_ai = call_odoo_ai
    mail_call_artifact.call_odoo_ai = call_odoo_ai
    ai_controller.call_odoo_ai = call_odoo_ai

    _patched = True
    _logger.info('modir_ai_provider: patched Odoo AI IAP entry points (IAP disabled)')
