# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class TimetableOffDay(models.Model):
    _name = 'elearning.timetable.offday'
    _description = 'Timetable Off Day'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    code = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], required=True)
    sequence = fields.Integer(default=10)


class TimetableTemplate(models.Model):
    _name = 'elearning.timetable.template'
    _description = 'Timetable Template'
    _rec_name = 'display_name'
    _order = 'semester_id'

    # Relationships
    semester_id = fields.Many2one('elearning.semester.slot', string='Semester', required=True, 
                                  ondelete='cascade', tracking=True,
                                  default=lambda self: self.env.context.get('default_semester_id'))
    department_id = fields.Many2one('hr.department', string='Department',
                                    related='semester_id.department_id', store=True, readonly=True)
    college_id = fields.Many2one('elearning.college', string='College',
                                  related='semester_id.college_id', store=True, readonly=True)
    
    # Global timetable settings
    start_time = fields.Float('Start Time', required=True, tracking=True,
                              help='Time in 24-hour format (e.g., 8.5 for 8:30 AM)')
    end_time = fields.Float('End Time', required=True, tracking=True,
                            help='Time in 24-hour format (e.g., 17.42 for 5:25 PM)')
    class_duration = fields.Char('Class Duration', required=True, default='00:55', tracking=True,
                                 help='Duration of each class in HH:MM format (e.g., 00:55 for 55 minutes)')
    break_duration = fields.Char('Break Duration', default='00:05', tracking=True,
                                 help='Break between classes in HH:MM format (e.g., 00:05 for 5 minutes)')
    
    off_day_ids = fields.Many2many(
        'elearning.timetable.offday',
        'elearning_timetable_template_offday_rel',
        'template_id',
        'offday_id',
        string='Off Days',
        help='Selected days will be excluded from timetable generation.'
    )
    
    # Computed field for semester courses (stored for domain usage)
    semester_course_ids = fields.Many2many('slide.channel', compute='_compute_semester_course_ids', store=True, string='Semester Courses')
    
    @api.depends('semester_id', 'semester_id.year', 'semester_id.semester_number', 'semester_id.department_id')
    def _compute_semester_course_ids(self):
        """Compute all courses for this semester (year + semester_number in same department)"""
        for record in self:
            if record.semester_id:
                # Get all semester records with same year, semester_number, and department
                semester_records = self.env['elearning.semester'].search([
                    ('year', '=', record.semester_id.year),
                    ('semester_number', '=', record.semester_id.semester_number),
                    ('department_id', '=', record.semester_id.department_id.id),
                ])
                # Get all course_ids from those semesters (filter out False/None)
                course_ids = [cid for cid in semester_records.mapped('course_id').ids if cid]
                if course_ids:
                    record.semester_course_ids = [(6, 0, course_ids)]
                else:
                    # If no courses, set to empty but valid Many2many
                    record.semester_course_ids = [(5, 0, 0)]
            else:
                record.semester_course_ids = [(5, 0, 0)]
    
    # Website publishing
    website_published = fields.Boolean('Published on Website', default=False, tracking=True)
    published_date = fields.Datetime('Published On', readonly=True)
    
    # Computed fields
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    timetable_entry_ids = fields.One2many('elearning.timetable', 'timetable_template_id', 
                                         string='Timetable Entries')
    total_entries = fields.Integer('Total Entries', compute='_compute_total_entries', store=True)
    grid_generated = fields.Boolean('Grid Generated', compute='_compute_grid_generated', store=True)
    
    @api.depends('semester_id')
    def _compute_display_name(self):
        """Compute display name from semester"""
        for record in self:
            if record.semester_id:
                record.display_name = f"Timetable - {record.semester_id.display_name}"
            else:
                record.display_name = f"Timetable Template {record.id}" if record.id else "New Timetable Template"
    
    @api.depends('timetable_entry_ids')
    def _compute_total_entries(self):
        """Compute total timetable entries"""
        for record in self:
            record.total_entries = len(record.timetable_entry_ids)
    
    @api.depends('timetable_entry_ids')
    def _compute_grid_generated(self):
        """Check if grid has been generated"""
        for record in self:
            record.grid_generated = len(record.timetable_entry_ids) > 0
    
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
    
    def _time_to_float(self, time_str):
        """Convert HH:MM format to float hours"""
        if not time_str:
            return 0.0
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours + (minutes / 60.0)
        except (ValueError, AttributeError):
            pass
        return 0.0
    
    def _generate_time_slots(self):
        """Generate time slots based on start_time, end_time, class_duration, and break_duration"""
        self.ensure_one()
        time_slots = []
        current_time = self.start_time
        
        # Convert class_duration and break_duration from HH:MM to float
        class_duration_float = self._time_to_float(self.class_duration)
        break_duration_float = self._time_to_float(self.break_duration)
        
        while current_time < self.end_time:
            slot_start = current_time
            slot_end = min(current_time + class_duration_float, self.end_time)
            
            if slot_end > self.end_time:
                break
            
            time_slots.append({
                'start': slot_start,
                'end': slot_end,
                'start_str': self._float_to_time(slot_start),
                'end_str': self._float_to_time(slot_end),
            })
            
            # Move to next slot (class duration + break)
            current_time = slot_end + break_duration_float
        
        return time_slots
    
    def action_generate_grid(self):
        """Generate timetable entries for all active days and time slots."""
        self.ensure_one()
        
        if not self.semester_id:
            raise UserError('Please select a semester first.')
        
        # Delete existing entries if any
        self.timetable_entry_ids.unlink()
        
        # Generate time slots
        time_slots = self._generate_time_slots()
        
        if not time_slots:
            raise UserError('No time slots can be generated with the current settings.')
        
        # Days of week: Monday (0) to Sunday (6)
        day_keys = ['0', '1', '2', '3', '4', '5', '6']
        
        # Selected off-day codes to skip.
        off_days_list = set(self.off_day_ids.mapped('code'))
        
        # Create entries for each day/time slot except off days.
        entries_to_create = []
        for day_key in day_keys:
            # Skip off days
            if day_key in off_days_list:
                continue
                
            for slot_idx, slot in enumerate(time_slots):
                entries_to_create.append({
                    'timetable_template_id': self.id,
                    'semester_id': self.semester_id.id,
                    'day_of_week': day_key,
                    'start_time': slot['start'],
                    'end_time': slot['end'],
                    'time_slot_index': slot_idx,
                    'website_published': bool(self.website_published),
                    'published_date': fields.Datetime.now() if self.website_published else False,
                })
        
        # Create all entries
        if entries_to_create:
            self.env['elearning.timetable'].create(entries_to_create)
        
        # Reload current form so the newly generated entries are visible immediately.
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'elearning.timetable.template',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': {'show_semester_only': True},
        }
    
    def action_update_grid(self):
        """Update timetable entries while preserving mapped course/teacher/room data."""
        self.ensure_one()
        
        if not self.semester_id:
            raise UserError('Please select a semester first.')
        
        if not self.timetable_entry_ids:
            return self.action_generate_grid()
        
        # Store existing entries data by day and time slot
        existing_data = {}
        for entry in self.timetable_entry_ids:
            key = (entry.day_of_week, entry.time_slot_index)
            existing_data[key] = {
                'course_id': entry.course_id.id if entry.course_id else False,
                'teacher_id': entry.teacher_id.id if entry.teacher_id else False,
                'room': entry.room or '',
            }
        
        # Delete existing entries
        self.timetable_entry_ids.unlink()
        
        # Generate new time slots
        time_slots = self._generate_time_slots()
        
        if not time_slots:
            raise UserError('No time slots can be generated with the current settings.')
        
        # Days of week: Monday (0) to Sunday (6)
        day_keys = ['0', '1', '2', '3', '4', '5', '6']
        
        # Selected off-day codes to skip.
        off_days_list = set(self.off_day_ids.mapped('code'))
        
        # Create entries for each day and time slot (excluding off days)
        entries_to_create = []
        for day_key in day_keys:
            # Skip off days
            if day_key in off_days_list:
                continue
                
            for slot_idx, slot in enumerate(time_slots):
                # Get existing data if available
                key = (day_key, slot_idx)
                existing = existing_data.get(key, {})
                
                entries_to_create.append({
                    'timetable_template_id': self.id,
                    'semester_id': self.semester_id.id,
                    'day_of_week': day_key,
                    'start_time': slot['start'],
                    'end_time': slot['end'],
                    'time_slot_index': slot_idx,
                    'course_id': existing.get('course_id', False),
                    'teacher_id': existing.get('teacher_id', False),
                    'room': existing.get('room', ''),
                    'website_published': bool(self.website_published),
                    'published_date': fields.Datetime.now() if self.website_published else False,
                })
        
        # Create all entries
        if entries_to_create:
            self.env['elearning.timetable'].create(entries_to_create)
        
        # Return form view reload action
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'elearning.timetable.template',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': {'show_semester_only': True},
        }
    
    def action_clear_grid(self):
        """Clear all generated timetable entries."""
        self.ensure_one()
        self.timetable_entry_ids.unlink()
        # Return form view reload action
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'elearning.timetable.template',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': {'show_semester_only': True},
        }
    
    @api.constrains('semester_id')
    def _check_unique_semester(self):
        """Ensure one template per semester"""
        for record in self:
            existing = self.search([
                ('semester_id', '=', record.semester_id.id),
                ('id', '!=', record.id)
            ], limit=1)
            if existing:
                raise ValidationError(f'This semester already has a timetable template. Please use the existing template or delete it first.')
    
    @api.constrains('start_time', 'end_time', 'class_duration', 'break_duration')
    def _check_time_settings(self):
        """Validate time settings"""
        for record in self:
            if record.end_time <= record.start_time:
                raise ValidationError('End time must be after start time.')
            
            class_duration_float = record._time_to_float(record.class_duration)
            if class_duration_float <= 0:
                raise ValidationError('Class duration must be greater than 0.')
            if class_duration_float > (record.end_time - record.start_time):
                raise ValidationError('Class duration cannot be greater than the total time range.')
            
            # Validate time format
            if record.class_duration and not self._is_valid_time_format(record.class_duration):
                raise ValidationError('Class duration must be in HH:MM format (e.g., 00:55).')
            if record.break_duration and not self._is_valid_time_format(record.break_duration):
                raise ValidationError('Break duration must be in HH:MM format (e.g., 00:05).')
    
    def _is_valid_time_format(self, time_str):
        """Validate time format HH:MM"""
        if not time_str:
            return True
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                return 0 <= hours < 24 and 0 <= minutes < 60
        except (ValueError, AttributeError):
            pass
        return False
    
    @api.onchange('department_id')
    def _onchange_department_id(self):
        """Update semester domain when department changes"""
        return self._get_semester_domain()
    
    @api.onchange('semester_id')
    def _onchange_semester_id(self):
        """Update semester domain and validate"""
        if self.semester_id:
            # Check if this semester already has a template
            existing = self.search([
                ('semester_id', '=', self.semester_id.id),
                ('id', '!=', self.id)
            ], limit=1)
            if existing:
                return {
                    'warning': {
                        'title': 'Semester Already Has Template',
                        'message': f'This semester already has a timetable template. Please select a different semester or use the existing template.'
                    }
                }
        return self._get_semester_domain()
    
    def _get_semester_domain(self):
        """Get semester domain based on department"""
        domain = [('department_id', '!=', False)]
        
        # Filter by department if set
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        elif self.env.context.get('default_department_id'):
            domain.append(('department_id', '=', self.env.context.get('default_department_id')))
        
        # Exclude semesters that already have templates (except current one)
        existing_templates = self.search([])
        if existing_templates:
            semester_ids_with_templates = existing_templates.filtered(
                lambda t: t.id != self.id
            ).mapped('semester_id').ids
            if semester_ids_with_templates:
                domain.append(('id', 'not in', semester_ids_with_templates))
        
        return {'domain': {'semester_id': domain}}
    
    @api.model
    def _get_available_semester_domain(self, department_id=None):
        """Get domain for available semesters (those without templates)"""
        domain = [('department_id', '!=', False)]
        if department_id:
            domain.append(('department_id', '=', department_id))
        # Exclude semesters that already have templates
        existing_templates = self.search([])
        if existing_templates:
            semester_ids_with_templates = existing_templates.mapped('semester_id').ids
            domain.append(('id', 'not in', semester_ids_with_templates))
        return domain
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-populate fields and set published_date"""
        for vals in vals_list:
            # Auto-populate semester_id from context if not provided
            if not vals.get('semester_id'):
                semester_id = self.env.context.get('default_semester_id')
                if semester_id:
                    vals['semester_id'] = semester_id
            
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
        res = super().write(vals)
        if 'website_published' in vals:
            for record in self:
                record.timetable_entry_ids.write({
                    'website_published': bool(record.website_published),
                    'published_date': fields.Datetime.now() if record.website_published else False,
                })
        return res
    
    def toggle_website_published(self):
        """Toggle website published status"""
        for record in self:
            new_state = not record.website_published
            record.website_published = new_state
            record.published_date = fields.Datetime.now() if new_state else False
            record.timetable_entry_ids.write({
                'website_published': bool(new_state),
                'published_date': fields.Datetime.now() if new_state else False,
            })
        return True
