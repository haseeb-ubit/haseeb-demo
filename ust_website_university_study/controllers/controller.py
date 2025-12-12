from odoo import http
from odoo.http import request


class InternationalLanguageCenterController(http.Controller):
    @http.route('/international-language-center', type='http', auth='public', website=True)
    def international_language_page(self):
        return request.render('ust_website_university_study.international_language_template', {})


class HandramoutBranchController(http.Controller):
    @http.route('/hadramout-branch-university', type='http', auth='public', website=True)
    def handramout_branch_page(self):
        return request.render('ust_website_university_study.handramout_branch_template', {})


class FacilitiesOfMedicineController(http.Controller):
    @http.route('/faculty-of-medicine-and-health-sciences', type='http', auth='public', website=True)
    def faculty_of_medicine_page(self):
        return request.render('ust_website_university_study.facility_of_medicine_template', {})


class HandramoutBranchController(http.Controller):
    @http.route('/hadramout-branch-details-university', type='http', auth='public', website=True)
    def handramout_branch_detail_page(self):
        return request.render('ust_website_university_study.handramout_branch_details_template', {})


class FacilityOfHumanitiesController(http.Controller):
    @http.route('/faculty-of-humanities-and-administrative-sciences', type='http', auth='public', website=True)
    def facility_of_humanities_page(self):
        return request.render('ust_website_university_study.facility_of_humanities_template', {})


class DeanshipOfELearningController(http.Controller):
    @http.route('/deanship-of-electronic-and-distance-learning', type='http', auth='public', website=True)
    def deanship_of_e_learning_page(self):
        return request.render('ust_website_university_study.deanship_of_e_learning_template', {})


class DeanshipOfPostgraduateController(http.Controller):
    @http.route('/deanship-of-postgraduate-studies-and-scientific-research', type='http', auth='public', website=True)
    def deanship_of_e_learning_page(self):
        return request.render('ust_website_university_study.deanship_of_postgraduate_template', {})


class UniversityBookCenterController(http.Controller):
    @http.route('/university-book-center', type='http', auth='public', website=True)
    def deanship_of_e_learning_page(self):
        return request.render('ust_website_university_study.university_book_center_template', {})


class FacultyOfEngineeringController(http.Controller):
    @http.route('/faculty-of-engineering-and-computing', type='http', auth='public', website=True)
    def deanship_of_e_learning_page(self):
        return request.render('ust_website_university_study.faculty_of_engineering_and_computing_template', {})
