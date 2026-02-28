# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class College(models.Model):
    _name = 'elearning.college'
    _description = 'College'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char('College Name', required=True, tracking=True)
    code = fields.Char('College Code', required=True, tracking=True)
    description = fields.Text('Description')
    dean_name = fields.Char('Dean Name')
    dean_email = fields.Char('Dean Email')
    dean_phone = fields.Char('Dean Phone')
    address = fields.Text('Address')
    website = fields.Char('Website')
    established_year = fields.Integer('Established Year')
    total_students = fields.Integer('Total Students', default=0)
    total_faculty = fields.Integer('Total Faculty', default=0)
    active = fields.Boolean('Active', default=True)
    
    # Related fields
    department_ids = fields.One2many('hr.department', 'college_id', string='Departments')
    course_ids = fields.One2many('slide.channel', 'college_id', string='Courses')
    exam_template_ids = fields.One2many('elearning.exam.template', 'college_id', string='Exam Schedules')
    
    # Computed fields
    total_courses = fields.Integer('Total Courses', compute='_compute_total_courses', store=True)
    total_departments = fields.Integer('Total Departments', compute='_compute_total_departments', store=True)
    total_exams = fields.Integer('Total Exam Schedules', compute='_compute_total_exams', store=True)
    
    @api.depends('course_ids')
    def _compute_total_courses(self):
        for college in self:
            college.total_courses = len(college.course_ids)
    
    @api.depends('department_ids')
    def _compute_total_departments(self):
        for college in self:
            college.total_departments = len(college.department_ids)
    
    @api.depends('exam_template_ids')
    def _compute_total_exams(self):
        for college in self:
            college.total_exams = len(college.exam_template_ids)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('elearning.college') or 'COL'
        return super().create(vals_list)
    
    def action_view_departments(self):
        """Action to view departments of this college"""
        action = self.env['ir.actions.act_window']._for_xml_id('elearning_colleges.action_view_departments')
        action['domain'] = [('college_id', '=', self.id)]
        action['context'] = {'default_college_id': self.id}
        return action
    
    def action_view_college_courses(self):
        """Action to view courses of this college"""
        action = self.env['ir.actions.act_window']._for_xml_id('elearning_colleges.action_view_college_courses')
        action['domain'] = [('college_id', '=', self.id)]
        action['context'] = {'default_college_id': self.id}
        return action
    
    def action_view_college_exams(self):
        """Action to view exam schedules of this college"""
        action = self.env['ir.actions.act_window']._for_xml_id('elearning_colleges.action_exam_template')
        action['domain'] = [('college_id', '=', self.id)]
        action['context'] = {'default_college_id': self.id}
        return action
    
    def get_exam_data_for_report(self):
        """Get exam data for PDF report"""
        self.ensure_one()
        # Get filters from context
        department_id = self.env.context.get('department_id')
        semester_id = self.env.context.get('semester_id')
        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        
        domain = [
            ('college_id', '=', self.id),
            ('website_published', '=', True),
            ('state', '!=', 'cancelled'),
        ]
        
        if department_id:
            domain.append(('department_id', '=', department_id))
        if semester_id:
            domain.append(('semester_id', '=', semester_id))
        if start_date:
            domain.append(('exam_date', '>=', start_date))
        if end_date:
            domain.append(('exam_date', '<=', end_date))
        
        entries = self.env['elearning.exam'].search(domain, order='exam_template_id, exam_date, start_time')
        
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
                'exam_date': entry.exam_date,
                'start_time': entry.start_time,
                'end_time': entry.end_time,
                'course': entry.course_id.name if entry.course_id else '',
                'department': entry.department_id.name if entry.department_id else '',
                'semester': entry.semester_id.display_name if entry.semester_id else '',
                'room': entry.room or '',
                'invigilator': entry.invigilator_id.name if entry.invigilator_id else '',
            })
        
        # Sort dates within each template and convert to list
        templates_list = []
        for template_id in exams_by_template:
            template_info = exams_by_template[template_id]
            template_info['sorted_dates'] = sorted(template_info['exams_by_date'].keys())
            templates_list.append(template_info)
        
        return {
            'exams_by_template': templates_list,
        }


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    
    college_id = fields.Many2one('elearning.college', string='College')


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    # Custom fields for course management
    course_code = fields.Char('Course Code', tracking=True)
    credit_hours = fields.Selection([
        ('1', '1 Credit Hour'),
        ('2', '2 Credit Hours'),
        ('3', '3 Credit Hours'),
        ('4', '4 Credit Hours'),
        ('5', '5 Credit Hours'),
    ], string='Credit Hours', default='3', tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    college_id = fields.Many2one('elearning.college', string='College', tracking=True)
    teacher_id = fields.Many2one('res.users', string='Teacher', tracking=True)
    prerequisite_id = fields.Many2one('slide.channel', string='Prerequisite Course', tracking=True)
    student_count = fields.Integer('Student Count', compute='_compute_student_count', store=True)
    available_prerequisite_ids = fields.Many2many('slide.channel', compute='_compute_available_prerequisites', string='Available Prerequisites')
    
    # English Course Outline Fields
    outline_level = fields.Char('Level')
    outline_description = fields.Html('Course Description')
    outline_topics = fields.Html('Topics Covered')
    outline_outcomes = fields.Html('Course Learning Outcomes')
    outline_textbooks = fields.Html('Textbooks')
    outline_assessment = fields.Html('Course Assessment')
    
    # Arabic Course Outline Fields
    outline_level_ar = fields.Char('المستوى')
    outline_description_ar = fields.Html('وصف المقرر')
    outline_topics_ar = fields.Html('محتوى المقرر')
    outline_outcomes_ar = fields.Html('مخرجات التعلم')
    outline_textbooks_ar = fields.Html('المراجع الأساسية للمقرر')
    outline_assessment_ar = fields.Html('تقييم أداء الطالب')

    @api.depends('slide_partner_ids')
    def _compute_student_count(self):
        """Compute student count from enrolled partners"""
        for course in self:
            course.student_count = len(course.slide_partner_ids)

    def _get_prerequisite_domain(self):
        self.ensure_one()
        if not (self.department_id or self.college_id):
            return [('id', '=', False)]

        domain = []
        if self.id and isinstance(self.id, int):
            domain.append(('id', '!=', self.id))

        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        else:
            domain.append(('college_id', '=', self.college_id.id))

        _logger.info(
            "[Prerequisite Domain] Course %s (college=%s, department=%s) -> %s",
            self.ids, self.college_id.ids, self.department_id.ids, domain
        )
        return domain

    def _filter_invalid_prerequisites(self):
        self.ensure_one()
        invalid = self.env['slide.channel']
        if self.id and isinstance(self.id, int):
            invalid |= self.prerequisite_channel_ids.filtered(lambda ch: ch.id == self.id)
        allowed = self.env['slide.channel'].search(self._get_prerequisite_domain())
        allowed_ids = set(allowed.ids)
        selected_ids = set()
        for ch in self.prerequisite_channel_ids:
            base_id = ch._origin.id if ch._origin and ch._origin.id else ch.id
            if base_id and isinstance(base_id, int):
                selected_ids.add(base_id)
        _logger.info(
            "[Prerequisite Allowed] Course %s domain allowed=%s selected=%s",
            self.ids, sorted(list(allowed_ids)), sorted(list(selected_ids))
        )
        invalid_ids = selected_ids - allowed_ids
        if invalid_ids:
            invalid |= self.prerequisite_channel_ids.filtered(
                lambda ch: ((ch._origin and ch._origin.id in invalid_ids) or (isinstance(ch.id, int) and ch.id in invalid_ids))
            )
        if invalid:
            _logger.info(
                "[Prerequisite Cleanup] Course %s removed invalid prerequisites %s",
                self.ids, invalid.ids
            )
            self.prerequisite_channel_ids -= invalid
        return invalid

    @api.depends('college_id', 'department_id')
    def _compute_available_prerequisites(self):
        for course in self:
            domain = course._get_prerequisite_domain()
            if domain == [('id', '=', False)]:
                course.available_prerequisite_ids = self.env['slide.channel']
            else:
                course.available_prerequisite_ids = self.env['slide.channel'].search(domain)

    def _get_onchange_domains(self):
        self.ensure_one()
        dept_domain = [('id', '=', False)]
        if self.college_id:
            dept_domain = [
                ('college_id', '=', self.college_id.id),
                ('is_college_department', '=', True)
            ]
        return {
            'department_id': dept_domain,
            'prerequisite_channel_ids': self._get_prerequisite_domain(),
        }

    @api.onchange('college_id')
    def _onchange_college_id(self):
        self.ensure_one()
        warnings = []
        if self.college_id and self.department_id and self.department_id.college_id != self.college_id:
            self.department_id = False
            warnings.append('The selected department does not belong to the chosen college. Department has been cleared.')
        invalid = self._filter_invalid_prerequisites()
        if invalid:
            warnings.append('Some pre-requisite courses do not belong to this college or department and have been removed: %s' % ', '.join(invalid.mapped('name')))
        domains = self._get_onchange_domains()
        _logger.debug(
            "[Onchange College] Course %s set college %s -> warnings=%s domains=%s",
            self.id, self.college_id.id, warnings, domains
        )
        result = {'domain': domains}
        if warnings:
            result['warning'] = {
                'title': 'Selection adjusted',
                'message': '\n'.join(warnings)
            }
        return result

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.ensure_one()
        warnings = []
        if self.department_id and self.department_id.college_id:
            if self.college_id and self.department_id.college_id != self.college_id:
                warnings.append('College was aligned with the selected department.')
            self.college_id = self.department_id.college_id
        invalid = self._filter_invalid_prerequisites()
        if invalid:
            warnings.append('Some pre-requisite courses do not belong to this department and have been removed: %s' % ', '.join(invalid.mapped('name')))
        domains = self._get_onchange_domains()
        _logger.debug(
            "[Onchange Department] Course %s set department %s -> warnings=%s domains=%s",
            self.id, self.department_id.id, warnings, domains
        )
        result = {'domain': domains}
        if warnings:
            result['warning'] = {
                'title': 'Selection adjusted',
                'message': '\n'.join(warnings)
            }
        return result

    @api.onchange('prerequisite_channel_ids')
    def _onchange_prerequisite_channel_ids(self):
        self.ensure_one()
        invalid = self._filter_invalid_prerequisites()
        if invalid:
            _logger.info(
                "[Onchange Prerequisites] Course %s removed invalid prerequisites %s",
                self.id, invalid.ids
            )
            return {
                'warning': {
                    'title': 'Invalid prerequisite',
                    'message': 'Pre-requisite courses must belong to the selected department or college. Removed: %s' % ', '.join(invalid.mapped('name'))
                },
                'domain': self._get_onchange_domains()
            }
        return {'domain': self._get_onchange_domains()}

    @api.constrains('college_id', 'department_id')
    def _check_college_department_alignment(self):
        for course in self:
            if course.department_id:
                department = course.department_id
                if not department.is_college_department:
                    raise ValidationError('Selected department is not a college department.')
                if not course.college_id:
                    raise ValidationError('Please select a college for this course.')
                if department.college_id and department.college_id != course.college_id:
                    raise ValidationError('The selected department belongs to a different college.')

    @api.constrains('prerequisite_channel_ids', 'college_id', 'department_id')
    def _check_prerequisite_restrictions(self):
        for course in self:
            if course.prerequisite_channel_ids:
                allowed_ids = self.env['slide.channel'].search(course._get_prerequisite_domain()).ids
                invalid = course.prerequisite_channel_ids.filtered(lambda ch: ch.id not in allowed_ids)
                if invalid:
                    _logger.warning(
                        "[Constraint] Course %s invalid prerequisites detected: %s",
                        course.id, invalid.ids
                    )
                    raise ValidationError(
                        'Pre-requisite courses must belong to the selected department or college. '
                        'Invalid courses: %s' % ', '.join(invalid.mapped('name'))
                    )

    @api.model_create_multi
    def create(self, vals_list):
        new_list = []
        for vals in vals_list:
            v = vals.copy()
            department_id = v.get('department_id')
            if department_id:
                department = self.env['hr.department'].browse(department_id)
                if department.college_id:
                    v.setdefault('college_id', department.college_id.id)
            _logger.debug("[Create Course] vals=%s", v)
            if not v.get('course_code'):
                sequence = self.env['ir.sequence'].next_by_code('elearning.course')
                v['course_code'] = sequence or 'CRS001'
            new_list.append(v)
        return super().create(new_list)

    def write(self, vals):
        vals = vals.copy()
        check_dependencies = any(field in vals for field in ['department_id', 'college_id'])
        if check_dependencies:
            for rec in self:
                if rec.prerequisite_of_channel_ids:
                    new_department_id = vals.get('department_id', rec.department_id.id if rec.department_id else False)
                    new_college_id = vals.get('college_id', rec.college_id.id if rec.college_id else False)
                    if (new_department_id != (rec.department_id.id if rec.department_id else False)) or (
                        new_college_id != (rec.college_id.id if rec.college_id else False)
                    ):
                        dependent_names = ', '.join(rec.prerequisite_of_channel_ids.mapped('name'))
                        raise ValidationError(
                            _('You cannot change the College or Department because this course is a prerequisite for other courses (%s). Remove this course from their prerequisites first.')
                            % dependent_names
                        )
        if 'department_id' in vals and vals['department_id']:
            department = self.env['hr.department'].browse(vals['department_id'])
            if department.college_id:
                vals.setdefault('college_id', department.college_id.id)
        _logger.debug("[Write Course %s] vals=%s", self.ids, vals)
        return super().write(vals)

    def action_view_course_outline(self):
        """Action to view English course outline PDF"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/course-outline/{self.id}/pdf',
            'target': 'new',
        }

    def action_view_course_outline_ar(self):
        """Action to view Arabic course outline PDF"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/course-outline/{self.id}/pdf/ar',
            'target': 'new',
        }


