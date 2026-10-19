# -*- coding: utf-8 -*-
{
    'name': 'IT Orbit Website',
    'version': '1.3.6',
    'category': 'Website',
    'summary': 'Homepage for مدارگسترش (IT Orbit) — national software platforms',
    'description': """
Modern bilingual (Persian / English) homepage for مدار گسترش فناوری اطلاعات.
Products: Orbit@ll, EPIC, ACE, Citadel, NAD.
Bitcoin DeFi visual system: true void, orange and gold glow, geometric type.
    """,
    'author': 'مدارگسترش',
    'website': 'https://www.itorbit.net',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'views/layout.xml',
        'views/homepage.xml',
        'views/contactus.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'itorbit_website/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_frontend': [
            'itorbit_website/static/src/scss/itorbit.scss',
            'itorbit_website/static/src/js/itorbit_home.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
}
