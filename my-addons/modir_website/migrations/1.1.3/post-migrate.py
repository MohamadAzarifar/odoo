def migrate(cr, version):
    # Assets-only bump: clear frontend bundles so RTL override CSS is rebuilt.
    cr.execute(
        """
        DELETE FROM ir_attachment
         WHERE name LIKE '%%assets_frontend%%'
            OR url LIKE '%%/web/assets/%%'
        """
    )
