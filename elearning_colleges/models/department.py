# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    # Image field for website display
    image = fields.Binary('Department Image', help='Department image for website display')
    is_college_department = fields.Boolean('College Department', compute='_compute_is_college_department', store=True)
    website_published = fields.Boolean('Published on Website', default=False)
    published_date = fields.Datetime('Published On', readonly=True)
    head_of_department_name = fields.Char('Head of Department')

    # Add relationships for courses
    course_ids = fields.One2many('slide.channel', 'department_id', string='Courses')
    total_courses = fields.Integer('Total Courses', compute='_compute_total_courses', store=True)
    department_course_ids = fields.Many2many('slide.channel', compute='_compute_department_course_ids', string='Department Courses')
    
    @api.depends('course_ids')
    def _compute_total_courses(self):
        for dept in self:
            dept.total_courses = len(dept.course_ids.filtered('active'))
    
    @api.depends('college_id')
    def _compute_is_college_department(self):
        for dept in self:
            dept.is_college_department = bool(dept.college_id)

    @api.depends('course_ids')
    def _compute_department_course_ids(self):
        """Compute field to provide department-specific courses for views"""
        for dept in self:
            dept.department_course_ids = dept.course_ids.filtered('active')

    def action_view_department_courses(self):
        """Action to view courses of this department"""
        action = self.env['ir.actions.act_window']._for_xml_id('website_slides.slide_channel_action_overview')
        action['domain'] = [('department_id', '=', self.id)]
        action['context'] = {
            'default_department_id': self.id,
            'default_college_id': self.college_id.id if self.college_id else False
        }
        return action

    @api.model
    def create(self, vals):
        dept = super().create(vals)
        if dept.website_published and not dept.published_date:
            dept.published_date = fields.Datetime.now()
        return dept

    def write(self, vals):
        res = super().write(vals)
        if 'website_published' in vals:
            for dept in self:
                if dept.website_published and not dept.published_date:
                    dept.published_date = fields.Datetime.now()
                elif not dept.website_published and dept.published_date:
                    dept.published_date = False
        return res
