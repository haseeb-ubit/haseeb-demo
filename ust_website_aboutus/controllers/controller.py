from odoo import http
from odoo.http import request

class AboutUsController(http.Controller):
    @http.route('/about-us', type='http', auth='public', website=True)
    def about_us_page(self):
        return request.render('ust_website_aboutus.about_us_template', {})

class universityPresidentController(http.Controller):
    @http.route('/university-president-opening-statement', type='http', auth='public', website=True)
    def about_us_page(self):
        return request.render('ust_website_aboutus.university_president_template', {})

class CertificateAchievementsController(http.Controller):
    @http.route('/international-rewards-and-recognitions', type='http', auth='public', website=True)
    def about_us_page(self):
        return request.render('ust_website_aboutus.certificate_achievements_template', {})

class FactsAndFigureController(http.Controller):
    @http.route('/facts-and-figures', type='http', auth='public', website=True)
    def about_us_page(self):
        return request.render('ust_website_aboutus.facts_and_figure_template', {})