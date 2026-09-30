# -*- coding: utf-8 -*-
{
    'name': "Artarad Web Persian Calendar",

    'summary': 
        """
        Persian Calendar in Odoo V20
        """,

    'description':
        """
            This module allows users to select Jalaali or Gregorian calendars regardless of selected language.
            Supported in: tree/form/kanban/pivot/gantt/graph/calendar/search views and chatter.
        """,

    'author': "Artarad Team",
    
    'website': "https://www.artadoo.ir",

    'license': 'LGPL-3',

    'category': 'web',
    
    'version': '20.0.1',

    'depends': ['web', 'mail' ,'base_import', 'calendar', 'web_gantt'],

    'external_dependencies': {
        'python': ['jdatetime', 'num2fawords']
    },

    'data': [
        'data/g2j.sql',
        'views/res_users_view.xml',
        'views/ir_sequence_views.xml',
    ],

    'assets': {
        "web._assets_core": [
            # for all
            ('before', 'web/static/src/session.js', 'artarad_web_persian_calendar/static/src/js/odoo.js',),
            ('after', 'web/static/lib/luxon/luxon.js', 'artarad_web_persian_calendar/static/src/js/luxon-jalaali.js',),
            # dates.js replaces exported functions of @web/core/l10n/dates. The module
            # loader starts a module as soon as its dependencies are defined, picking
            # jobs in bundle order, so the patch has to be declared before any consumer.
            ('after', 'web/static/src/module_loader.js', 'artarad_web_persian_calendar/static/src/js/dates.js'),
            
            # for datetime picker
            ('after', 'web/static/src/core/datetime/datetime_picker.js', 'artarad_web_persian_calendar/static/src/js/datetimepicker/datetime_picker.js')
        ],

        'web.assets_frontend': [
            ('after', 'web/static/lib/luxon/luxon.js', 'artarad_web_persian_calendar/static/src/js/luxon-jalaali.js',),
        ],

        'web.assets_backend': [
            # These three replace exported functions instead of patching a class, so
            # they have to be declared before the modules that import those functions.
            ('after', 'web/static/src/module_loader.js', 'artarad_web_persian_calendar/static/src/js/search/dates.js',),
            ('after', 'web/static/src/module_loader.js', 'artarad_web_persian_calendar/static/src/js/calendar/utils.js',),
            ('after', 'web/static/src/module_loader.js', 'artarad_web_persian_calendar/static/src/js/calendar/hooks.js',),

            # for calendar view
            ('after', 'web/static/src/views/*/**', 'artarad_web_persian_calendar/static/src/js/calendar/calendar_common_renderer.js',),
            ('after', 'web/static/src/views/*/**', 'artarad_web_persian_calendar/static/src/js/calendar/calendar_year_renderer.js',),
            ('after', 'web/static/src/views/*/**', 'artarad_web_persian_calendar/static/src/js/calendar/calendar_controller.js',),
        ],

        # for calendar view
        'web.jfullcalendar_lib' : [
            '/artarad_web_persian_calendar/static/src/js/calendar/jfullcalendar/core/index.global.js',
            '/artarad_web_persian_calendar/static/src/js/calendar/jfullcalendar/core/locales-all.global.js',
            '/artarad_web_persian_calendar/static/src/js/calendar/jfullcalendar/interaction/index.global.js',
            '/artarad_web_persian_calendar/static/src/js/calendar/jfullcalendar/daygrid/index.global.js',
            '/artarad_web_persian_calendar/static/src/js/calendar/jfullcalendar/luxon3/index.global.js',
            '/artarad_web_persian_calendar/static/src/js/calendar/jfullcalendar/timegrid/index.global.js',
            '/artarad_web_persian_calendar/static/src/js/calendar/jfullcalendar/list/index.global.js',
        ],

        # The gantt patches target APIs that were removed in Odoo 20
        # (gantt_helpers.getRangeFromDate, GanttRendererControls.dateDescription,
        # the SCALES/RANGES shape of GanttArchParser). They are kept in
        # static/src/js/gantt/ but unloaded until they are ported, so the gantt
        # view falls back to the gregorian calendar instead of crashing.
    },

    'installable': True,

    'auto_install': False,
}
