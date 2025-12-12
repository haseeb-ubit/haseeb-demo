from odoo import http
from odoo.http import request
from werkzeug.utils import redirect


class ExamScheduleController(http.Controller):
    @http.route('/exam-timetables', type='http', auth='public', website=True)
    def student_service_page(self):
        return request.render('ust_website_student_service.exam_schedule_template', {})


class CampusController(http.Controller):
    @http.route('/campus-life', type='http', auth='public', website=True)
    def student_service_page(self):
        return request.render('ust_website_student_service.campus_template', {})


class StudentGuideController(http.Controller):
    # Directly redirect user to PDF download when visiting '/student/guide'
    @http.route('/student-guide', type='http', auth='public',
                )
    def student_guide_download(self):
        return redirect('/ust_website_student_service/static/src/pdf/pdf1.pdf');


class CollegeGuideController(http.Controller):
    @http.route('/faculty-brochoures', type='http', auth='public', website=True)
    def student_service_page(self):
        return request.render('ust_website_student_service.college_guide_template', {})


class PlacementExamInstructionsController(http.Controller):
    # Directly redirect user to PDF download when visiting '/student/guide'
    @http.route('/placement-exam-instruction', type='http', auth='public',
                )
    def student_guide_download(self):
        return redirect('/ust_website_student_service/static/src/pdf/pdf3.pdf')


class ElearningController(http.Controller):

    @http.route('/e-learning', type='http', auth='public',
                )
    def student_guide_download(self):
        return redirect('/ust_website_student_service/static/src/pdf/pdf4.pdf')


class ElearningportalController(http.Controller):
    # Redirect user to https://smart.ust.edu/
    @http.route('/redirect_to_smart_ust', type='http', auth='public')
    def redirect_to_smart_ust(self):
        return http.redirect_with_hash('https://smart.ust.edu/')


class StudySchedulesController(http.Controller):
    @http.route('/schedules', type='http', auth='public', website=True)
    def student_service_page(self):
        return request.render('ust_website_student_service.study_schedules_template', {})


class AcademicCalendarController(http.Controller):
    @http.route('/academic-calendar', type='http', auth='public', website=True)
    def student_service_page(self):
        return request.render('ust_website_student_service.academic_calendar_template', {})


class ExamStudentAccommodationController(http.Controller):
    @http.route('/student-accommodation', type='http', auth='public', website=True)
    def exam_student_accommodation_page(self):
        return request.render('ust_website_student_service.exam_student_accommodation_template', {})


class FormsController(http.Controller):
    @http.route('/forms', type='http', auth='public', website=True)
    def forms_page(self):
        return request.render('ust_website_student_service.forms_template', {})


class RedirectController(http.Controller):

    @http.route('/redirect-to-erp', type='http', auth="public", website=True)
    def redirect_to_external_url(self, **kwargs):
        return request.redirect("https://erp.ust.edu/ords/f?p=103:LOGIN_DESKTOP:11779259183389:::::")


class RedirectSmartController(http.Controller):
    @http.route('/redirect-to-smart', type='http', auth="public", website=True)
    def redirect_to_external_url(self, **kwargs):
        return request.redirect("https://smart.ust.edu/")


class LibraryController(http.Controller):
    @http.route('/library', type='http', auth='public', website=True)
    def library_page(self):
        return request.render('ust_website_student_service.library_template', {})
