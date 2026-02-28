# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Exam(models.Model):
    _name = 'elearning.exam'
    _description = 'Exam Entry'
    _order = 'exam_date, start_time'
    _rec_name = 'display_name'

    exam_template_id = fields.Many2one('elearning.exam.template', string='Exam Template', 
                                       required=True, ondelete='cascade')
    college_id = fields.Many2one('elearning.college', string='College',
                                 related='exam_template_id.college_id', store=True, readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    semester_id = fields.Many2one('elearning.semester.slot', string='Semester', tracking=True)
    course_id = fields.Many2one('slide.channel', string='Course', tracking=True,
                                domain="[('id', 'in', available_course_ids)]")
    
    # Date and Time
    exam_date = fields.Date('Exam Date', required=True, tracking=True)
    shift_number = fields.Integer('Shift Number', required=True)
    start_time = fields.Char('Start Time', required=True, tracking=True)
    end_time = fields.Char('End Time', required=True, readonly=True)
    
    # Venue and Invigilator
    room = fields.Char('Room', tracking=True, help='Room number or name')
    invigilator_id = fields.Many2one('res.users', string='Invigilator', tracking=True)
    
    # Status
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='scheduled', tracking=True)
    website_published = fields.Boolean('Published on Website', related='exam_template_id.website_published', 
                                       readonly=True, store=True)
    
    # Computed
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    available_course_ids = fields.Many2many('slide.channel', compute='_compute_available_course_ids',
                                            string='Available Courses')
    
    @api.depends('course_id', 'exam_date', 'start_time', 'end_time')
    def _compute_display_name(self):
        for exam in self:
            if exam.course_id:
                exam.display_name = f"{exam.course_id.name} - {exam.exam_date} {exam.start_time}"
            else:
                exam.display_name = f"Exam - {exam.exam_date} {exam.start_time}"
    
    @api.depends('semester_id', 'department_id')
    def _compute_available_course_ids(self):
        for exam in self:
            if exam.semester_id:
                # Get courses from semester lines for this semester slot
                domain = [
                    ('year', '=', exam.semester_id.year),
                    ('semester_number', '=', exam.semester_id.semester_number),
                    ('course_id', '!=', False),
                ]
                if exam.department_id:
                    domain.append(('department_id', '=', exam.department_id.id))
                
                semester_records = self.env['elearning.semester'].search(domain)
                course_ids = [cid for cid in semester_records.mapped('course_id').ids if cid]
                exam.available_course_ids = [(6, 0, course_ids)] if course_ids else [(5, 0, 0)]
            else:
                exam.available_course_ids = [(5, 0, 0)]
    
    @api.onchange('department_id')
    def _onchange_department_id(self):
        """Clear semester and course when department changes"""
        if self.department_id:
            # Clear semester if it doesn't belong to this department
            if self.semester_id:
                if self.semester_id.department_id != self.department_id:
                    self.semester_id = False
            # Clear course if it doesn't belong to this department
            if self.course_id:
                if self.course_id.department_id != self.department_id:
                    self.course_id = False
        else:
            self.semester_id = False
            self.course_id = False
        return {
            'domain': {
                'semester_id': [('department_id', '=', self.department_id.id)] if self.department_id else [],
                'course_id': [('id', 'in', self.available_course_ids.ids)]
            }
        }
    
    @api.onchange('semester_id')
    def _onchange_semester_id(self):
        """Update department and available courses when semester changes"""
        if self.semester_id:
            # Set department from semester if not set
            if not self.department_id:
                semester_records = self.env['elearning.semester'].search([
                    ('year', '=', self.semester_id.year),
                    ('semester_number', '=', self.semester_id.semester_number),
                ], limit=1)
                if semester_records:
                    self.department_id = semester_records[0].department_id
            # Clear course if it doesn't belong to this semester
            if self.course_id:
                if self.course_id.id not in self.available_course_ids.ids:
                    self.course_id = False
        return {
            'domain': {
                'course_id': [('id', 'in', self.available_course_ids.ids)]
            }
        }
    
    @api.onchange('course_id')
    def _onchange_course_id(self):
        """Validate course belongs to selected department and semester"""
        if self.course_id and self.department_id:
            if self.course_id.department_id != self.department_id:
                return {
                    'warning': {
                        'title': 'Invalid Course',
                        'message': f"Course '{self.course_id.name}' does not belong to department '{self.department_id.name}'. Please select a course from the selected department."
                    }
                }
        if self.course_id and self.semester_id:
            if self.course_id.id not in self.available_course_ids.ids:
                return {
                    'warning': {
                        'title': 'Invalid Course',
                        'message': f"Course '{self.course_id.name}' is not available for the selected semester. Please select a course from the available courses for this semester."
                    }
                }
    
    @api.constrains('department_id', 'course_id', 'semester_id')
    def _check_department_semester_course(self):
        """Validate department, semester, and course relationships"""
        for exam in self:
            if exam.department_id and exam.course_id:
                if exam.course_id.department_id != exam.department_id:
                    raise ValidationError(
                        f"Course '{exam.course_id.name}' does not belong to department '{exam.department_id.name}'. "
                        "Please select a course from the selected department."
                    )
            
            if exam.semester_id and exam.department_id:
                if exam.semester_id.department_id != exam.department_id:
                    raise ValidationError(
                        f"Semester '{exam.semester_id.display_name}' does not belong to department '{exam.department_id.name}'. "
                        "Please select a semester from the selected department."
                    )
            
            if exam.semester_id and exam.course_id:
                if exam.course_id.id not in exam.available_course_ids.ids:
                    raise ValidationError(
                        f"Course '{exam.course_id.name}' is not available for semester '{exam.semester_id.display_name}'. "
                        "Please select a course that is available for the selected semester."
                    )
