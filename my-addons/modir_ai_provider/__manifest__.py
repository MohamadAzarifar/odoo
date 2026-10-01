# -*- coding: utf-8 -*-
{
    'name': 'Modir AI Provider',
    'version': '1.0.0',
    'category': 'Hidden',
    'summary': 'Route Odoo Enterprise AI through a custom OpenAI-compatible API (no Odoo IAP)',
    'description': """
Intercepts Enterprise AI IAP calls and forwards them to a configured
OpenAI-compatible endpoint (base URL, API key, chat/embedding models).

Odoo never contacts ai.api.odoo.com when this module is configured.
    """,
    'author': 'Modir.Digital',
    'website': 'https://modir.digital',
    'license': 'LGPL-3',
    'depends': ['ai', 'base_setup'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'post_load': 'post_load',
    'installable': True,
    'application': False,
    'auto_install': False,
}
