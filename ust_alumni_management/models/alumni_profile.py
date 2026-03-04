# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
import re


class AlumniProfile(models.Model):
    _name = 'alumni.profile'
    _description = 'Alumni Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'graduation_year desc, name'

    # Partner and User Links
    partner_id = fields.Many2one('res.partner', string='Contact', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Portal User', ondelete='set null')
    
    # Personal Information
    name = fields.Char(string='Full Name', required=True, related='partner_id.name', store=True, readonly=False)
    email = fields.Char(string='Email', related='partner_id.email', store=True, readonly=False)
    phone = fields.Char(string='Phone', related='partner_id.phone', store=True, readonly=False)
    mobile = fields.Char(string='Mobile')
    street = fields.Char(string='Street', related='partner_id.street', store=True, readonly=False)
    street2 = fields.Char(string='Street2', related='partner_id.street2', store=True, readonly=False)
    city = fields.Char(string='City', related='partner_id.city', store=True, readonly=False)
    state_id = fields.Many2one('res.country.state', string='State', related='partner_id.state_id', store=True, readonly=False)
    zip = fields.Char(string='ZIP', related='partner_id.zip', store=True, readonly=False)
    country_id = fields.Many2one('res.country', string='Country', related='partner_id.country_id', store=True, readonly=False)
    photo = fields.Image(string='Photo', max_width=1024, max_height=1024)
    date_of_birth = fields.Date(string='Date of Birth')
    nationality = fields.Many2one('res.country', string='Nationality')
    
    # Academic Information (Read-only in portal)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    college_id = fields.Many2one('elearning.college', string='College')
    graduation_year = fields.Date(string='Graduation Year', required=True)
    degree = fields.Char(string='Degree')
    major = fields.Char(string='Major')

    # Contact Information
    linkedin = fields.Char(string='LinkedIn Profile')
    website = fields.Char(string='Portfolio Website')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    invitation_sent = fields.Boolean(string='Invitation Sent', default=False)
    url_slug = fields.Char(string='URL Slug', copy=False, index=True, help='URL-friendly identifier for website')
    user_state = fields.Selection(string='User Status', related='user_id.state', store=False)
    
    # Related Records
    employment_ids = fields.One2many('alumni.employment', 'alumni_id', string='Employment History')
    achievement_ids = fields.One2many('alumni.achievement', 'alumni_id', string='Achievements')
    
    # Computed Fields
    current_employment_id = fields.Many2one('alumni.employment', string='Current Employment', 
                                           compute='_compute_current_employment', 
                                           search='_search_current_employment', store=False)
    verified_achievements_count = fields.Integer(string='Verified Achievements', 
                                                compute='_compute_achievements_count', store=False)
    published_achievements_count = fields.Integer(string='Published Achievements', 
                                                  compute='_compute_achievements_count', store=False)
    
    @api.onchange('college_id')
    def _onchange_college_id(self):
        if self.college_id and self.department_id and self.department_id.college_id != self.college_id:
            self.department_id = False

    @api.depends('employment_ids', 'employment_ids.employment_type')
    def _compute_current_employment(self):
        for record in self:
            current = record.employment_ids.filtered(lambda e: e.employment_type == 'current' and e.verification_status == 'verified')
            record.current_employment_id = current[0] if current else False
            
    def _search_current_employment(self, operator, value):
        if operator in ('ilike', 'not ilike', 'like', 'not like', '=like', '=ilike'):
            # Search for alumni with current/verified employment matching the query
            employment_records = self.env['alumni.employment'].search([
                ('employment_type', '=', 'current'),
                ('verification_status', '=', 'verified'),
                '|', ('job_title', operator, value), ('company_name', operator, value)
            ])
            alumni_ids = employment_records.mapped('alumni_id').ids
            return [('id', 'in', alumni_ids)]
        
        if operator == '!=' and not value:
            # != False means has a current employment
            employment_records = self.env['alumni.employment'].search([
                ('employment_type', '=', 'current'),
                ('verification_status', '=', 'verified')
            ])
            alumni_ids = employment_records.mapped('alumni_id').ids
            return [('id', 'in', alumni_ids)]
        
        if operator == '=' and not value:
            # = False means has no current employment
            employment_records = self.env['alumni.employment'].search([
                ('employment_type', '=', 'current'),
                ('verification_status', '=', 'verified')
            ])
            alumni_ids = employment_records.mapped('alumni_id').ids
            return [('id', 'not in', alumni_ids)]
        
        # Fallback
        return []
    
    @api.depends('achievement_ids', 'achievement_ids.is_verified')
    def _compute_achievements_count(self):
        for record in self:
            record.verified_achievements_count = len(record.achievement_ids.filtered('is_verified'))
            record.published_achievements_count = record.verified_achievements_count
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate URL slug from name if not provided"""
        for vals in vals_list:
            if not vals.get('url_slug') and vals.get('name'):
                vals['url_slug'] = self._generate_url_slug(vals['name'])
            
            # Create partner if not provided
            if not vals.get('partner_id'):
                partner_vals = {
                    'name': vals.get('name', 'New Alumni'),
                    'email': vals.get('email', False),
                    'phone': vals.get('phone', False),
                    'is_company': False,
                }
                # Only add mobile if the field exists on res.partner
                if 'mobile' in self.env['res.partner']._fields:
                    partner_vals['mobile'] = vals.get('mobile', False)
                partner = self.env['res.partner'].create(partner_vals)
                vals['partner_id'] = partner.id
            
        return super().create(vals_list)
    
    def write(self, vals):
        """Handle URL slug updates"""
        if 'name' in vals and 'url_slug' not in vals:
            for record in self:
                if not record.url_slug:
                    vals['url_slug'] = self._generate_url_slug(vals['name'])
        
        # Update partner if name/email/mobile changed
        if 'name' in vals or 'email' in vals or 'mobile' in vals:
            for record in self:
                partner_vals = {}
                if 'name' in vals:
                    partner_vals['name'] = vals['name']
                if 'email' in vals:
                    partner_vals['email'] = vals['email']
                if 'mobile' in vals and 'mobile' in self.env['res.partner']._fields:
                    partner_vals['mobile'] = vals['mobile']
                if partner_vals:
                    record.partner_id.write(partner_vals)
        
        return super().write(vals)
    
    def _generate_url_slug(self, name):
        """Generate a URL-friendly slug from a name"""
        if not name:
            return ''
        
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure uniqueness
        if self.id:
            existing = self.search([
                ('url_slug', '=', slug),
                ('id', '!=', self.id)
            ], limit=1)
            if existing:
                slug = f"{slug}-{self.id}"
        
        return slug
    
    @api.constrains('url_slug')
    def _check_url_slug(self):
        """Validate URL slug format"""
        for record in self:
            if record.url_slug:
                if not re.match(r'^[a-z0-9-]+$', record.url_slug):
                    raise ValidationError(_("URL slug can only contain lowercase letters, numbers, and hyphens."))
                
                duplicate = self.search([
                    ('url_slug', '=', record.url_slug),
                    ('id', '!=', record.id)
                ], limit=1)
                
                if duplicate:
                    raise ValidationError(_("URL slug '%s' is already used. Please choose a different slug.") % record.url_slug)
    
    @api.constrains('graduation_year')
    def _check_graduation_year(self):
        """Validate graduation year"""
        current_year = fields.Date.today().year
        for record in self:
            if record.graduation_year:
                if record.graduation_year.year < 1900 or record.graduation_year.year > current_year + 5:
                    raise ValidationError(_("Graduation year must be between 1900 and %s.") % (current_year + 5))
    
    def get_base_url(self):
        """Get base URL for email templates"""
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
    
    def action_send_portal_invitation(self):
        """Send portal invitation email to alumni"""
        self.ensure_one()
        if not self.email:
            raise ValidationError(_("Email is required to send portal invitation."))
        
        template = self.env.ref('ust_alumni_management.email_template_portal_invitation', False)
        if template:
            template.send_mail(self.id, force_send=True)
            self.invitation_sent = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Portal invitation sent successfully.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        return False
    
    
    def action_view_employment(self):
        """Open employment records for this alumni"""
        self.ensure_one()
        return {
            'name': _('Employment History'),
            'type': 'ir.actions.act_window',
            'res_model': 'alumni.employment',
            'view_mode': 'list,form',
            'domain': [('alumni_id', '=', self.id)],
            'context': {'default_alumni_id': self.id},
        }
    
    def action_view_achievements(self):
        """Open achievements for this alumni"""
        self.ensure_one()
        return {
            'name': _('Achievements'),
            'type': 'ir.actions.act_window',
            'res_model': 'alumni.achievement',
            'view_mode': 'list,form',
            'domain': [('alumni_id', '=', self.id)],
            'context': {'default_alumni_id': self.id},
        }
