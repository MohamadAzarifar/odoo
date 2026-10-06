def migrate(cr, version):
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.modir_website import hooks
    hooks.setup_website(env)
    cr.execute(
        """
        DELETE FROM ir_attachment
         WHERE name LIKE '%%assets_frontend%%'
            OR name LIKE '%%assets_backend%%'
            OR url LIKE '%%/web/assets/%%'
        """
    )
