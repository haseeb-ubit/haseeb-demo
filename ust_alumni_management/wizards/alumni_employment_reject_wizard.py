# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AlumniEmploymentRejectWizard(models.TransientModel):
    _name = 'alumni.employment.reject.wizard'
    _description = 'Alumni Employment Reject Wizard'

    employment_id = fields.Many2one('alumni.employment', string='Employment Record', required=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_employment_id'):
            res['employment_id'] = self.env.context['default_employment_id']
        return res
    
    def action_reject(self):
        """Reject employment verification"""
        self.ensure_one()
        self.employment_id.write({
            'verification_status': 'rejected',
            'verification_notes': self.rejection_reason,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Rejected'),
                'message': _('Employment record rejected.'),
                'type': 'info',
                'sticky': False,
            }
        }
