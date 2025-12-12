from odoo import http
from odoo.http import request

class AdmissionController(http.Controller):
    @http.route('/international-programs-admission-and-registration', type='http', auth='public', website=True)
    def programmes_page(self):
        return request.render('ust_website_programmes.admission_template', {})

class AcademicProgramsController(http.Controller):
        @http.route('/bachelor-programs', type='http', auth='public', website=True)
        def programmes_page(self):
            return request.render('ust_website_programmes.academic_programs_template', {})


class AppliedCollegeController(http.Controller):
    @http.route('/ords/erpedu/r/portal/login?session=5104593528794', type='http', auth='public', website=True)
    def programmes_page(self):
        return request.render('ust_website_programmes.applied_college_template', {})

class PostgraduateAdmission(http.Controller):
    @http.route('/programmes/postgraduate/admission', type='http', auth='public', website=True)
    def programmes_page(self):
        return request.render('ust_website_programmes.postgraduate_admission_template', {})

class PostgraduateAcademicPrograms(http.Controller):
    @http.route('/programmes/postgraduate/academic-programmes', type='http', auth='public', website=True)
    def programmes_page(self):
        return request.render('ust_website_programmes.academic_programs_template', {})

class PostgraduateAppliedCollege(http.Controller):
    @http.route('/programmes/postgraduate/apply-now', type='http', auth='public', website=True)
    def programmes_page(self):
        return request.render('ust_website_programmes.postgraduate_applied_college_template', {})

class InternationalAdmission(http.Controller):
    @http.route('/programmes/international/admission', type='http', auth='public', website=True)
    def programmes_page(self):
        return request.render('ust_website_programmes.international_admission_template', {})

class InternationalAcademicPrograms(http.Controller):
    @http.route('/programmes/international/academic-programmes', type='http', auth='public', website=True)
    def programmes_page(self):
        return request.render('ust_website_programmes.international_academic_program_template', {})

class InternationalAppliedCollegeController(http.Controller):
    @http.route('/programmes/international/apply-now', type='http', auth='public', website=True)
    def programmes_page(self):
        return request.render('ust_website_programmes.international_applied_college_template', {})



