# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EventEvent(models.Model):
    _inherit = 'event.event'

    is_alumni_event = fields.Boolean(string='Alumni Event', default=False)
    alumni_filters = fields.Text(string='Alumni Filters (JSON)', 
                                help='JSON filters for alumni selection')
    
    alumni_registration_count = fields.Integer(string='Alumni Registrations', 
                                              compute='_compute_alumni_registration_count', store=False)
    
    def _compute_alumni_registration_count(self):
        """Count alumni registrations"""
        for record in self:
            record.alumni_registration_count = len(record.registration_ids.filtered('alumni_profile_id'))
    
    def action_view_alumni_registrations(self):
        """View alumni registrations for this event"""
        self.ensure_one()
        return {
            'name': _('Alumni Registrations'),
            'type': 'ir.actions.act_window',
            'res_model': 'event.registration',
            'view_mode': 'list,form',
            'domain': [('event_id', '=', self.id), ('alumni_profile_id', '!=', False)],
            'context': {'default_event_id': self.id},
        }
    
    def action_invite_alumni(self):
        """Open wizard to filter and invite alumni"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invite Alumni'),
            'res_model': 'alumni.event.invite.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_event_id': self.id,
                'default_is_alumni_event': self.is_alumni_event,
            },
        }
