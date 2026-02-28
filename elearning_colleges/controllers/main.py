# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
import urllib.parse
import re
import json


class ElearningCollegesController(http.Controller):
    def _float_to_time(self, float_time):
        if float_time is None:
            return ''
        hours = int(float_time)
        minutes = int(round((float_time - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    def _build_department_timetable_data(self, department_id, year=None, semester=None):
        domain = [
            ('department_id', '=', department_id),
            ('website_published', '=', True),
        ]
        if year:
            domain.append(('semester_id.year', '=', int(year)))
        if semester:
            domain.append(('semester_id.semester_number', '=', int(semester)))

        entries = request.env['elearning.timetable'].sudo().search(domain, order='semester_id, day_of_week, start_time')
        
        day_names = {
            '0': 'Monday',
            '1': 'Tuesday',
            '2': 'Wednesday',
            '3': 'Thursday',
            '4': 'Friday',
            '5': 'Saturday',
            '6': 'Sunday',
        }
        day_keys = ['0', '1', '2', '3', '4', '5', '6']

        # Group entries by semester
        semesters_data = []
        semester_groups = {}
        
        for entry in entries:
            sem_id = entry.semester_id.id if entry.semester_id else None
            if sem_id not in semester_groups:
                semester_groups[sem_id] = {
                    'semester_id': entry.semester_id,
                    'semester_name': entry.semester_id.display_name if entry.semester_id else 'Unknown',
                    'entries': []
                }
            semester_groups[sem_id]['entries'].append(entry)
        
        # Build timetable grid for each semester
        for sem_id, sem_data in semester_groups.items():
            sem_entries = sem_data['entries']
            time_slots_raw = sorted(set((e.start_time, e.end_time) for e in sem_entries))
            time_slots = [{'start': self._float_to_time(s), 'end': self._float_to_time(e), 'start_str': self._float_to_time(s), 'end_str': self._float_to_time(e)} for s, e in time_slots_raw]
            
            timetable_grid = {d: {} for d in day_keys}
            slot_map = {(s, e): idx for idx, (s, e) in enumerate(time_slots_raw)}
            
            for entry in sem_entries:
                slot_idx = slot_map.get((entry.start_time, entry.end_time))
                if slot_idx is None:
                    continue
                timetable_grid.setdefault(entry.day_of_week, {}).setdefault(slot_idx, []).append({
                    'course': entry.course_id.name if entry.course_id else '',
                    'teacher': entry.teacher_id.name if entry.teacher_id else '',
                    'room': entry.room or '',
                    'start': self._float_to_time(entry.start_time),
                    'end': self._float_to_time(entry.end_time),
                })
            
            sem_record = sem_data['semester_id']
            sem_year = sem_record.year if sem_record else 0
            sem_num = sem_record.semester_number if sem_record else 0
            semesters_data.append({
                'semester_id': sem_record,
                'semester_name': sem_data['semester_name'],
                'year': sem_year,
                'semester_number': sem_num,
                'year_label': f'Year {sem_year}',
                'timetable_grid': timetable_grid,
                'time_slots': time_slots,
                'entries': sem_entries,
                'no_data': not bool(sem_entries),
            })
        
        # Sort semesters by year and semester number
        semesters_data.sort(key=lambda x: (
            x['semester_id'].year if x['semester_id'] else 999,
            x['semester_id'].semester_number if x['semester_id'] else 999
        ))

        return {
            'semesters_data': semesters_data,
            'day_names': day_names,
            'day_keys': day_keys,
            'no_data': not bool(entries),
        }

    @http.route('/colleges/<int:college_id>', type='http', auth='public', website=True)
    def college_detail(self, college_id, **kw):
        """Maintain legacy URL by redirecting to departments page"""
        college = request.env['elearning.college'].sudo().browse(college_id)
        if not college.exists() or not college.active:
            return request.not_found()
        return request.redirect(f'/colleges/{college_id}/department')

    @http.route('/colleges/<int:college_id>/department', type='http', auth='public', website=True)
    def college_departments(self, college_id, **kw):
        """Display departments for a given college"""
        college = request.env['elearning.college'].sudo().browse(college_id)
        if not college.exists() or not college.active:
            return request.not_found()

        departments = request.env['hr.department'].sudo().search([
            ('college_id', '=', college_id),
            ('is_college_department', '=', True),
            ('active', '=', True),
            ('website_published', '=', True)
        ], order='name')

        department_published_counts = {
            dept.id: len(dept.course_ids.filtered(lambda c: c.active and c.website_published))
            for dept in departments
        }

        return request.render('elearning_colleges.college_departments_template', {
            'college': college,
            'departments': departments,
            'department_published_counts': department_published_counts,
        })

    @http.route('/colleges/<int:college_id>/resume', type='http', auth='public', website=True)
    def college_resumes(self, college_id, **kw):
        """Display faculty resumes for a given college with advanced search metadata"""
        college = request.env['elearning.college'].sudo().browse(college_id)
        if not college.exists() or not college.active:
            return request.not_found()

        arabic_resumes = request.env['ust.resume'].sudo().search([
            ('college_id', '=', college_id),
            ('website_published', '=', True)
        ])
        english_resumes = request.env['ust.resume.en'].sudo().search([
            ('college_id', '=', college_id),
            ('website_published', '=', True)
        ])

        def _normalize_list(values):
            """Return list with unique values preserving order (case-insensitive)."""
            seen = set()
            ordered = []
            for val in values:
                if not val:
                    continue
                key = val.lower()
                if key not in seen:
                    seen.add(key)
                    ordered.append(val)
            return ordered

        def _extract_education(resume_records):
            degrees = _normalize_list([
                (deg or '').strip()
                for deg in resume_records.mapped('degree')
                if deg and deg.strip()
            ])
            specializations = _normalize_list([
                (spec or '').strip()
                for spec in resume_records.mapped('specialization')
                if spec and spec.strip()
            ])
            return degrees, specializations

        teachers_data = []
        teacher_lookup = {}

        for resume in arabic_resumes:
            user_id = resume.user_id.id if resume.user_id else None
            if not user_id or user_id in teacher_lookup:
                continue

            degrees, specializations = _extract_education(resume.education_ids)
            department_name = (resume.department_id.name or '').strip()

            teacher_entry = {
                'user_id': user_id,
                'name': resume.user_id.name,
                'job_title': resume.job_title or '',
                'email': resume.email or '',
                'photo': resume.photo,
                'photo_model': 'ust.resume',
                'photo_id': resume.id,
                'college_id': resume.college_id.id if resume.college_id else False,
                'department_id': resume.department_id.id if resume.department_id else False,
                'department_name': department_name,
                'degrees': degrees,
                'specializations': specializations,
                'resume_id': resume.id,
                'resume_id_en': False,
                'resume_type': 'ar'
            }

            teachers_data.append(teacher_entry)
            teacher_lookup[user_id] = teacher_entry

        for resume in english_resumes:
            user_id = resume.user_id.id if resume.user_id else None
            if user_id:
                degrees, specializations = _extract_education(resume.education_ids)
                department_name = (resume.department_id.name or '').strip()
                existing = teacher_lookup.get(user_id)
                if existing:
                    existing['resume_id_en'] = resume.id
                    existing['resume_type'] = 'both'
                    if not existing.get('photo') and resume.photo:
                        existing['photo'] = resume.photo
                        existing['photo_model'] = 'ust.resume.en'
                        existing['photo_id'] = resume.id
                    existing['degrees'] = _normalize_list((existing.get('degrees') or []) + degrees)
                    existing['specializations'] = _normalize_list((existing.get('specializations') or []) + specializations)
                    if not existing.get('department_name') and department_name:
                        existing['department_name'] = department_name
                else:
                    teacher_entry = {
                        'user_id': user_id,
                        'name': resume.user_id.name,
                        'job_title': resume.job_title or '',
                        'email': resume.email or '',
                        'photo': resume.photo,
                        'photo_model': 'ust.resume.en',
                        'photo_id': resume.id,
                        'college_id': resume.college_id.id if resume.college_id else False,
                        'department_id': resume.department_id.id if resume.department_id else False,
                        'department_name': department_name,
                        'degrees': degrees,
                        'specializations': specializations,
                        'resume_id': resume.id,
                        'resume_id_en': False,
                        'resume_type': 'en'
                    }
                    teachers_data.append(teacher_entry)
                    teacher_lookup[user_id] = teacher_entry

        department_values = sorted({
            teacher.get('department_name').strip()
            for teacher in teachers_data
            if teacher.get('department_name')
        }, key=lambda x: x.lower())

        degree_values = sorted({
            degree
            for teacher in teachers_data
            for degree in (teacher.get('degrees') or [])
            if degree
        }, key=lambda x: x.lower())

        specialization_values = sorted({
            specialization
            for teacher in teachers_data
            for specialization in (teacher.get('specializations') or [])
            if specialization
        }, key=lambda x: x.lower())

        resume_filters_payload = {
            'department': department_values,
            'degree': degree_values,
            'specialization': specialization_values,
            'teacher': sorted({
                teacher.get('name').strip()
                for teacher in teachers_data
                if teacher.get('name')
            }, key=lambda x: x.lower()),
        }

        resume_teachers_payload = [{
            'user_id': teacher.get('user_id'),
            'name': teacher.get('name', ''),
            'department_name': teacher.get('department_name', ''),
            'degrees': teacher.get('degrees', []),
            'specializations': teacher.get('specializations', []),
        } for teacher in teachers_data]

        return request.render('elearning_colleges.college_resumes_template', {
            'college': college,
            'teachers': teachers_data,
            'resume_filters_json': json.dumps(resume_filters_payload, ensure_ascii=False),
            'resume_teachers_json': json.dumps(resume_teachers_payload, ensure_ascii=False),
        })

    @http.route('/colleges/<int:college_id>/department/<int:department_id>/courses', type='http', auth='public', website=True)
    def department_courses(self, college_id, department_id, **kw):
        """Display courses, requirements, and semesters filtered by department"""
        department = request.env['hr.department'].sudo().browse(department_id)
        if (not department.exists() or department.college_id.id != college_id
                or not department.is_college_department or not department.website_published):
            return request.not_found()
        
        # Get courses for this department
        # Use website_published field instead of is_published
        courses = request.env['slide.channel'].sudo().search([
            ('department_id', '=', department_id),
            ('website_published', '=', True)
        ], order='name')
        
        # Get requirements grouped by type
        requirements_by_type = {
            'faculty': request.env['elearning.requirement'].sudo().search([
                ('department_id', '=', department_id),
                ('requirement_type', '=', 'faculty')
            ], order='course_id'),
            'department': request.env['elearning.requirement'].sudo().search([
                ('department_id', '=', department_id),
                ('requirement_type', '=', 'department')
            ], order='course_id'),
            'program': request.env['elearning.requirement'].sudo().search([
                ('department_id', '=', department_id),
                ('requirement_type', '=', 'program')
            ], order='course_id'),
            'elective': request.env['elearning.requirement'].sudo().search([
                ('department_id', '=', department_id),
                ('requirement_type', '=', 'elective')
            ], order='course_id'),
            'university': request.env['elearning.requirement'].sudo().search([
                ('department_id', '=', department_id),
                ('requirement_type', '=', 'university')
            ], order='course_id'),
        }
        
        # Get semesters grouped by year and semester_number
        semesters_by_year = {}
        all_semesters = request.env['elearning.semester'].sudo().search([
            ('department_id', '=', department_id)
        ], order='year, semester_number, course_id')
        
        for semester in all_semesters:
            year = semester.year
            sem_num = semester.semester_number
            key = f'Y{year}S{sem_num}'
            if key not in semesters_by_year:
                semesters_by_year[key] = []
            semesters_by_year[key].append(semester)
        
        # Sort semester keys for consistent display
        semester_keys_sorted = sorted(semesters_by_year.keys())
        first_semester_key = semester_keys_sorted[0] if semester_keys_sorted else None

        return request.render('elearning_colleges.department_courses_template', {
            'department': department,
            'college': department.college_id,
            'courses': courses,
            'requirements_by_type': requirements_by_type,
            'semesters_by_year': semesters_by_year,
            'semester_keys_sorted': semester_keys_sorted,
            'first_semester_key': first_semester_key
        })

    @http.route('/course-outline/<int:course_id>', type='http', auth='public', website=True)
    def course_outline(self, course_id, **kw):
        return request.redirect(f'/course-outline/{course_id}/pdf')

    @http.route('/course-outline/<int:course_id>/pdf', type='http', auth='public', website=True, csrf=False)
    def course_outline_pdf(self, course_id, **kw):
        """Render English course outline as PDF"""
        course = request.env['slide.channel'].sudo().browse(course_id)
        if not course.exists():
            return request.not_found()

        if not course.website_published and request.env.user.has_group('base.group_public'):
            return request.redirect('/web/login')

        report = request.env.ref('elearning_colleges.action_report_course_outline')
        pdf_content, _ = report.sudo()._render_qweb_pdf('elearning_colleges.course_outline_report_template', [course_id])

        course_name = course.name or 'Course-Outline'
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', course_name)
        filename = f"Course Outline {sanitized_name}.pdf"

        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{filename}"')
            ]
        )

    @http.route('/course-outline/<int:course_id>/pdf/ar', type='http', auth='public', website=True, csrf=False)
    def course_outline_pdf_ar(self, course_id, **kw):
        """Render Arabic course outline as PDF"""
        course = request.env['slide.channel'].sudo().browse(course_id)
        if not course.exists():
            return request.not_found()

        if not course.website_published and request.env.user.has_group('base.group_public'):
            return request.redirect('/web/login')

        report = request.env.ref('elearning_colleges.action_report_course_outline_ar')
        pdf_content, _ = report.sudo()._render_qweb_pdf('elearning_colleges.course_outline_report_template_ar', [course_id])

        course_name = course.name or 'Course-Outline'
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', course_name)
        filename = f"Course Outline {sanitized_name} (Arabic).pdf"

        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{filename}"')
            ]
        )

    def _get_department_name(self, department_id):
        """Helper method to get department name"""
        try:
            department = request.env['hr.department'].sudo().browse(department_id)
            if department.exists() and department.is_college_department and department.name:
                return department.name
        except (AccessError, MissingError):
            pass
        return None

    @http.route(['/report/pdf/elearning_colleges.action_report_department_requirements/<int:department_id>'], type='http', auth='public', website=True, csrf=False)
    def department_requirements_report_pdf(self, department_id, **kw):
        """Override the standard department requirements report route"""
        department_name = self._get_department_name(department_id)
        if not department_name:
            return request.not_found()
        
        # Format filename: Requirements-<department_name>.pdf
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', department_name)
        pdf_filename = f"Requirements-{sanitized_name}.pdf"
        encoded_filename = urllib.parse.quote(pdf_filename, safe='')
        
        return request.redirect(f'/department_pdf/{department_id}/requirements/{encoded_filename}')

    @http.route(['/report/pdf/elearning_colleges.action_report_department_semesters/<int:department_id>'], type='http', auth='public', website=True, csrf=False)
    def department_semesters_report_pdf(self, department_id, **kw):
        """Override the standard department semesters report route"""
        department_name = self._get_department_name(department_id)
        if not department_name:
            return request.not_found()
        
        # Format filename: Semesters-<department_name>.pdf
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', department_name)
        pdf_filename = f"Semesters-{sanitized_name}.pdf"
        encoded_filename = urllib.parse.quote(pdf_filename, safe='')
        
        return request.redirect(f'/department_pdf/{department_id}/semesters/{encoded_filename}')

    @http.route(['/department_pdf/<int:department_id>/<string:report_type>/<path:filename>'], type='http', auth='public', website=True, csrf=False)
    def department_pdf_named(self, department_id, report_type, filename, **kw):
        """Serve department PDF with custom filename - handles both Requirements and Semesters"""
        is_requirements = (report_type == 'requirements')
        report_ref = 'elearning_colleges.action_report_department_requirements' if is_requirements else 'elearning_colleges.action_report_department_semesters'
        template_ref = 'elearning_colleges.department_requirements_report_template' if is_requirements else 'elearning_colleges.department_semesters_report_template'
        
        try:
            department = request.env['hr.department'].sudo().browse(department_id)
            if not department.exists():
                return request.not_found()
        except (AccessError, MissingError):
            return request.not_found()

        # Generate PDF using the correct Odoo 18 method
        report = request.env.ref(report_ref)
        pdf_content, _ = report.sudo()._render_qweb_pdf(template_ref, [department_id])

        # Decode the filename from URL
        decoded_filename = urllib.parse.unquote(filename)

        # Return PDF with custom filename
        response = request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{decoded_filename}"')
            ]
        )

        return response

    @http.route('/colleges/<int:college_id>/department/<int:department_id>/timetable', type='http', auth='public', website=True)
    def department_timetable(self, college_id, department_id, year=None, semester=None, **kw):
        """Department timetable view (all semesters by default)."""
        department = request.env['hr.department'].sudo().browse(department_id)
        college = request.env['elearning.college'].sudo().browse(college_id)
        if (not department.exists() or department.college_id.id != college_id
                or not college.exists() or not college.active):
            return request.not_found()

        data = self._build_department_timetable_data(department_id, year=year, semester=semester)
        return request.render('elearning_colleges.department_timetable_template', {
            'department': department,
            'college': college,
            'year': year,
            'semester': semester,
            **data,
        })

    @http.route(['/report/pdf/elearning_colleges.action_report_department_timetable/<int:department_id>'], type='http', auth='public', website=True, csrf=False)
    def department_timetable_report_pdf(self, department_id, **kw):
        """Generate PDF report for complete department timetable (all semesters)."""
        department_name = self._get_department_name(department_id)
        if not department_name:
            return request.not_found()

        department = request.env['hr.department'].sudo().browse(department_id)
        
        # Generate PDF using the report action - always all semesters
        # The timetable data will be fetched by the template via doc.get_timetable_data_for_report()
        report = request.env.ref('elearning_colleges.action_report_department_timetable')
        pdf_content, _ = report.sudo()._render_qweb_pdf(
            'elearning_colleges.department_timetable_report_template', [department_id]
        )

        # Format filename - always complete department timetable
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', department_name)
        pdf_filename = f"Timetable-{sanitized_name}.pdf"

        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{pdf_filename}"')
            ]
        )

    @http.route('/colleges/<int:college_id>/department/<int:department_id>/noticeboard', type='http', auth='public', website=True)
    def department_noticeboard(self, college_id, department_id, **kw):
        """Display department-wide published noticeboard."""
        department = request.env['hr.department'].sudo().browse(department_id)
        college = request.env['elearning.college'].sudo().browse(college_id)
        if (not department.exists() or department.college_id.id != college_id
                or not college.exists() or not college.active):
            return request.not_found()

        notices = request.env['elearning.noticeboard'].sudo().search([
            ('department_id', '=', department_id),
            ('website_published', '=', True),
        ], order='priority desc, publish_date desc')

        priority_labels = {'0': 'Low', '1': 'Medium', '2': 'High', '3': 'Urgent'}
        return request.render('elearning_colleges.semester_noticeboard_template', {
            'semester': False,
            'department': department,
            'college': college,
            'notices': notices,
            'priority_labels': priority_labels,
        })

    @http.route('/colleges/<int:college_id>/department/<int:department_id>/semester/<int:semester_id>/timetable', type='http', auth='public', website=True)
    def semester_timetable(self, college_id, department_id, semester_id, **kw):
        """Legacy semester route: redirect to the department timetable (all semesters)."""
        sem = request.env['elearning.semester'].sudo().browse(semester_id)
        if not sem.exists():
            return request.not_found()
        return request.redirect(
            f"/colleges/{college_id}/department/{department_id}/timetable"
        )

    def _build_college_exam_data(self, college_id, department_id=None, semester_id=None):
        """Build exam data for website/PDF display"""
        domain = [
            ('college_id', '=', college_id),
            ('website_published', '=', True),
            ('state', '!=', 'cancelled'),
        ]
        
        if department_id:
            domain.append(('department_id', '=', department_id))
        if semester_id:
            domain.append(('semester_id', '=', semester_id))
        
        entries = request.env['elearning.exam'].sudo().search(domain, order='exam_template_id, exam_date, start_time')
        
        # Group by exam template, then by date
        exams_by_template = {}
        for entry in entries:
            template_id = entry.exam_template_id.id if entry.exam_template_id else 0
            template_name = entry.exam_template_id.name if entry.exam_template_id else 'Unknown'
            template_type = entry.exam_template_id.exam_type if entry.exam_template_id else 'other'
            
            if template_id not in exams_by_template:
                exams_by_template[template_id] = {
                    'template_name': template_name,
                    'template_type': template_type,
                    'exams_by_date': {},
                }
            
            date_key = entry.exam_date.strftime('%Y-%m-%d') if entry.exam_date else 'unknown'
            if date_key not in exams_by_template[template_id]['exams_by_date']:
                exams_by_template[template_id]['exams_by_date'][date_key] = []
            
            exams_by_template[template_id]['exams_by_date'][date_key].append({
                'id': entry.id,
                'exam_date': entry.exam_date,
                'start_time': entry.start_time,
                'end_time': entry.end_time,
                'shift_number': entry.shift_number,
                'course': entry.course_id.name if entry.course_id else '',
                'course_id': entry.course_id.id if entry.course_id else False,
                'department': entry.department_id.name if entry.department_id else '',
                'department_id': entry.department_id.id if entry.department_id else False,
                'semester': entry.semester_id.display_name if entry.semester_id else '',
                'semester_id': entry.semester_id.id if entry.semester_id else False,
                'room': entry.room or '',
                'invigilator': entry.invigilator_id.name if entry.invigilator_id else '',
                'invigilator_id': entry.invigilator_id.id if entry.invigilator_id else False,
                'state': entry.state,
            })
        
        # Sort dates within each template and convert to list
        templates_list = []
        for template_id in exams_by_template:
            template_info = exams_by_template[template_id]
            template_info['sorted_dates'] = sorted(template_info['exams_by_date'].keys())
            templates_list.append(template_info)
        
        return {
            'exams_by_template': templates_list,
            'total_exams': len(entries),
            'no_data': not bool(entries),
        }

    @http.route('/colleges/<int:college_id>/exams', type='http', auth='public', website=True)
    def college_exams(self, college_id, department_id=None, semester_id=None, **kw):
        """College exam schedule page"""
        college = request.env['elearning.college'].sudo().browse(college_id)
        if not college.exists() or not college.active:
            return request.not_found()
        
        # Get filter values from query params
        dept_id = int(department_id) if department_id and department_id.isdigit() else None
        sem_id = int(semester_id) if semester_id and semester_id.isdigit() else None
        
        data = self._build_college_exam_data(college_id, department_id=dept_id, semester_id=sem_id)
        
        # Get departments and semesters for filters
        departments = request.env['hr.department'].sudo().search([
            ('college_id', '=', college_id),
            ('is_college_department', '=', True),
            ('active', '=', True),
        ], order='name')
        
        semester_slots = request.env['elearning.semester.slot'].sudo().search([
            ('department_id.college_id', '=', college_id),
        ], order='year, semester_number')
        
        return request.render('elearning_colleges.college_exam_schedule_template', {
            'college': college,
            'departments': departments,
            'semester_slots': semester_slots,
            'selected_department_id': dept_id,
            'selected_semester_id': sem_id,
            **data,
        })

    @http.route(['/report/pdf/elearning_colleges.action_report_college_exam/<int:college_id>'], type='http', auth='public', website=True, csrf=False)
    def college_exam_report_pdf(self, college_id, department_id=None, semester_id=None, **kw):
        """Generate PDF report for college exam schedule"""
        college = request.env['elearning.college'].sudo().browse(college_id)
        if not college.exists() or not college.active:
            return request.not_found()
        
        # Get filter values
        dept_id = int(department_id) if department_id and department_id.isdigit() else None
        sem_id = int(semester_id) if semester_id and semester_id.isdigit() else None
        
        # Generate PDF using the report action
        report = request.env.ref('elearning_colleges.action_report_college_exam')
        context = {}
        if dept_id:
            context['department_id'] = dept_id
        if sem_id:
            context['semester_id'] = sem_id
        pdf_content, _ = report.sudo().with_context(**context)._render_qweb_pdf(
            'elearning_colleges.college_exam_report_template', [college_id]
        )
        
        # Format filename
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', college.name or 'College')
        pdf_filename = f"Exam-Schedule-{sanitized_name}.pdf"
        
        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{pdf_filename}"')
            ]
        )
