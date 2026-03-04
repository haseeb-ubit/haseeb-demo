# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AlumniAchievement(models.Model):
    _name = 'alumni.achievement'
    _description = 'Alumni Achievement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'title'
    _order = 'date_achieved desc, id desc'

    alumni_id = fields.Many2one('alumni.profile', string='Alumni', required=True, ondelete='cascade')
    achievement_type = fields.Selection([
        ('award', 'Award'),
        ('promotion', 'Promotion'),
        ('publication', 'Publication'),
        ('research', 'Research'),
        ('community_work', 'Community Work'),
        ('other', 'Other')
    ], string='Achievement Type', required=True, default='award')
    
    title = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    date_achieved = fields.Date(string='Date Achieved', required=True, default=fields.Date.today)
    issuer_organization = fields.Char(string='Issuer Organization')
    supporting_document = fields.Binary(string='Supporting Document')
    supporting_document_filename = fields.Char(string='Document Filename')
    
    # Verification
    is_verified = fields.Boolean(string='Verified', default=False, tracking=True)
    verified_by = fields.Many2one('res.users', string='Verified By', readonly=True)
    verified_date = fields.Datetime(string='Verified Date', readonly=True)
    verification_notes = fields.Text(string='Verification Notes')
    
    # Website Publishing
    published_date = fields.Datetime(string='Published Date', readonly=True)
    
    @api.constrains('date_achieved')
    def _check_date_achieved(self):
        """Validate achievement date"""
        for record in self:
            if record.date_achieved:
                if record.date_achieved > fields.Date.today():
                    raise ValidationError(_("Achievement date cannot be in the future."))
    
    def action_verify(self):
        """Verify achievement and auto-publish on website"""
        self.ensure_one()
        self.write({
            'is_verified': True,
            'verified_by': self.env.user.id,
            'verified_date': fields.Datetime.now(),
            'published_date': fields.Datetime.now(),
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Verified & Published'),
                'message': _('Achievement verified and published on website.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_unverify(self):
        """Unverify achievement and unpublish from website"""
        self.ensure_one()
        self.write({
            'is_verified': False,
            'verified_by': False,
            'verified_date': False,
            'published_date': False,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Unverified'),
                'message': _('Achievement unverified.'),
                'type': 'info',
                'sticky': False,
            }
        }
    

