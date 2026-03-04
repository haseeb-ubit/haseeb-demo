# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError


class AlumniPortalController(http.Controller):

    @http.route(['/my/alumni/profile'], type='http', auth="user", website=True)
    def portal_alumni_profile(self, **kw):
        """Main portal page for alumni"""
        user = request.env.user
        alumni = request.env['alumni.profile'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)
        
        if not alumni:
            # Try to find by partner
            if user.partner_id:
                alumni = request.env['alumni.profile'].sudo().search([
                    ('partner_id', '=', user.partner_id.id)
                ], limit=1)
        
        if not alumni:
            return request.redirect('/my')
        
        values = {
            'alumni': alumni,
            'page_name': 'alumni_profile',
        }
        return request.render('ust_alumni_management.portal_alumni_profile', values)
    
    @http.route(['/my/alumni/employment/<int:employment_id>/verify/<token>'], 
                type='http', auth="public", website=True, csrf=False)
    def portal_verify_employment(self, employment_id, token, **kw):
        """Verify employment via confirmation link"""
        employment = request.env['alumni.employment'].sudo().browse(employment_id)
        
        if not employment.exists():
            return request.render('ust_alumni_management.portal_verification_error', {
                'error': 'Employment record not found.'
            })
        
        if employment.verification_token != token:
            return request.render('ust_alumni_management.portal_verification_error', {
                'error': 'Invalid verification token.'
            })
        
        try:
            employment.action_verify_via_link(token)
            return request.render('ust_alumni_management.portal_verification_success', {
                'employment': employment,
            })
        except Exception as e:
            return request.render('ust_alumni_management.portal_verification_error', {
                'error': str(e)
            })
    
    @http.route(['/my/alumni/employment/<int:employment_id>/verify'], 
                type='http', auth="user", website=True)
    def portal_verify_employment_form(self, employment_id, **kw):
        """Verification form (for logged-in users)"""
        user = request.env.user
        employment = request.env['alumni.employment'].sudo().browse(employment_id)
        
        if not employment.exists():
            return request.redirect('/my/alumni/profile')
        
        # Check if user owns this employment record
        if employment.alumni_id.user_id != user:
            raise AccessError("You don't have access to this employment record.")
        
        values = {
            'employment': employment,
            'page_name': 'verify_employment',
        }
        return request.render('ust_alumni_management.portal_verify_employment_form', values)
    
    @http.route(['/my/alumni/profile/update'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_update_profile(self, **kw):
        """Update alumni profile from portal"""
        user = request.env.user
        alumni = request.env['alumni.profile'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)
        
        if not alumni:
            if user.partner_id:
                alumni = request.env['alumni.profile'].sudo().search([
                    ('partner_id', '=', user.partner_id.id)
                ], limit=1)
        
        if not alumni:
            return request.redirect('/my')
        
        section = kw.get('section', 'general')
        
        if section == 'general':
            # Update personal information (academic fields are read-only)
            vals = {
                'name': kw.get('name'),
                'email': kw.get('email'),
                'phone': kw.get('phone'),
                'mobile': kw.get('mobile'),
                'date_of_birth': kw.get('date_of_birth') or False,
                'linkedin': kw.get('linkedin'),
                'website': kw.get('website'),
                'street': kw.get('street'),
                'street2': kw.get('street2'),
                'city': kw.get('city'),
                'zip': kw.get('zip'),
            }
            
            if kw.get('nationality_id'):
                vals['nationality'] = int(kw.get('nationality_id'))
            if kw.get('state_id'):
                vals['state_id'] = int(kw.get('state_id'))
            if kw.get('country_id'):
                vals['country_id'] = int(kw.get('country_id'))
            
            # Handle photo upload
            if 'photo' in request.httprequest.files:
                photo_file = request.httprequest.files['photo']
                if photo_file:
                    photo_data = photo_file.read()
                    vals['photo'] = base64.b64encode(photo_data)
            
            # Remove empty values
            vals = {k: v for k, v in vals.items() if v}
            alumni.write(vals)
        
        return request.redirect('/my/alumni/profile')
    
    @http.route(['/my/alumni/employment/add'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_add_employment(self, **kw):
        """Add new employment from portal"""
        user = request.env.user
        alumni = request.env['alumni.profile'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not alumni and user.partner_id:
            alumni = request.env['alumni.profile'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
            
        if not alumni:
            return request.redirect('/my')
            
        vals = {
            'alumni_id': alumni.id,
            'job_title': kw.get('job_title'),
            'company_name': kw.get('company_name'),
            'company_website': kw.get('company_website'),
            'start_date': kw.get('start_date'),
            'end_date': kw.get('end_date') or False,
            'employment_type': 'current' if not kw.get('end_date') else 'previous',
            'hr_email': kw.get('hr_email'),
            'gm_email': kw.get('gm_email'),
            'description': kw.get('description'),
            'verification_status': 'draft',
        }
        
        request.env['alumni.employment'].sudo().create(vals)
        return request.redirect('/my/alumni/profile?tab=employment')

    @http.route(['/my/alumni/achievement/add'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_add_achievement(self, **kw):
        """Add new achievement from portal"""
        user = request.env.user
        alumni = request.env['alumni.profile'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not alumni and user.partner_id:
            alumni = request.env['alumni.profile'].sudo().search([('partner_id', '=', user.partner_id.id)], limit=1)
            
        if not alumni:
            return request.redirect('/my')
            
        vals = {
            'alumni_id': alumni.id,
            'title': kw.get('title'),
            'achievement_type': kw.get('achievement_type'),
            'date_achieved': kw.get('date_achieved'),
            'issuer_organization': kw.get('issuer_organization'),
            'description': kw.get('description'),
            'certificate_url': kw.get('certificate_url'),
            'is_verified': False,
        }
        
        if 'certificate_file' in request.httprequest.files:
            cert_file = request.httprequest.files['certificate_file']
            if cert_file:
                vals['supporting_document'] = base64.b64encode(cert_file.read())
                vals['supporting_document_filename'] = cert_file.filename
                
        request.env['alumni.achievement'].sudo().create(vals)
        return request.redirect('/my/alumni/profile?tab=achievements')

    @http.route(['/my/alumni/employment/<int:employment_id>/update'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_update_employment(self, employment_id, **kw):
        """Update existing employment from portal (only draft/pending)"""
        user = request.env.user
        employment = request.env['alumni.employment'].sudo().browse(employment_id)
        
        if not employment.exists():
            return request.redirect('/my/alumni/profile?tab=employment')
        
        # Verify ownership
        alumni = employment.alumni_id
        if alumni.user_id != user and alumni.partner_id != user.partner_id:
            return request.redirect('/my/alumni/profile#employment')
        
        # Only allow editing draft or pending records
        if employment.verification_status not in ('draft', 'pending_verification'):
            return request.redirect('/my/alumni/profile#employment')
        
        vals = {
            'job_title': kw.get('job_title'),
            'company_name': kw.get('company_name'),
            'company_website': kw.get('company_website'),
            'start_date': kw.get('start_date'),
            'end_date': kw.get('end_date') or False,
            'employment_type': 'current' if not kw.get('end_date') else 'previous',
            'hr_email': kw.get('hr_email'),
            'gm_email': kw.get('gm_email'),
            'description': kw.get('description'),
        }
        
        # Remove empty values but keep False for end_date
        vals = {k: v for k, v in vals.items() if v or k == 'end_date'}
        employment.write(vals)
        return request.redirect('/my/alumni/profile?tab=employment')

    @http.route(['/my/alumni/achievement/<int:achievement_id>/update'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_update_achievement(self, achievement_id, **kw):
        """Update existing achievement from portal (only unverified)"""
        user = request.env.user
        achievement = request.env['alumni.achievement'].sudo().browse(achievement_id)
        
        if not achievement.exists():
            return request.redirect('/my/alumni/profile?tab=achievements')
        
        # Verify ownership
        alumni = achievement.alumni_id
        if alumni.user_id != user and alumni.partner_id != user.partner_id:
            return request.redirect('/my/alumni/profile?tab=achievements')
        
        # Only allow editing unverified records
        if achievement.is_verified:
            return request.redirect('/my/alumni/profile?tab=achievements')
        
        vals = {
            'title': kw.get('title'),
            'achievement_type': kw.get('achievement_type'),
            'date_achieved': kw.get('date_achieved') or False,
            'issuer_organization': kw.get('issuer_organization'),
            'description': kw.get('description'),
            'certificate_url': kw.get('certificate_url'),
        }


        if 'certificate_file' in request.httprequest.files:
            cert_file = request.httprequest.files['certificate_file']
            if cert_file and cert_file.filename:
                vals['supporting_document'] = base64.b64encode(cert_file.read())
                vals['supporting_document_filename'] = cert_file.filename
        
        # Remove empty values but keep False for date_achieved
        vals = {k: v for k, v in vals.items() if v or k == 'date_achieved'}
        achievement.write(vals)
        return request.redirect('/my/alumni/profile?tab=achievements')

