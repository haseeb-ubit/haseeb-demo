# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Timetable(models.Model):
    _name = 'elearning.timetable'
    _description = 'Timetable Entry'
    _order = 'day_of_week, start_time'
    _rec_name = 'display_name'

    # Relationships
    timetable_template_id = fields.Many2one('elearning.timetable.template', string='Timetable Template',
                                            ondelete='cascade', tracking=True,
                                            default=lambda self: self.env.context.get('default_timetable_template_id'))
    semester_id = fields.Many2one('elearning.semester', string='Semester', 
                                  compute='_compute_semester_id', store=True, readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', 
                                    related='semester_id.department_id', store=True, readonly=True)
    college_id = fields.Many2one('elearning.college', string='College', 
                                  related='semester_id.college_id', store=True, readonly=True)
    
    # Grid position
    time_slot_index = fields.Integer('Time Slot Index', help='Position of this entry in the grid')
    
    # Timetable fields
    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Day of Week', required=True, tracking=True)
    
    start_time = fields.Float('Start Time', required=True, tracking=True, 
                               help='Time in 24-hour format (e.g., 8.5 for 8:30 AM, 14.25 for 2:15 PM)')
    end_time = fields.Float('End Time', required=True, tracking=True,
                             help='Time in 24-hour format (e.g., 9.5 for 9:30 AM, 15.25 for 3:15 PM)')
    
    course_id = fields.Many2one('slide.channel', string='Course', tracking=True)
    available_course_ids = fields.Many2many(
        'slide.channel',
        compute='_compute_available_course_ids',
        string='Available Courses',
        help='Courses allowed for this timetable entry based on selected semester.'
    )
    room = fields.Char('Room', tracking=True)
    teacher_id = fields.Many2one('res.users', string='Teacher', tracking=True)
    
    # Website publishing
    website_published = fields.Boolean('Published on Website', default=False, tracking=True)
    published_date = fields.Datetime('Published On', readonly=True)
    
    # Computed fields
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    time_display = fields.Char('Time', compute='_compute_time_display', store=True)
    
    @api.depends('timetable_template_id')
    def _compute_semester_id(self):
        """Compute semester from template"""
        for record in self:
            if record.timetable_template_id:
                record.semester_id = record.timetable_template_id.semester_id
            elif not record.semester_id:
                # Fallback for entries created without template
                semester_id = self.env.context.get('default_semester_id')
                if semester_id:
                    record.semester_id = semester_id

    @api.depends(
        'timetable_template_id',
        'timetable_template_id.semester_id',
        'timetable_template_id.semester_id.year',
        'timetable_template_id.semester_id.semester_number',
        'timetable_template_id.semester_id.department_id',
    )
    def _compute_available_course_ids(self):
        """Compute courses available for this entry from same department/year/semester."""
        Semester = self.env['elearning.semester']
        for record in self:
            template = record.timetable_template_id
            semester = template.semester_id if template else False
            if not semester:
                record.available_course_ids = [(5, 0, 0)]
                continue

            semester_records = Semester.search([
                ('department_id', '=', semester.department_id.id),
                ('year', '=', semester.year),
                ('semester_number', '=', semester.semester_number),
            ])
            course_ids = [cid for cid in semester_records.mapped('course_id').ids if cid]
            record.available_course_ids = [(6, 0, course_ids)] if course_ids else [(5, 0, 0)]
    
    def _float_to_time(self, float_time):
        """Convert float time to HH:MM format"""
        if not float_time:
            return ''
        hours = int(float_time)
        minutes = int(round((float_time - hours) * 60))
        if minutes == 60:
            hours += 1
            minutes = 0
        return f"{hours:02d}:{minutes:02d}"
    
    @api.depends('day_of_week', 'start_time', 'end_time', 'course_id.name')
    def _compute_display_name(self):
        """Compute display name from day, time, and course"""
        for record in self:
            day_name = dict(self._fields['day_of_week'].selection).get(record.day_of_week, '')
            start_str = record._float_to_time(record.start_time) if record.start_time else ''
            end_str = record._float_to_time(record.end_time) if record.end_time else ''
            course_name = record.course_id.name if record.course_id else ''
            
            if day_name and start_str and end_str:
                record.display_name = f"{day_name} {start_str}-{end_str} - {course_name}" if course_name else f"{day_name} {start_str}-{end_str}"
            elif day_name and course_name:
                record.display_name = f"{day_name} - {course_name}"
            else:
                record.display_name = f"Timetable {record.id}" if record.id else "New Timetable"
    
    @api.depends('start_time', 'end_time')
    def _compute_time_display(self):
        """Compute time display string"""
        for record in self:
            if record.start_time and record.end_time:
                start_str = record._float_to_time(record.start_time)
                end_str = record._float_to_time(record.end_time)
                record.time_display = f"{start_str} - {end_str}"
            else:
                record.time_display = ''
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-populate fields and set published_date"""
        for vals in vals_list:
            # Auto-populate template_id from context if not provided
            if not vals.get('timetable_template_id'):
                template_id = self.env.context.get('default_timetable_template_id')
                if template_id:
                    vals['timetable_template_id'] = template_id
            
            # Auto-populate semester_id from template if not set
            if not vals.get('semester_id') and vals.get('timetable_template_id'):
                template = self.env['elearning.timetable.template'].browse(vals['timetable_template_id'])
                if template.semester_id:
                    vals['semester_id'] = template.semester_id.id
            
            # Set published_date if publishing
            if vals.get('website_published') and not vals.get('published_date'):
                vals['published_date'] = fields.Datetime.now()
        
        records = super().create(vals_list)
        return records
    
    def write(self, vals):
        """Handle published_date updates"""
        if 'website_published' in vals:
            for record in self:
                if vals['website_published'] and not record.published_date:
                    vals['published_date'] = fields.Datetime.now()
                elif not vals['website_published'] and record.published_date:
                    vals['published_date'] = False
        return super().write(vals)
    
    @api.constrains('start_time', 'end_time')
    def _check_time_range(self):
        """Ensure end_time is after start_time"""
        for record in self:
            if record.start_time and record.end_time:
                if record.end_time <= record.start_time:
                    raise ValidationError('End time must be after start time.')
    
    @api.onchange('timetable_template_id')
    def _onchange_timetable_template_id(self):
        """Update course domain based on template semester courses."""
        self._compute_available_course_ids()
        return {'domain': {'course_id': [('id', 'in', self.available_course_ids.ids)]}}
    
    def toggle_website_published(self):
        """Toggle website published status"""
        for record in self:
            record.website_published = not record.website_published
        return True
