# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AlumniEventInviteWizard(models.TransientModel):
    _name = 'alumni.event.invite.wizard'
    _description = 'Alumni Event Invite Wizard'

    event_id = fields.Many2one('event.event', string='Event', required=True)
    is_alumni_event = fields.Boolean(string='Is Alumni Event', related='event_id.is_alumni_event')
    
    # Filter fields
    department_ids = fields.Many2many('hr.department', string='Departments')
    graduation_year_from = fields.Integer(string='Graduation Year From')
    graduation_year_to = fields.Integer(string='Graduation Year To')
    degree = fields.Char(string='Degree')
    country_ids = fields.Many2many('res.country', string='Countries')
    
    # Selected alumni
    selected_alumni_ids = fields.Many2many('alumni.profile', string='Selected Alumni')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_event_id'):
            res['event_id'] = self.env.context['default_event_id']
        if self.env.context.get('default_is_alumni_event'):
            res['is_alumni_event'] = self.env.context['default_is_alumni_event']
        return res
    
    def action_search_alumni(self):
        """Search alumni based on filters"""
        self.ensure_one()
        
        # Build domain
        domain = [('active', '=', True), ('portal_access_granted', '=', True)]
        
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        
        if self.graduation_year_from:
            domain.append(('graduation_year', '>=', self.graduation_year_from))
        
        if self.graduation_year_to:
            domain.append(('graduation_year', '<=', self.graduation_year_to))
        
        if self.degree:
            domain.append(('degree', 'ilike', self.degree))
        
        if self.country_ids:
            domain.append(('country_id', 'in', self.country_ids.ids))
        
        alumni = self.env['alumni.profile'].search(domain)
        
        self.selected_alumni_ids = [(6, 0, alumni.ids)]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Search Complete'),
                'message': _('Found %d alumni matching your criteria.') % len(alumni),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_send_invitations(self):
        """Send event invitations to selected alumni"""
        self.ensure_one()
        
        if not self.selected_alumni_ids:
            raise ValidationError(_("Please select alumni to invite."))
        
        if not self.event_id:
            raise ValidationError(_("Event is required."))
        
        template = self.env.ref('ust_alumni_management.email_template_event_invitation', False)
        if not template:
            raise ValidationError(_("Event invitation email template not found."))
        
        sent_count = 0
        for alumni in self.selected_alumni_ids:
            if alumni.email:
                try:
                    template.with_context(alumni_email=alumni.email).send_mail(
                        self.event_id.id, 
                        force_send=True
                    )
                    sent_count += 1
                except Exception as e:
                    pass  # Log error but continue
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invitations Sent'),
                'message': _('Event invitations sent to %d alumni.') % sent_count,
                'type': 'success',
                'sticky': False,
            }
        }
