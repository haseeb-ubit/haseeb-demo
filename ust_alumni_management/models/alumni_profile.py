# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
from odoo.tools import email_normalize
import re
import logging

_logger = logging.getLogger(__name__)


class AlumniProfile(models.Model):
    _name = 'alumni.profile'
    _description = 'Alumni Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'name'

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
    
    # Academic Information
    last_university = fields.Char(string='Last University')
    university_duration = fields.Char(string='Duration of University', help='e.g. 2008 - 2014')
    department = fields.Char(string='Department')
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
    
    @api.constrains('email')
    def _check_unique_email(self):
        """Ensure email is unique across alumni profiles"""
        for record in self:
            if record.email:
                duplicate = self.search([
                    ('email', '=', record.email),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        _("An alumni profile with email '%s' already exists.", record.email)
                    )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate URL slug from name if not provided"""
        for vals in vals_list:
            if not vals.get('url_slug') and vals.get('name'):
                # Generate unique slug, checking against existing records
                vals['url_slug'] = self._generate_url_slug(
                    vals['name'], 
                    exclude_id=None,  # No ID yet during create
                    email=vals.get('email')
                )
            
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
            
        records = super().create(vals_list)

        # Auto-create portal user for each new alumni
        for record in records:
            if record.email:
                try:
                    record._auto_create_portal_user()
                except Exception as e:
                    _logger.warning(
                        "Failed to auto-create portal user for alumni '%s' (%s): %s",
                        record.name, record.email, str(e)
                    )

        return records

    def _auto_create_portal_user(self):
        """Auto-create portal user and send invitation for this alumni."""
        self.ensure_one()
        normalized_email = email_normalize(self.email)
        if not normalized_email:
            return

        # Check if user already exists for this partner
        existing_user = self.env['res.users'].sudo().search([
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)
        if existing_user:
            self.write({'user_id': existing_user.id, 'invitation_sent': True})
            return

        # Check if a user with the same login already exists
        existing_login = self.env['res.users'].sudo().search([
            ('login', '=', normalized_email)
        ], limit=1)
        if existing_login:
            self.write({'user_id': existing_login.id, 'invitation_sent': True})
            return

        # Create portal user using Odoo's template mechanism
        group_portal = self.env.ref('base.group_portal')
        group_public = self.env.ref('base.group_public')
        group_alumni = self.env.ref('ust_alumni_management.group_alumni_user')

        company = self.partner_id.company_id or self.env.company
        user = self.env['res.users'].with_context(
            no_reset_password=True
        ).sudo().with_company(company.id)._create_user_from_template({
            'email': normalized_email,
            'login': normalized_email,
            'partner_id': self.partner_id.id,
            'company_id': company.id,
            'company_ids': [(6, 0, company.ids)],
        })

        # Set proper groups: portal + alumni user, remove public
        user.write({
            'active': True,
            'group_ids': [
                (4, group_portal.id),
                (3, group_public.id),
                (4, group_alumni.id),
            ],
        })

        # Link user to alumni profile
        self.write({'user_id': user.id, 'invitation_sent': True})

        # Send password setup email (portal invitation)
        user.partner_id.signup_prepare()
        template = self.env.ref('auth_signup.portal_set_password_email', raise_if_not_found=False)
        if template:
            template.with_context(
                dbname=self._cr.dbname,
                lang=user.lang,
            ).send_mail(user.id, force_send=True)

        _logger.info(
            "Auto-created portal user for alumni '%s' (login: %s)",
            self.name, normalized_email
        )
    
    def write(self, vals):
        """Handle URL slug updates"""
        if 'name' in vals and 'url_slug' not in vals:
            for record in self:
                if not record.url_slug:
                    vals['url_slug'] = record._generate_url_slug(
                        vals['name'],
                        exclude_id=record.id,
                        email=vals.get('email') or record.email
                    )
        
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

        res = super().write(vals)

        # Auto-create portal user if email was added/updated and no user exists
        if 'email' in vals:
            for record in self:
                if record.email and not record.user_id and not record.invitation_sent:
                    try:
                        record._auto_create_portal_user()
                    except Exception as e:
                        _logger.warning("Failed to auto-create portal user for alumni '%s' upon update: %s",
                                        record.name, str(e))

        return res
    def _generate_url_slug(self, name, exclude_id=None, email=None):
        """Generate a URL-friendly slug from a name, ensuring uniqueness"""
        if not name:
            return ''
        
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure uniqueness - check for existing slugs
        base_slug = slug
        counter = 1
        while True:
            domain = [('url_slug', '=', slug)]
            if exclude_id:
                domain.append(('id', '!=', exclude_id))
            elif self.id:
                domain.append(('id', '!=', self.id))
            
            existing = self.search(domain, limit=1)
            if not existing:
                # Slug is unique, return it
                break
            
            # If email is available and different, try using email part
            if email and counter == 1:
                email_part = email.split('@')[0].lower()
                email_part = re.sub(r'[^\w\s-]', '', email_part)
                email_part = re.sub(r'[\s]+', '-', email_part)
                email_part = re.sub(r'-+', '-', email_part).strip('-')
                if email_part and email_part != slug:
                    slug = f"{base_slug}-{email_part}"
                    continue
            
            # Otherwise, append counter
            slug = f"{base_slug}-{counter}"
            counter += 1
            
            # Safety limit to prevent infinite loop
            if counter > 1000:
                # Fallback: use timestamp
                import time
                slug = f"{base_slug}-{int(time.time())}"
                break
        
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

               
    def get_base_url(self):
        """Get base URL for email templates"""
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
    

    
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
