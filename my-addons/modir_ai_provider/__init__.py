# -*- coding: utf-8 -*-
from . import models


def post_load():
    """Apply monkey-patches after the registry has imported Enterprise AI."""
    from . import patch
    patch.apply_patches()
