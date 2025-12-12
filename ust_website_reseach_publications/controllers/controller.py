from odoo import http
from odoo.http import request

class ResearchandPublicationsController(http.Controller):
    @http.route('/research-publications', type='http', auth='public', website=True)
    def research_publications_page(self):
        return request.render('ust_website_reseach_publications.research_publications_template', {})

