# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class ExamBulkAssign(models.TransientModel):
    _name = 'elearning.exam.bulk.assign'
    _description = 'Bulk Assign Room/Invigilator to Exams'

    room = fields.Char('Room', help='Room number or name')
    invigilator_id = fields.Many2one('res.users', string='Invigilator')
    exam_ids = fields.Many2many('elearning.exam', string='Exam Entries', required=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            res['exam_ids'] = [(6, 0, active_ids)]
        return res
    
    def action_assign(self):
        """Assign room/invigilator to selected exams"""
        if not self.exam_ids:
            raise UserError("Please select at least one exam entry.")
        
        if not self.room and not self.invigilator_id:
            raise UserError("Please enter a room or select an invigilator to assign.")
        
        # Perform assignment
        vals = {}
        if self.room:
            vals['room'] = self.room
        if self.invigilator_id:
            vals['invigilator_id'] = self.invigilator_id.id
        
        if vals:
            self.exam_ids.write(vals)
        
        return {'type': 'ir.actions.act_window_close'}
