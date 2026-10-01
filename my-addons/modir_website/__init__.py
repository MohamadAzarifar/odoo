from . import hooks


def post_init_hook(env):
    hooks.setup_website(env)


def uninstall_hook(env):
    hooks.teardown_website(env)
