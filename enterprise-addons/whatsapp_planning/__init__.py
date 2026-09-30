from . import models
from . import wizard


def _post_init_hook(env):
    env['res.company'].search([]).write({
        'wa_template_schedule_published': env.ref('whatsapp_planning.whatsapp_template_planning_schedule_published').id,
        'wa_template_open_shift_available': env.ref('whatsapp_planning.whatsapp_template_planning_open_shift_available').id,
        'wa_template_assigned_shift': env.ref('whatsapp_planning.whatsapp_template_planning_assigned_shift').id,
        'wa_template_shift_reassigned': env.ref('whatsapp_planning.whatsapp_template_planning_shift_reassigned').id
    })
