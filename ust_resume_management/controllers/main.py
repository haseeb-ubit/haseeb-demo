# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
import urllib.parse
import re


class USTResumeController(http.Controller):

    @http.route(['/my/resume/<int:user_id>'], type='http', auth="user", website=True)
    def portal_edit_resume(self, user_id, **kw):
        user = request.env['res.users'].sudo().browse(user_id)
        if user.partner_id and user.id == request.uid or request.env.user.has_group('base.group_system'):
            resume = request.env['ust.resume'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not resume:
                resume = request.env['ust.resume'].sudo().create(
                    {'user_id': user.id, 'name': user.partner_id.name or user.login, 'email': user.login})
            return request.render('ust_resume_management.portal_resume_form', {'resume': resume})
        return request.redirect('/')

    def _get_resume_record(self, resume_id, is_english=False):
        model = 'ust.resume.en' if is_english else 'ust.resume'
        try:
            resume_sudo = request.env[model].sudo().browse(resume_id)
            if not resume_sudo.exists():
                return None
        except (AccessError, MissingError):
            return None

        user = request.env.user
        if resume_sudo.website_published:
            return resume_sudo

        if not user._is_public() and (user == resume_sudo.user_id or user.has_group('base.group_system')):
            return resume_sudo

        return None

    def _redirect_to_login(self):
        redirect_url = request.httprequest.url
        login_url = f"/web/login?redirect={urllib.parse.quote(redirect_url)}"
        return request.redirect(login_url)

    @http.route(['/report/pdf/ust_resume_management.ust_resume_report/<int:resume_id>'], type='http', auth="public",
                website=True)
    def resume_report_pdf(self, resume_id, **kw):
        """Override the standard resume report route (Arabic)"""
        resume = self._get_resume_record(resume_id, is_english=False)
        if not resume:
            if request.env.user._is_public():
                return self._redirect_to_login()
            return request.redirect('/')

        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', resume.user_id.name or '')
        pdf_filename = f"Resume-{sanitized_name}.pdf"
        encoded_filename = urllib.parse.quote(pdf_filename, safe='')

        return request.redirect(f'/resume_pdf/{resume_id}/ar/{encoded_filename}')

    @http.route(['/report/pdf/ust_resume_management.ust_resume_report_en/<int:resume_id>'], type='http', auth="public",
                website=True)
    def resume_report_pdf_en(self, resume_id, **kw):
        """Override the standard English resume report route"""
        resume = self._get_resume_record(resume_id, is_english=True)
        if not resume:
            if request.env.user._is_public():
                return self._redirect_to_login()
            return request.redirect('/')

        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', resume.user_id.name or '')
        pdf_filename = f"Resume-{sanitized_name}.pdf"
        encoded_filename = urllib.parse.quote(pdf_filename, safe='')

        return request.redirect(f'/resume_pdf/{resume_id}/en/{encoded_filename}')

    @http.route(['/resume_pdf/<int:resume_id>/<string:lang>/<path:filename>'], type='http', auth="public", website=True)
    def resume_pdf_named(self, resume_id, lang, filename, **kw):
        """Serve PDF with custom filename - handles both Arabic and English"""
        is_english = (lang == 'en')
        report_ref = 'ust_resume_management.ust_resume_report_en' if is_english else 'ust_resume_management.ust_resume_report'
        template_ref = 'ust_resume_management.ust_resume_report_template_en' if is_english else 'ust_resume_management.ust_resume_report_template'

        resume = self._get_resume_record(resume_id, is_english=is_english)
        if not resume:
            if request.env.user._is_public():
                return self._redirect_to_login()
            return request.redirect('/')

        report = request.env.ref(report_ref)
        pdf_content, _ = report.sudo()._render_qweb_pdf(template_ref, [resume_id])

        decoded_filename = urllib.parse.unquote(filename)

        response = request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{decoded_filename}"')
            ]
        )

        return response
