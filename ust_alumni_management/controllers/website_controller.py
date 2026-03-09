# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import MissingError
import json


class AlumniWebsiteController(http.Controller):

    @http.route(['/alumni-profiles', '/alumni-profiles/page/<int:page>'], type='http', auth="public", website=True)
    def alumni_directory(self, page=1, **kw):
        """Alumni directory listing page"""
        AlumniProfile = request.env['alumni.profile']
        
        # Get search parameters
        search = kw.get('search', '')
        department = kw.get('department', '')
        degree = kw.get('degree', '')
        country_id = kw.get('country_id', False)
        company_name = kw.get('company_name', '')
        
        # Build domain
        domain = [('active', '=', True)]
        
        if search:
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('email', 'ilike', search))
        
        if department:
            domain.append(('department', 'ilike', department))
        
        if degree:
            domain.append(('degree', 'ilike', degree))
        
        if country_id:
            domain.append(('country_id', '=', int(country_id)))
        
        # Company name filter — find alumni who work(ed) at the selected company
        if company_name:
            employment_records = request.env['alumni.employment'].sudo().search([
                ('company_name', 'ilike', company_name),
            ])
            alumni_ids = employment_records.mapped('alumni_id').ids
            domain.append(('id', 'in', alumni_ids))
        
        # Pagination
        per_page = 12
        total = AlumniProfile.sudo().search_count(domain)
        pager = request.website.pager(
            url='/alumni-profiles',
            total=total,
            page=page,
            step=per_page,
            url_args=kw
        )
        
        alumni = AlumniProfile.sudo().search(domain, limit=per_page, offset=(page - 1) * per_page, order='name')
        
        # Get filter options — departments are now free text, so get unique values
        dept_records = AlumniProfile.sudo().search_read([('department', '!=', False)], ['department'])
        unique_departments = sorted(set([d['department'] for d in dept_records if d['department']]))
        
        countries = request.env['res.country'].sudo().search([])
        degree_records = AlumniProfile.sudo().search_read([('degree', '!=', False)], ['degree'])
        unique_degrees = sorted(set([d['degree'] for d in degree_records if d['degree']]))
        
        # Get unique company names from employment records
        emp_records = request.env['alumni.employment'].sudo().search_read(
            [('company_name', '!=', False)], ['company_name']
        )
        unique_companies = sorted(set([e['company_name'] for e in emp_records if e['company_name']]))
        
        values = {
            'alumni': alumni,
            'pager': pager,
            'search': search,
            'department': department,
            'degree': degree,
            'country_id': int(country_id) if country_id else False,
            'company_name': company_name,
            'departments': unique_departments,
            'countries': countries,
            'degrees': unique_degrees,
            'companies': unique_companies,
            'page_name': 'alumni_directory',
        }
        
        return request.render('ust_alumni_management.website_alumni_directory', values)
    
    @http.route(['/alumni/<int:alumni_id>', '/alumni/<string:slug>'], type='http', auth="public", website=True)
    def alumni_profile_page(self, alumni_id=None, slug=None, **kw):
        """Individual alumni profile page"""
        AlumniProfile = request.env['alumni.profile']
        
        if slug:
            alumni = AlumniProfile.sudo().search([('url_slug', '=', slug), ('active', '=', True)], limit=1)
        elif alumni_id:
            alumni = AlumniProfile.sudo().browse(alumni_id)
            if not alumni.exists() or not alumni.active:
                raise MissingError("Alumni profile not found.")
        else:
            raise MissingError("Alumni profile not found.")
        
        if not alumni:
            raise MissingError("Alumni profile not found.")
        
        # Get verified achievements
        achievements = alumni.achievement_ids.filtered(lambda a: a.is_verified)
        
        # Get verified current employment
        current_employment = alumni.current_employment_id
        
        # Get all verified employment history
        employments = alumni.employment_ids.filtered(lambda e: e.verification_status == 'verified')
        
        values = {
            'alumni': alumni,
            'achievements': achievements,
            'current_employment': current_employment,
            'employments': employments,
            'page_name': 'alumni_profile',
        }
        
        return request.render('ust_alumni_management.website_alumni_profile', values)
    
    @http.route(['/alumni/search'], type='json', auth="public", website=True, methods=['POST'], csrf=False)
    def alumni_search(self, **kw):
        """AJAX search endpoint for alumni"""
        AlumniProfile = request.env['alumni.profile']
        
        search_term = kw.get('search', '')
        filters = kw.get('filters', {})
        
        # Build domain
        domain = [('active', '=', True)]
        
        if search_term:
            domain.append('|')
            domain.append(('name', 'ilike', search_term))
            domain.append(('email', 'ilike', search_term))
        
        if filters.get('department'):
            domain.append(('department', 'ilike', filters['department']))
        
        if filters.get('degree'):
            domain.append(('degree', 'ilike', filters['degree']))
        
        if filters.get('country_id'):
            domain.append(('country_id', '=', int(filters['country_id'])))
        
        if filters.get('company_name'):
            employment_records = request.env['alumni.employment'].sudo().search([
                ('company_name', 'ilike', filters['company_name']),
            ])
            alumni_ids = employment_records.mapped('alumni_id').ids
            domain.append(('id', 'in', alumni_ids))
        
        alumni = AlumniProfile.sudo().search(domain, limit=50, order='name')
        
        results = []
        for alum in alumni:
            results.append({
                'id': alum.id,
                'name': alum.name,
                'email': alum.email,
                'department': alum.department or '',
                'last_university': alum.last_university or '',
                'degree': alum.degree or '',
                'photo': f'/web/image/alumni.profile/{alum.id}/photo' if alum.photo else False,
                'url': f'/alumni/{alum.url_slug or alum.id}',
                'current_job': alum.current_employment_id.job_title if alum.current_employment_id else '',
                'current_company': alum.current_employment_id.company_name if alum.current_employment_id else '',
            })
        
        return {'results': results, 'count': len(results)}
