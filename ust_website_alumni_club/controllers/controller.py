from odoo import http
from odoo.http import request

class AlumniClubController(http.Controller):
    @http.route('/alumni', type='http', auth='public', website=True)
    def alumni_club_page(self):
        return request.render('ust_website_alumni_club.alumni_club_template', {})


class VerifcationsOfUniversityAlumniController(http.Controller):
    @http.route('/university-alumni-verification', type='http', auth='public', website=True)
    def university_verification_page(self):
        return request.render('ust_website_alumni_club.university_verification_template', {})

class JobVaccanciesController(http.Controller):
    @http.route('/job-vacancies', type='http', auth='public', website=True)
    def university_verification_page(self):
        return request.render('ust_website_alumni_club.job_vacancies_template', {})