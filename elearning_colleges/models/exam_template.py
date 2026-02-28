# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class ExamOffDate(models.Model):
    _name = 'elearning.exam.offdate'
    _description = 'Exam Off Date'
    _order = 'off_date'
    _rec_name = 'off_date'

    exam_template_id = fields.Many2one('elearning.exam.template', string='Exam Template', 
                                       required=True, ondelete='cascade')
    off_date = fields.Date('Off Date', required=True)
    
    @api.constrains('off_date', 'exam_template_id')
    def _check_off_date_range(self):
        for record in self:
            if record.exam_template_id and record.off_date:
                template = record.exam_template_id
                if template.start_date and template.end_date:
                    if not (template.start_date <= record.off_date <= template.end_date):
                        raise ValidationError(
                            f"Off date {record.off_date} must be between start date ({template.start_date}) "
                            f"and end date ({template.end_date})."
                        )


class ExamTemplate(models.Model):
    _name = 'elearning.exam.template'
    _description = 'Exam Schedule Template'
    _order = 'start_date desc, name'
    _rec_name = 'name'

    name = fields.Char('Exam Name', required=True, tracking=True)
    college_id = fields.Many2one('elearning.college', string='College', required=True, tracking=True)
    exam_type = fields.Selection([
        ('midterm', 'Midterm Examination'),
        ('final', 'Final Examination'),
        ('supplementary', 'Supplementary Examination'),
        ('other', 'Other'),
    ], string='Exam Type', required=True, default='midterm', tracking=True)
    
    # Date and Time Configuration
    start_date = fields.Date('Start Date', required=True, tracking=True)
    end_date = fields.Date('End Date', required=True, tracking=True)
    daily_start_time = fields.Char('Daily Start Time', required=True, default='08:00', 
                                   help='Format: HH:MM (e.g., 08:00)')
    daily_end_time = fields.Char('Daily End Time', required=True, default='17:00',
                                 help='Format: HH:MM (e.g., 17:00)')
    shift_duration = fields.Char('Shift Duration', required=True, default='02:00',
                                 help='Format: HH:MM (e.g., 02:00 for 2 hours)')
    break_duration = fields.Char('Break Duration', required=True, default='00:30',
                                 help='Format: HH:MM (e.g., 00:30 for 30 minutes)')
    off_date_ids = fields.One2many('elearning.exam.offdate', 'exam_template_id', 
                                    string='Off Dates',
                                    help='Specific dates to exclude from exam schedule')
    
    # Status and Publishing
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', tracking=True)
    website_published = fields.Boolean('Published on Website', default=False, tracking=True)
    published_date = fields.Datetime('Published On', readonly=True)
    
    # Computed Fields
    grid_generated = fields.Boolean('Exam Entries Generated', default=False, readonly=True)
    total_shifts_per_day = fields.Integer('Shifts Per Day', compute='_compute_shifts_per_day', store=True)
    total_days = fields.Integer('Total Days', compute='_compute_total_days', store=True)
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    
    # Relationships
    exam_entry_ids = fields.One2many('elearning.exam', 'exam_template_id', string='Exam Entries')
    
    @api.depends('name', 'exam_type', 'start_date')
    def _compute_display_name(self):
        for template in self:
            if template.name:
                template.display_name = template.name
            else:
                template.display_name = f"Exam Template {template.id}" if template.id else "New Exam Template"
    
    @api.depends('daily_start_time', 'daily_end_time', 'shift_duration', 'break_duration')
    def _compute_shifts_per_day(self):
        for template in self:
            if template.daily_start_time and template.daily_end_time and template.shift_duration and template.break_duration:
                shifts = self._calculate_shifts_per_day(
                    template.daily_start_time,
                    template.daily_end_time,
                    template.shift_duration,
                    template.break_duration
                )
                template.total_shifts_per_day = shifts
            else:
                template.total_shifts_per_day = 0
    
    @api.depends('start_date', 'end_date', 'off_date_ids')
    def _compute_total_days(self):
        for template in self:
            if template.start_date and template.end_date:
                days = self._calculate_exam_days(template.start_date, template.end_date, template.off_date_ids)
                template.total_days = days
            else:
                template.total_days = 0
    
    def _time_to_float(self, time_str):
        """Convert HH:MM string to float hours"""
        if not time_str or ':' not in time_str:
            return 0.0
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours + (minutes / 60.0)
        except (ValueError, IndexError):
            return 0.0
    
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
    
    def _is_valid_time_format(self, time_str):
        """Validate HH:MM format"""
        if not time_str:
            return False
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hours = int(parts[0])
            minutes = int(parts[1])
            return 0 <= hours <= 23 and 0 <= minutes <= 59
        except (ValueError, IndexError):
            return False
    
    def _calculate_shifts_per_day(self, start_time, end_time, shift_duration, break_duration):
        """Calculate number of shifts per day"""
        start_float = self._time_to_float(start_time)
        end_float = self._time_to_float(end_time)
        shift_float = self._time_to_float(shift_duration)
        break_float = self._time_to_float(break_duration)
        
        if shift_float <= 0:
            return 0
        
        shifts = 0
        current_time = start_float
        while current_time + shift_float <= end_float:
            shifts += 1
            current_time += shift_float + break_float
        
        return shifts
    
    def _calculate_exam_days(self, start_date, end_date, off_dates):
        """Calculate total exam days excluding off dates"""
        if not start_date or not end_date:
            return 0
        
        off_date_set = set(off_dates.mapped('off_date')) if off_dates else set()
        current_date = start_date
        days_count = 0
        
        while current_date <= end_date:
            if current_date not in off_date_set:
                days_count += 1
            current_date += timedelta(days=1)
        
        return days_count
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for template in self:
            if template.start_date and template.end_date:
                if template.start_date > template.end_date:
                    raise ValidationError("Start date must be before or equal to end date.")
    
    @api.constrains('daily_start_time', 'daily_end_time', 'shift_duration', 'break_duration')
    def _check_times(self):
        for template in self:
            if not all([template.daily_start_time, template.daily_end_time, 
                       template.shift_duration, template.break_duration]):
                continue
            
            if not all([self._is_valid_time_format(template.daily_start_time),
                       self._is_valid_time_format(template.daily_end_time),
                       self._is_valid_time_format(template.shift_duration),
                       self._is_valid_time_format(template.break_duration)]):
                raise ValidationError("Time fields must be in HH:MM format (e.g., 08:00).")
            
            start_float = self._time_to_float(template.daily_start_time)
            end_float = self._time_to_float(template.daily_end_time)
            
            if start_float >= end_float:
                raise ValidationError("Daily start time must be before daily end time.")
    
    def action_generate_grid(self):
        """Generate exam entries grid based on date range and shifts"""
        self.ensure_one()
        
        if not all([self.start_date, self.end_date, self.daily_start_time, 
                   self.daily_end_time, self.shift_duration, self.break_duration]):
            raise UserError("Please fill all date and time fields before generating the grid.")
        
        # Clear existing entries if any
        self.exam_entry_ids.unlink()
        
        # Calculate shifts
        start_float = self._time_to_float(self.daily_start_time)
        shift_float = self._time_to_float(self.shift_duration)
        break_float = self._time_to_float(self.break_duration)
        
        off_date_set = set(self.off_date_ids.mapped('off_date')) if self.off_date_ids else set()
        
        # Generate entries for each day
        current_date = self.start_date
        shift_number = 1
        
        entries_to_create = []
        
        while current_date <= self.end_date:
            # Skip off dates
            if current_date not in off_date_set:
                current_time = start_float
                day_shift = 1
                
                while current_time + shift_float <= self._time_to_float(self.daily_end_time):
                    end_time_float = current_time + shift_float
                    
                    entries_to_create.append({
                        'exam_template_id': self.id,
                        'exam_date': current_date,
                        'shift_number': day_shift,
                        'start_time': self._float_to_time(current_time),
                        'end_time': self._float_to_time(end_time_float),
                        'state': 'scheduled',
                        'website_published': bool(self.website_published),
                    })
                    
                    current_time += shift_float + break_float
                    day_shift += 1
                    shift_number += 1
            
            current_date += timedelta(days=1)
        
        # Create all entries
        if entries_to_create:
            self.env['elearning.exam'].create(entries_to_create)
        
        self.grid_generated = True
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exam Schedule',
            'res_model': 'elearning.exam.template',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_update_grid(self):
        """Update exam entries while preserving mapped course/department/semester/room/invigilator data."""
        self.ensure_one()
        
        if not all([self.start_date, self.end_date, self.daily_start_time, 
                   self.daily_end_time, self.shift_duration, self.break_duration]):
            raise UserError("Please fill all date and time fields before updating the exam entries.")
        
        if not self.exam_entry_ids:
            return self.action_generate_grid()
        
        # Store existing entries data by date and shift
        existing_data = {}
        for entry in self.exam_entry_ids:
            key = (entry.exam_date, entry.shift_number)
            existing_data[key] = {
                'department_id': entry.department_id.id if entry.department_id else False,
                'semester_id': entry.semester_id.id if entry.semester_id else False,
                'course_id': entry.course_id.id if entry.course_id else False,
                'room': entry.room or '',
                'invigilator_id': entry.invigilator_id.id if entry.invigilator_id else False,
            }
        
        # Delete existing entries
        self.exam_entry_ids.unlink()
        
        # Calculate shifts
        start_float = self._time_to_float(self.daily_start_time)
        shift_float = self._time_to_float(self.shift_duration)
        break_float = self._time_to_float(self.break_duration)
        
        off_date_set = set(self.off_date_ids.mapped('off_date')) if self.off_date_ids else set()
        
        # Generate entries for each day
        current_date = self.start_date
        shift_number = 1
        
        entries_to_create = []
        
        while current_date <= self.end_date:
            # Skip off dates
            if current_date not in off_date_set:
                current_time = start_float
                day_shift = 1
                
                while current_time + shift_float <= self._time_to_float(self.daily_end_time):
                    end_time_float = current_time + shift_float
                    
                    # Get existing data if available
                    key = (current_date, day_shift)
                    existing = existing_data.get(key, {})
                    
                    entries_to_create.append({
                        'exam_template_id': self.id,
                        'exam_date': current_date,
                        'shift_number': day_shift,
                        'start_time': self._float_to_time(current_time),
                        'end_time': self._float_to_time(end_time_float),
                        'state': 'scheduled',
                        'website_published': bool(self.website_published),
                        'department_id': existing.get('department_id', False),
                        'semester_id': existing.get('semester_id', False),
                        'course_id': existing.get('course_id', False),
                        'room': existing.get('room', ''),
                        'invigilator_id': existing.get('invigilator_id', False),
                    })
                    
                    current_time += shift_float + break_float
                    day_shift += 1
                    shift_number += 1
            
            current_date += timedelta(days=1)
        
        # Create all entries
        if entries_to_create:
            self.env['elearning.exam'].create(entries_to_create)
        
        self.grid_generated = True
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exam Schedule',
            'res_model': 'elearning.exam.template',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_clear_grid(self):
        """Clear all exam entries"""
        self.ensure_one()
        if self.exam_entry_ids:
            self.exam_entry_ids.unlink()
        self.grid_generated = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exam Schedule',
            'res_model': 'elearning.exam.template',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def toggle_website_published(self):
        """Toggle website published status"""
        self.ensure_one()
        self.website_published = not self.website_published
        if self.website_published:
            self.published_date = fields.Datetime.now()
            # Propagate to entries
            self.exam_entry_ids.write({'website_published': True})
        else:
            self.exam_entry_ids.write({'website_published': False})
        return True
