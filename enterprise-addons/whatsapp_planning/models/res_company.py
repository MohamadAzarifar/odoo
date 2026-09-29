from odoo import fields, models

WA_PLANNING_TEMPLATES = [
    "wa_template_schedule_published",
    "wa_template_open_shift_available",
    "wa_template_assigned_shift",
    "wa_template_shift_reassigned",
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    planning_medium = fields.Selection([('mail', 'Email'), ('whatsapp', 'WhatsApp')], string="Send Planning", default='mail')
    wa_template_schedule_published = fields.Many2one('whatsapp.template', string="Schedule Publishing Template", default=lambda self: self.env.ref('whatsapp_planning.whatsapp_template_planning_schedule_published', raise_if_not_found=False))
    wa_template_open_shift_available = fields.Many2one('whatsapp.template', string="Open Shift Template", default=lambda self: self.env.ref('whatsapp_planning.whatsapp_template_planning_open_shift_available', raise_if_not_found=False))
    wa_template_assigned_shift = fields.Many2one('whatsapp.template', string="Assigned Shift Template", default=lambda self: self.env.ref('whatsapp_planning.whatsapp_template_planning_assigned_shift', raise_if_not_found=False))
    wa_template_shift_reassigned = fields.Many2one('whatsapp.template', string="Shift Reassigned Template", default=lambda self: self.env.ref('whatsapp_planning.whatsapp_template_planning_shift_reassigned', raise_if_not_found=False))
