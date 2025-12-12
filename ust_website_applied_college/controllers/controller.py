from odoo import http
from odoo.http import request

class AppliedCollegeeController(http.Controller):
    @http.route('/applied-college-of-science-and-technology', type='http', auth='public', website=True)
    def applied_college_page(self):
        return request.render('ust_website_applied_college.applied_college_template', {})