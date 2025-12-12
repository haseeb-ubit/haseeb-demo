# -*- coding: utf-8 -*-
from odoo import models


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    
    def action_print_requirements(self):
        """Action to print requirements report"""
        return self.env.ref('elearning_colleges.action_report_department_requirements').report_action(self)
    
    def action_print_semesters(self):
        """Action to print semesters report"""
        return self.env.ref('elearning_colleges.action_report_department_semesters').report_action(self)

