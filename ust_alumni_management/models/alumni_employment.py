# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import secrets
import string


class AlumniEmployment(models.Model):
    _name = 'alumni.employment'
    _description = 'Alumni Employment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'start_date desc, id desc'

    alumni_id = fields.Many2one('alumni.profile', string='Alumni', required=True, ondelete='cascade')
    employment_type = fields.Selection([
        ('previous', 'Previous Employment'),
        ('current', 'Current Employment')
    ], string='Employment Type', required=True, default='previous')
    
    # Job Details
    job_title = fields.Char(string='Job Title', required=True)
    company_name = fields.Char(string='Company Name', required=True)
    company_website = fields.Char(string='Company Website')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date')
    end_date_display = fields.Char(string='End Date', compute='_compute_end_date_display')
    description = fields.Text(string='Job Description')
    
    @api.depends('end_date', 'employment_type')
    def _compute_end_date_display(self):
        for record in self:
            if record.employment_type == 'current':
                record.end_date_display = _('Present')
            elif record.end_date:
                # Format date as string according to user locale
                record.end_date_display = fields.Date.to_string(record.end_date)
            else:
                record.end_date_display = ''
    
    # Verification Details
    hr_email = fields.Char(string='HR Email')
    gm_email = fields.Char(string='GM/Manager Email')
    verification_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending_verification', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], string='Verification Status', default='draft', tracking=True)
    
    verification_token = fields.Char(string='Verification Token', copy=False, index=True, 
                                    help='Unique token for email verification link')
    
    verified_by = fields.Many2one('res.users', string='Verified By', readonly=True)
    verified_date = fields.Datetime(string='Verified Date', readonly=True)
    verification_notes = fields.Text(string='Verification Notes')
    
    # Display Name
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    @api.depends('job_title', 'company_name', 'alumni_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.job_title and record.company_name:
                record.display_name = f"{record.job_title} at {record.company_name}"
            elif record.job_title:
                record.display_name = record.job_title
            elif record.company_name:
                record.display_name = record.company_name
            else:
                record.display_name = f"Employment - {record.alumni_id.name or 'Unknown'}"
    
    @api.constrains('start_date', 'end_date', 'employment_type')
    def _check_dates(self):
        """Validate employment dates"""
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date < record.start_date:
                    raise ValidationError(_("End date cannot be before start date."))
            
            if record.employment_type == 'current' and record.end_date:
                raise ValidationError(_("Current employment should not have an end date."))
    
    @api.constrains('hr_email', 'gm_email')
    def _check_emails(self):
        """Validate email formats"""
        for record in self:
            if record.hr_email and '@' not in record.hr_email:
                raise ValidationError(_("Invalid HR email format."))
            if record.gm_email and '@' not in record.gm_email:
                raise ValidationError(_("Invalid GM email format."))
    
    def _generate_verification_token(self):
        """Generate a unique verification token"""
        token_length = 32
        characters = string.ascii_letters + string.digits
        while True:
            token = ''.join(secrets.choice(characters) for _ in range(token_length))
            # Ensure uniqueness
            existing = self.search([('verification_token', '=', token)], limit=1)
            if not existing:
                return token
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generate verification token if not provided"""
        for vals in vals_list:
            if not vals.get('verification_token'):
                record = self.new(vals)
                vals['verification_token'] = record._generate_verification_token()
        return super().create(vals_list)
    
    def get_base_url(self):
        """Get base URL for email templates"""
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
    
    def action_verify(self):
        """Admin action: Send verification email to HR/GR and set status to pending"""
        self.ensure_one()
        
        if not self.hr_email and not self.gm_email:
            raise ValidationError(_("At least one email (HR or GM/Manager) is required for verification."))
        
        # Generate token if not exists
        if not self.verification_token:
            self.verification_token = self._generate_verification_token()
        
        # Update status to pending verification
        self.verification_status = 'pending_verification'
        
        # Send verification emails to HR/GR
        template = self.env.ref('ust_alumni_management.email_template_employment_verification', False)
        if template:
            emails_sent = []
            if self.hr_email:
                template.send_mail(self.id, force_send=True, email_values={'email_to': self.hr_email})
                emails_sent.append(self.hr_email)
            if self.gm_email and self.gm_email != self.hr_email:
                template.send_mail(self.id, force_send=True, email_values={'email_to': self.gm_email})
                emails_sent.append(self.gm_email)
            
            return True
        
        return True
    
    def action_verify_via_link(self, token=None):
        """HR/GR confirms employment via the confirmation link in email"""
        self.ensure_one()
        
        if token and self.verification_token != token:
            raise ValidationError(_("Invalid verification token."))
        
        if self.verification_status == 'verified':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Already Verified'),
                    'message': _('This employment record is already verified.'),
                    'type': 'info',
                    'sticky': False,
                }
            }
        
        self.write({
            'verification_status': 'verified',
            'verified_by': self.env.user.id,
            'verified_date': fields.Datetime.now(),
        })
        
        # Send confirmation email to alumni
        template = self.env.ref('ust_alumni_management.email_template_employment_verified', False)
        if template:
            template.send_mail(self.id, force_send=True)
        
        return True
    
    def action_verify_manually(self):
        """Manually verify employment (admin action)"""
        self.ensure_one()
        self.write({
            'verification_status': 'verified',
            'verified_by': self.env.user.id,
            'verified_date': fields.Datetime.now(),
        })
        
        # Send confirmation email to alumni
        template = self.env.ref('ust_alumni_management.email_template_employment_verified', False)
        if template:
            template.send_mail(self.id, force_send=True)
        
        return True
    
    def action_reject(self):
        """Reject verification"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Verification'),
            'res_model': 'alumni.employment.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employment_id': self.id},
        }
    
    def action_reset_to_draft(self):
        """Reset to draft status"""
        self.ensure_one()
        self.write({
            'verification_status': 'draft',
            'verified_by': False,
            'verified_date': False,
            'verification_notes': False,
        })
