# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ExamVenue(models.Model):
    _name = 'elearning.exam.venue'
    _description = 'Exam Venue'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char('Venue Name', required=True, tracking=True)
    code = fields.Char('Venue Code', help='Short code for the venue')
    building = fields.Char('Building')
    floor = fields.Char('Floor')
    address = fields.Text('Address')
    college_id = fields.Many2one('elearning.college', string='College', required=True, tracking=True)
    room_ids = fields.One2many('elearning.exam.room', 'venue_id', string='Rooms')
    total_rooms = fields.Integer('Total Rooms', compute='_compute_total_rooms', store=True)
    active = fields.Boolean('Active', default=True)

    @api.depends('room_ids')
    def _compute_total_rooms(self):
        for venue in self:
            venue.total_rooms = len(venue.room_ids.filtered('active'))
    
    def action_view_venue_rooms(self):
        """Action to view rooms of this venue"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('elearning_colleges.action_exam_room')
        action['domain'] = [('venue_id', '=', self.id)]
        action['context'] = {
            'default_venue_id': self.id,
            'search_default_venue_id': self.id,
        }
        action['name'] = f'Rooms - {self.name}'
        return action


class ExamRoom(models.Model):
    _name = 'elearning.exam.room'
    _description = 'Exam Room'
    _order = 'venue_id, name'
    _rec_name = 'display_name'

    name = fields.Char('Room Number/Name', required=True, tracking=True)
    venue_id = fields.Many2one('elearning.exam.venue', string='Venue', required=True, ondelete='cascade')
    college_id = fields.Many2one('elearning.college', string='College', related='venue_id.college_id', store=True, readonly=True)
    capacity = fields.Integer('Seating Capacity', default=30, help='Maximum number of students')
    floor = fields.Char('Floor', related='venue_id.floor', readonly=True)
    building = fields.Char('Building', related='venue_id.building', readonly=True)
    active = fields.Boolean('Active', default=True)
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)

    @api.depends('name', 'venue_id.name')
    def _compute_display_name(self):
        for room in self:
            if room.venue_id:
                room.display_name = f"{room.venue_id.name} - {room.name}"
            else:
                room.display_name = room.name

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result
