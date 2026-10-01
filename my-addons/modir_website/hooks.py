# -*- coding: utf-8 -*-

FOOTER_FA = {
    'Useful Links': 'لینک‌های مفید',
    'About us': 'درباره ما',
    'Connect with us': 'تماس با ما',
    '>Home</': '>خانه</',
    '>Products</': '>محصولات</',
    '>Services</': '>خدمات</',
    '>Legal</': '>قانونی</',
    '>Contact us</': '>تماس با ما</',
    "We are a team of passionate people whose goal is to improve everyone's life through disruptive products. We build great products to solve your business problems.":
        'ما تیمی از افراد متخصص هستیم که هدفمان بهبود عملکرد سازمان‌ها از طریق سامانه‌ها و مشاوره مدیریتی است. محصولات و خدمات ما برای شرکت‌هایی طراحی شده‌اند که می‌خواهند فرآیندهای خود را بهینه کنند.',
    "We are a team of passionate people whose goal is to improve everyone\u2019s life through disruptive products. We build great products to solve your business problems.":
        'ما تیمی از افراد متخصص هستیم که هدفمان بهبود عملکرد سازمان‌ها از طریق سامانه‌ها و مشاوره مدیریتی است. محصولات و خدمات ما برای شرکت‌هایی طراحی شده‌اند که می‌خواهند فرآیندهای خود را بهینه کنند.',
    'Our products are designed for small to medium size companies willing to optimize their performance.':
        'تمرکز ما بر سازمان‌هایی است که می‌خواهند ERP، دانش، اسناد، فروش، پروژه و تولید را یکپارچه کنند.',
}

MENU_FA = {
    'Home': 'خانه',
    'About us': 'درباره ما',
    'Products': 'محصولات',
    'Services': 'خدمات',
    'Legal': 'قانونی',
    'Contact us': 'تماس با ما',
    'Contact Us': 'تماس با ما',
}

# Exact English → Persian replacements for homepage arch blobs
HOMEPAGE_FA = {
    'Enterprise systems,<br/>\n                            made clear.':
        'سامانه‌های سازمانی،<br/>\n                            شفاف و یکپارچه.',
    'Consultancy and products for ERP, knowledge, documents,\n                            customers, projects, products, and manufacturing —\n                            so your organization runs as one.':
        'مشاوره و محصولات برای ERP، مدیریت دانش، اسناد،\n                            مشتریان، پروژه‌ها، محصول و تولید —\n                            تا سازمان شما یکپارچه کار کند.',
    'Book a consultation': 'دریافت مشاوره',
    'Explore capabilities': 'مشاهده توانمندی‌ها',
    'What we do': 'آنچه انجام می‌دهیم',
    'Two ways we help enterprises move forward': 'دو مسیر برای پیشبرد سازمان‌ها',
    'Consultancy': 'مشاوره',
    'Discovery, process design, vendor selection, implementation\n                                    oversight, and change management for enterprise platforms.':
        'شناخت نیاز، طراحی فرآیند، انتخاب راهکار، نظارت بر پیاده‌سازی\n                                    و مدیریت تغییر برای سامانه‌های سازمانی.',
    'Products': 'محصولات',
    'Ready-to-extend modules and solutions across planning,\n                                    operations, collaboration, and manufacturing control.':
        'ماژول‌ها و راهکارهای قابل توسعه در برنامه‌ریزی،\n                                    عملیات، همکاری و کنترل تولید.',
    'Capabilities': 'توانمندی‌ها',
    'The systems that run modern enterprises': 'سامانه‌هایی که سازمان‌های مدرن را پیش می‌برند',
    'One partnership covering the stack your teams actually use.':
        'یک همکاری برای تمام سامانه‌هایی که تیم‌های شما واقعاً استفاده می‌کنند.',
    'Enterprise Resource Planning': 'برنامه‌ریزی منابع سازمانی',
    'Knowledge Management': 'مدیریت دانش',
    'Document Management': 'مدیریت اسناد',
    'Customer Relationship': 'مدیریت ارتباط با مشتری',
    'Project Management': 'مدیریت پروژه',
    'Product Lifecycle': 'چرخه عمر محصول',
    'Manufacturing Planning': 'برنامه‌ریزی تولید',
    'How we work': 'نحوه همکاری',
    'Simple process. Serious outcomes.': 'فرایند ساده. نتایج جدی.',
    'Listen &amp; map': 'شنیدن و نقشه‌برداری',
    'We learn your processes, constraints, and goals before recommending tools.':
        'پیش از پیشنهاد ابزار، فرآیندها، محدودیت‌ها و اهداف شما را می‌شناسیم.',
    'Design &amp; deliver': 'طراحی و اجرا',
    'Architecture, configuration, and products aligned to how your teams work.':
        'معماری، پیکربندی و محصولاتی هم‌راستا با شیوه کار تیم‌های شما.',
    'Adopt &amp; improve': 'به‌کارگیری و بهبود',
    'Training, handover, and continuous improvement after go-live.':
        'آموزش، تحویل و بهبود مستمر پس از راه‌اندازی.',
    'Ready to modernize how your enterprise runs?':
        'آماده مدرن‌سازی نحوه اداره سازمان خود هستید؟',
    'Tell us where you are today — we will help you choose the right path.':
        'وضعیت امروز خود را بگویید — مسیر درست را با هم انتخاب می‌کنیم.',
    'Talk to Modir.Digital': 'گفتگو با Modir.Digital',
    '<span class="modir-offer__index">01</span>': '<span class="modir-offer__index">۰۱</span>',
    '<span class="modir-offer__index">02</span>': '<span class="modir-offer__index">۰۲</span>',
}


def _activate_persian(env):
    fa = env.ref('base.lang_fa_IR', raise_if_not_found=False)
    en = env.ref('base.lang_en', raise_if_not_found=False)
    if fa and not fa.active:
        wizard = env['base.language.install'].create({
            'lang_ids': [(6, 0, [fa.id])],
            'overwrite': False,
        })
        wizard.lang_install()
        fa = env.ref('base.lang_fa_IR')
    return fa, en


def _reload_modir_translations(env):
    module = env['ir.module.module'].search([('name', '=', 'modir_website')], limit=1)
    if module:
        module._update_translations(['fa_IR'], overwrite=True)


def _drop_homepage_cow(env):
    """Remove website-specific copies of our inherit so module translations apply."""
    cows = env['ir.ui.view'].sudo().search([
        ('key', '=', 'modir_website.homepage'),
        ('website_id', '!=', False),
    ])
    if cows:
        cows.unlink()


def _apply_replacements(text, mapping):
    if not text:
        return text
    out = text
    # Longer keys first to avoid partial collisions
    for src, dst in sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True):
        out = out.replace(src, dst)
    return out


def _translate_views_by_key(env, key, mapping):
    import re
    env.cr.execute(
        "SELECT id, arch_db FROM ir_ui_view WHERE key = %s",
        (key,),
    )
    for view_id, arch_db in env.cr.fetchall():
        if not arch_db or 'en_US' not in arch_db:
            continue
        en = arch_db.get('en_US') or ''
        if not isinstance(en, str):
            continue
        # Always retranslate from English so stale FA copies are refreshed
        fa = _apply_replacements(en, mapping)
        if key == 'website.footer_custom':
            fa = re.sub(
                r"We are a team of passionate people whose goal is to improve everyone.s life through disruptive products\. We build great products to solve your business problems\.",
                "ما تیمی از افراد متخصص هستیم که هدفمان بهبود عملکرد سازمان‌ها از طریق سامانه‌ها و مشاوره مدیریتی است. محصولات و خدمات ما برای شرکت‌هایی طراحی شده‌اند که می‌خواهند فرآیندهای خود را بهینه کنند.",
                fa,
                count=1,
            )
        # Guard against corrupted literal \n sequences from bad writes
        if '\\n' in fa:
            fa = fa.replace('\\n', '\n')
        if arch_db.get('fa_IR') != fa:
            env.cr.execute(
                """
                UPDATE ir_ui_view
                   SET arch_db = jsonb_set(COALESCE(arch_db, '{}'::jsonb), '{fa_IR}', to_jsonb(%s::text))
                 WHERE id = %s
                """,
                (fa, view_id),
            )


def _translate_menus(env):
    import json
    env.cr.execute("SELECT id, name FROM website_menu")
    for menu_id, name in env.cr.fetchall():
        if not name or not isinstance(name, dict):
            continue
        en = name.get('en_US')
        if not en or en not in MENU_FA:
            continue
        if name.get('fa_IR') == MENU_FA[en]:
            continue
        name = dict(name)
        name['fa_IR'] = MENU_FA[en]
        env.cr.execute(
            "UPDATE website_menu SET name = %s::jsonb WHERE id = %s",
            (json.dumps(name, ensure_ascii=False), menu_id),
        )


# Website theme: Modir fonts + ink/teal palette (replaces Inter + purple)
MODIR_FONTS = {
    'font': "'Manrope'",
    'headings-font': "'Syne'",
    'navbar-font': "'Manrope'",
    'buttons-font': "'Manrope'",
    'google-fonts': "('Manrope', 'Syne', 'Vazirmatn')",
}
MODIR_PALETTE = {
    'o-color-1': '#2ec4b6',
    'o-color-2': '#0b1220',
    'o-color-3': '#d7e0ef',
    'o-color-4': '#f4f7fb',
    'o-color-5': '#121a2b',
    'menu': 2,
    'footer': 2,
    'copyright': 2,
}


def _apply_theme(env):
    """Set Modir fonts/colors as website theme defaults for every website."""
    Assets = env['website.assets'].sudo()
    websites = env['website'].sudo().search([])
    for website in websites:
        assets = Assets.with_context(website_id=website.id)
        assets.make_scss_customization(
            '/website/static/src/scss/options/user_values.scss',
            {
                **MODIR_FONTS,
                'color-palettes-name': "'user-palette'",
            },
        )
        assets.make_scss_customization(
            '/website/static/src/scss/options/colors/user_color_palette.scss',
            MODIR_PALETTE,
        )


def setup_website(env):
    """Brand the website, enable FA/EN, and apply Persian website content."""
    fa, en = _activate_persian(env)

    websites = env['website'].sudo().search([])
    for website in websites:
        vals = {'name': 'Modir.Digital'}
        lang_cmds = []
        if en:
            lang_cmds.append((4, en.id))
        if fa:
            lang_cmds.append((4, fa.id))
        if lang_cmds:
            vals['language_ids'] = lang_cmds
            if fa:
                vals['default_lang_id'] = fa.id
        website.write(vals)

    company = env.ref('base.main_company', raise_if_not_found=False)
    if company:
        company.write({
            'name': 'Modir.Digital',
            'email': company.email if company.email and 'example.com' not in (company.email or '') else 'info@modir.digital',
            'website': 'https://modir.digital',
            'primary_color': '#2ec4b6',
            'secondary_color': '#0b1220',
        })

    _apply_theme(env)
    _drop_homepage_cow(env)
    _reload_modir_translations(env)
    _translate_views_by_key(env, 'modir_website.homepage', HOMEPAGE_FA)
    _translate_views_by_key(env, 'website.footer_custom', FOOTER_FA)
    _translate_menus(env)


def teardown_website(env):
    return
