# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    modir_ai_base_url = fields.Char(
        string='AI API Base URL',
        config_parameter='modir_ai.base_url',
        help='OpenAI-compatible base URL, e.g. https://api.openai.com/v1',
    )
    modir_ai_api_key = fields.Char(
        string='AI API Key',
        config_parameter='modir_ai.api_key',
    )
    modir_ai_chat_model = fields.Char(
        string='Chat Model',
        config_parameter='modir_ai.chat_model',
        help='Model id for chat/completions, e.g. gpt-4o-mini',
    )
    modir_ai_embedding_model = fields.Char(
        string='Embedding Model',
        config_parameter='modir_ai.embedding_model',
        help='Must produce 1536-dimensional vectors (Odoo AI vector column size). '
             'Example: text-embedding-3-small',
    )
