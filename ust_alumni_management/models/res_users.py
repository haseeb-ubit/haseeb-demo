# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    alumni_profile_id = fields.Many2one('alumni.profile', string='Alumni Profile', compute='_compute_alumni_profile', store=False)
    
    def _compute_alumni_profile(self):
        """Find alumni profile for this user"""
        for user in self:
            if user.partner_id:
                alumni = self.env['alumni.profile'].search([
                    ('partner_id', '=', user.partner_id.id)
                ], limit=1)
                user.alumni_profile_id = alumni.id if alumni else False
            else:
                user.alumni_profile_id = False
