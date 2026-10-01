# -*- coding: utf-8 -*-
{
    'name': 'Modir.Digital Website',
    'version': '1.1.5',
    'category': 'Website',
    'summary': 'Homepage for Modir.Digital — enterprise management consultancy & products',
    'description': """
Modern bilingual (Persian / English) homepage for Modir.Digital.
Covers ERP, KM, DMS, CRM, PM, PLM, MRP consultancy and products.
    """,
    'author': 'Modir.Digital',
    'website': 'https://modir.digital',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'views/layout.xml',
        'views/homepage.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'modir_website/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_frontend': [
            'modir_website/static/src/scss/modir.scss',
            'modir_website/static/src/js/modir_home.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
}
