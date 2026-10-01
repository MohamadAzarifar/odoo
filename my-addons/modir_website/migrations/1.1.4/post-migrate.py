def migrate(cr, version):
    cr.execute(
        """
        DELETE FROM ir_attachment
         WHERE name LIKE '%%assets_frontend%%'
            OR url LIKE '%%/web/assets/%%'
        """
    )
