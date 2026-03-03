# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    alumni_profile_id = fields.Many2one('alumni.profile', string='Alumni Profile', ondelete='set null')
    
    @api.model_create_multi
    def create(self, vals_list):
        """Link to alumni profile if user is alumni"""
        records = super().create(vals_list)
        
        for record in records:
            # Try to find alumni profile by partner or email
            if record.partner_id:
                alumni = self.env['alumni.profile'].search([
                    ('partner_id', '=', record.partner_id.id)
                ], limit=1)
                if alumni:
                    record.alumni_profile_id = alumni.id
            
        return records
