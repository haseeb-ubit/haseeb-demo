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
    total_timetables = fields.Integer('Total Timetables', compute='_compute_total_timetables')
    total_noticeboards = fields.Integer('Total Noticeboards', compute='_compute_total_noticeboards')
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

    def _compute_total_timetables(self):
        for dept in self:
            dept.total_timetables = self.env['elearning.timetable.template'].search_count([
                ('department_id', '=', dept.id)
            ])

    def _compute_total_noticeboards(self):
        for dept in self:
            dept.total_noticeboards = self.env['elearning.noticeboard'].search_count([
                ('department_id', '=', dept.id)
            ])

    def action_view_department_courses(self):
        """Action to view courses of this department"""
        action = self.env['ir.actions.act_window']._for_xml_id('website_slides.slide_channel_action_overview')
        action['domain'] = [('department_id', '=', self.id)]
        action['context'] = {
            'default_department_id': self.id,
            'default_college_id': self.college_id.id if self.college_id else False
        }
        return action
    
    def action_view_department_timetables(self):
        """Action to view timetable templates for this department"""
        action = self.env['ir.actions.act_window']._for_xml_id('elearning_colleges.action_timetable_template')
        action['domain'] = [('department_id', '=', self.id)]
        action['context'] = {
            'default_department_id': self.id,
            'search_default_department_id': self.id,
            'show_semester_only': True,
        }
        action['name'] = f'Timetables - {self.name}'
        return action

    def action_view_department_noticeboards(self):
        """Action to view noticeboards for this department."""
        action = self.env['ir.actions.act_window']._for_xml_id('elearning_colleges.action_noticeboard')
        action['domain'] = [('department_id', '=', self.id)]
        action['context'] = {
            'default_department_id': self.id,
            'search_default_department_id': self.id,
        }
        action['name'] = f'Noticeboard - {self.name}'
        return action
    
    def get_timetable_data_for_report(self):
        """Get timetable data for PDF report (all semesters). This method is called from the report template."""
        # Build timetable data for all semesters - no filtering
        domain = [
            ('department_id', '=', self.id),
            ('website_published', '=', True),
        ]

        entries = self.env['elearning.timetable'].sudo().search(domain, order='semester_id, day_of_week, start_time')
        
        def _float_to_time(time_float):
            """Convert float time to HH:MM format"""
            if not time_float:
                return '00:00'
            hours = int(time_float)
            minutes = int(round((time_float - hours) * 60))
            if minutes == 60:
                hours += 1
                minutes = 0
            return f"{hours:02d}:{minutes:02d}"
        
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
            time_slots = [{'start': _float_to_time(s), 'end': _float_to_time(e), 'start_str': _float_to_time(s), 'end_str': _float_to_time(e)} for s, e in time_slots_raw]
            
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
                    'start': _float_to_time(entry.start_time),
                    'end': _float_to_time(entry.end_time),
                })
            
            sem_record = sem_data['semester_id']
            sem_year   = sem_record.year             if sem_record else 0
            sem_num    = sem_record.semester_number  if sem_record else 0
            semesters_data.append({
                'semester_id':      sem_record,
                'semester_name':    sem_data['semester_name'],
                'year':             sem_year,
                'semester_number':  sem_num,
                'year_label':       f'Year {sem_year}',
                'timetable_grid':   timetable_grid,
                'time_slots':       time_slots,
                'entries':          sem_entries,
                'no_data':          not bool(sem_entries),
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
