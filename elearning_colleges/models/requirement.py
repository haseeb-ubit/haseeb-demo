# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class Requirement(models.Model):
    _name = 'elearning.requirement'
    _description = 'Academic Requirement'
    _order = 'id'
    _rec_name = 'display_name'

    name = fields.Char('Requirement Name', compute='_compute_display_name', store=True)
    description = fields.Text('Description')
    requirement_type = fields.Selection([
        ('faculty', 'Faculty Requirements'),
        ('department', 'Department Requirements'),
        ('program', 'Program Requirements'),
        ('elective', 'Elective Requirements'),
        ('university', 'University Requirements'),
    ], string='Requirement Type', required=True, tracking=True)
    
    # Relationships
    department_id = fields.Many2one('hr.department', string='Department', required=True, tracking=True)
    college_id = fields.Many2one('elearning.college', string='College', related='department_id.college_id', store=True, readonly=True)
    course_id = fields.Many2one('slide.channel', string='Course', required=True, tracking=True)
    
    # Auto-populated fields from course
    course_credit_hours = fields.Selection([
        ('1', '1 Credit Hour'),
        ('2', '2 Credit Hours'),
        ('3', '3 Credit Hours'),
        ('4', '4 Credit Hours'),
        ('5', '5 Credit Hours'),
    ], string='Credit Hours', related='course_id.credit_hours', readonly=True)
    course_code = fields.Char('Course Code', related='course_id.course_code', readonly=True)
    course_prerequisite = fields.Char('Prerequisites', compute='_compute_course_prerequisite', store=True, readonly=True)
    
    # Additional fields
    credit_hours = fields.Float('Credit Hours', default=0.0)
    
    # Computed fields
    total_courses = fields.Integer('Total Courses', compute='_compute_total_courses', store=True)
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    
    @api.depends('course_id.prerequisite_channel_ids')
    def _compute_course_prerequisite(self):
        """Compute prerequisites from course prerequisite_channel_ids Many2many field"""
        for req in self:
            if req.course_id and req.course_id.prerequisite_channel_ids:
                # Format as comma-separated course names
                prereq_names = [prereq.name for prereq in req.course_id.prerequisite_channel_ids]
                req.course_prerequisite = ', '.join(prereq_names)
            else:
                req.course_prerequisite = '-'
    
    @api.depends('course_id.name', 'requirement_type')
    def _compute_display_name(self):
        """Auto-generate name and display_name from course"""
        for req in self:
            if req.course_id:
                req.name = req.course_id.name
                req.display_name = f"{req.course_id.name} ({req.requirement_type})"
            else:
                req.name = f"Requirement {req.id}" if req.id else "New Requirement"
                req.display_name = req.name
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-populate missing fields from context or related fields.
        With @api.model_create_multi, vals_list is a list of dicts; iterate over each.
        """
        for vals in vals_list:
            # Set requirement_type from context if not provided
            if not vals.get('requirement_type'):
                req_type = self.env.context.get('default_requirement_type')
                if req_type:
                    vals['requirement_type'] = req_type

            # Auto-populate department_id based on the calling context
            if not vals.get('department_id'):
                if self.env.context.get('default_department_id'):
                    vals['department_id'] = self.env.context.get('default_department_id')
                elif self.env.context.get('active_model') == 'hr.department':
                    dept_id = self.env.context.get('active_id')
                    if dept_id:
                        vals['department_id'] = dept_id

            # Auto-populate name from course_id if course is provided
            if vals.get('course_id'):
                course = self.env['slide.channel'].browse(vals['course_id'])
                if course:
                    vals['name'] = course.name
            elif 'name' not in vals:
                vals['name'] = f"Requirement {vals.get('requirement_type', 'New')}"

        return super(Requirement, self).create(vals_list)
    
    @api.depends('department_id')
    def _compute_total_courses(self):
        for req in self:
            req.total_courses = 0
    
    @api.constrains('course_id', 'department_id')
    def _check_course_unique_in_requirements(self):
        """Ensure a course is only added once across all requirement types for a department"""
        for req in self:
            if req.course_id and req.department_id:
                # Check if this course already exists in any requirement for this department
                existing_req = self.search([
                    ('course_id', '=', req.course_id.id),
                    ('department_id', '=', req.department_id.id),
                    ('id', '!=', req.id)
                ], limit=1)
                if existing_req:
                    raise ValidationError(
                        f"Course '{req.course_id.name}' is already added in '{existing_req.requirement_type}' requirements for this department. "
                        f"A course can only be added once across all requirement types."
                    )


class Semester(models.Model):
    _name = 'elearning.semester'
    _description = 'Academic Semester'
    _order = 'year, semester_number'
    _rec_name = 'display_name'

    name = fields.Char('Semester Name', compute='_compute_display_name', store=True)
    year = fields.Integer('Year', required=True, tracking=True, default=lambda self: self.env.context.get('default_year'))
    semester_number = fields.Integer('Semester Number', required=True, tracking=True, default=lambda self: self.env.context.get('default_semester_number'))
    description = fields.Text('Description')
    
    # Relationships
    department_id = fields.Many2one('hr.department', string='Department', required=True, tracking=True, default=lambda self: self.env.context.get('default_department_id'))
    college_id = fields.Many2one('elearning.college', string='College', related='department_id.college_id', store=True, readonly=True)
    course_id = fields.Many2one('slide.channel', string='Course', required=True, tracking=True)
    
    # Auto-populated fields from course
    course_credit_hours = fields.Selection([
        ('1', '1 Credit Hour'),
        ('2', '2 Credit Hours'),
        ('3', '3 Credit Hours'),
        ('4', '4 Credit Hours'),
        ('5', '5 Credit Hours'),
    ], string='Credit Hours', related='course_id.credit_hours', readonly=True)
    course_code = fields.Char('Course Code', related='course_id.course_code', readonly=True)
    course_prerequisite = fields.Char('Prerequisites', compute='_compute_course_prerequisite', store=True, readonly=True)

    @api.depends('course_id.prerequisite_channel_ids')
    def _compute_course_prerequisite(self):
        """Compute prerequisites from course prerequisite_channel_ids Many2many field"""
        for semester in self:
            if semester.course_id and semester.course_id.prerequisite_channel_ids:
                # Format as comma-separated course names
                prereq_names = [prereq.name for prereq in semester.course_id.prerequisite_channel_ids]
                semester.course_prerequisite = ', '.join(prereq_names)
            else:
                semester.course_prerequisite = '-'

    # Semester dates
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    
    # Additional fields
    is_active = fields.Boolean('Active Semester', default=False)
    total_courses = fields.Integer('Total Courses', compute='_compute_total_courses', store=True)
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    
    @api.depends('year', 'semester_number')
    def _compute_display_name(self):
        """Auto-generate name and display_name from year and semester (without course name)"""
        for semester in self:
            semester_name = f"Year {semester.year} Semester {semester.semester_number}"
            semester.name = semester_name
            semester.display_name = f"Y{semester.year}S{semester.semester_number}"
    
    def name_get(self):
        """Always show compact semester labels like Y1S1."""
        result = []
        for record in self:
            name = f"Y{record.year}S{record.semester_number}"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Search semesters by compact label and return compact labels only."""
        args = args or []
        records = self.search(args, limit=limit)
        if name:
            needle = (name or '').lower().replace(' ', '')
            records = records.filtered(
                lambda s: needle in f"y{s.year}s{s.semester_number}".lower()
                or needle in (s.display_name or '').lower().replace(' ', '')
            )
        return records.name_get()
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-populate missing fields from context"""
        # Set year and semester_number from context if not provided
        if 'year' not in vals_list or not vals_list.get('year'):
            year = self.env.context.get('default_year')
            if year:
                vals_list['year'] = year
        
        if 'semester_number' not in vals_list or not vals_list.get('semester_number'):
            semester_num = self.env.context.get('default_semester_number')
            if semester_num:
                vals_list['semester_number'] = semester_num
        
        # Auto-populate department_id based on the calling context
        if 'department_id' not in vals_list or not vals_list.get('department_id'):
            # Try to get from context first
            if self.env.context.get('default_department_id'):
                vals_list['department_id'] = self.env.context.get('default_department_id')
            # If context doesn't have it, infer from the active record
            elif self.env.context.get('active_model') == 'hr.department':
                dept_id = self.env.context.get('active_id')
                if dept_id:
                    vals_list['department_id'] = dept_id
        
        # Auto-generate name
        if 'year' in vals_list and 'semester_number' in vals_list:
            vals_list['name'] = f"Year {vals_list['year']} Semester {vals_list['semester_number']}"
        
        return super(Semester, self).create(vals_list)
    
    @api.depends('department_id')
    def _compute_total_courses(self):
        for semester in self:
            semester.total_courses = 0  # Can be extended later to count related courses
    
    @api.constrains('course_id', 'department_id')
    def _check_course_unique_in_semesters(self):
        """Ensure a course is only added once across all semesters for a department"""
        for semester in self:
            if semester.course_id and semester.department_id:
                # Check if this course already exists in any semester for this department
                existing_sem = self.search([
                    ('course_id', '=', semester.course_id.id),
                    ('department_id', '=', semester.department_id.id),
                    ('id', '!=', semester.id)
                ], limit=1)
                if existing_sem:
                    raise ValidationError(
                        f"Course '{semester.course_id.name}' is already added in Year {existing_sem.year} Semester {existing_sem.semester_number} "
                        f"for this department. A course can only be added once across all semesters."
                    )

    def action_view_course_outline(self):
        """Action to view English course outline PDF"""
        self.ensure_one()
        if not self.course_id:
            raise UserError('Please select a course to view its outline.')
        return {
            'type': 'ir.actions.act_url',
            'url': f'/course-outline/{self.course_id.id}/pdf',
            'target': 'new',
        }

    def action_view_course_outline_ar(self):
        """Action to view Arabic course outline PDF"""
        self.ensure_one()
        if not self.course_id:
            raise UserError('Please select a course to view its outline.')
        return {
            'type': 'ir.actions.act_url',
            'url': f'/course-outline/{self.course_id.id}/pdf/ar',
            'target': 'new',
        }

    def write(self, vals):
        """Prevent changing/removing semester course when used in timetable."""
        if 'course_id' in vals:
            Timetable = self.env['elearning.timetable']
            new_course_id = vals.get('course_id')
            for rec in self:
                # If existing course is changing or being cleared, ensure it's not used in timetable.
                if rec.course_id and rec.course_id.id != new_course_id:
                    used = Timetable.search_count([
                        ('department_id', '=', rec.department_id.id),
                        ('semester_id.year', '=', rec.year),
                        ('semester_id.semester_number', '=', rec.semester_number),
                        ('course_id', '=', rec.course_id.id),
                    ])
                    if used:
                        raise ValidationError(
                            f"Course '{rec.course_id.name}' is already used in timetable entries for "
                            f"Y{rec.year}S{rec.semester_number}. Remove it from timetable first."
                        )
        return super().write(vals)

    def unlink(self):
        """Prevent deleting semester line when its course is used in timetable."""
        Timetable = self.env['elearning.timetable']
        for rec in self:
            if rec.course_id:
                used = Timetable.search_count([
                    ('department_id', '=', rec.department_id.id),
                    ('semester_id.year', '=', rec.year),
                    ('semester_id.semester_number', '=', rec.semester_number),
                    ('course_id', '=', rec.course_id.id),
                ])
                if used:
                    raise ValidationError(
                        f"Course '{rec.course_id.name}' is already used in timetable entries for "
                        f"Y{rec.year}S{rec.semester_number}. Remove it from timetable first."
                    )
        return super().unlink()


class SemesterSlot(models.Model):
    _name = 'elearning.semester.slot'
    _description = 'Semester Slot'
    _order = 'department_id, year, semester_number'
    _rec_name = 'display_name'

    name = fields.Char('Name', compute='_compute_display_name', store=True)
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    year = fields.Integer('Year', required=True)
    semester_number = fields.Integer('Semester Number', required=True)

    department_id = fields.Many2one('hr.department', string='Department', required=True, ondelete='cascade')
    college_id = fields.Many2one('elearning.college', string='College', related='department_id.college_id', store=True, readonly=True)
    timetable_template_ids = fields.One2many('elearning.timetable.template', 'semester_id', string='Timetable Templates')

    _sql_constraints = [
        ('slot_unique_per_department', 'unique(department_id, year, semester_number)',
         'A semester slot already exists for this department and semester.'),
    ]

    @api.depends('year', 'semester_number')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"Y{rec.year}S{rec.semester_number}"
            rec.name = rec.display_name


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    
    # Add relationships for requirements and semesters
    requirement_ids = fields.One2many('elearning.requirement', 'department_id', string='All Requirements')
    
    # Separate fields for each requirement type to ensure proper domain isolation
    faculty_requirement_ids = fields.One2many('elearning.requirement', 'department_id', string='Faculty Requirements', domain=[('requirement_type', '=', 'faculty')])
    department_requirement_ids = fields.One2many('elearning.requirement', 'department_id', string='Department Requirements', domain=[('requirement_type', '=', 'department')])
    program_requirement_ids = fields.One2many('elearning.requirement', 'department_id', string='Program Requirements', domain=[('requirement_type', '=', 'program')])
    elective_requirement_ids = fields.One2many('elearning.requirement', 'department_id', string='Elective Requirements', domain=[('requirement_type', '=', 'elective')])
    university_requirement_ids = fields.One2many('elearning.requirement', 'department_id', string='University Requirements', domain=[('requirement_type', '=', 'university')])
    
    semester_ids = fields.One2many('elearning.semester', 'department_id', string='All Semesters')
    
    # Separate fields for each semester to ensure proper domain isolation (up to 6 years = 12 semesters)
    y1s1_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y1S1 Semesters', domain=[('year', '=', 1), ('semester_number', '=', 1)])
    y1s2_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y1S2 Semesters', domain=[('year', '=', 1), ('semester_number', '=', 2)])
    y2s1_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y2S1 Semesters', domain=[('year', '=', 2), ('semester_number', '=', 1)])
    y2s2_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y2S2 Semesters', domain=[('year', '=', 2), ('semester_number', '=', 2)])
    y3s1_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y3S1 Semesters', domain=[('year', '=', 3), ('semester_number', '=', 1)])
    y3s2_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y3S2 Semesters', domain=[('year', '=', 3), ('semester_number', '=', 2)])
    y4s1_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y4S1 Semesters', domain=[('year', '=', 4), ('semester_number', '=', 1)])
    y4s2_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y4S2 Semesters', domain=[('year', '=', 4), ('semester_number', '=', 2)])
    y5s1_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y5S1 Semesters', domain=[('year', '=', 5), ('semester_number', '=', 1)])
    y5s2_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y5S2 Semesters', domain=[('year', '=', 5), ('semester_number', '=', 2)])
    y6s1_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y6S1 Semesters', domain=[('year', '=', 6), ('semester_number', '=', 1)])
    y6s2_semester_ids = fields.One2many('elearning.semester', 'department_id', string='Y6S2 Semesters', domain=[('year', '=', 6), ('semester_number', '=', 2)])
    
    # Academic year fields
    academic_year_start = fields.Selection(selection='_get_year_options', string='Academic Year Start', default='2023', tracking=True)
    academic_year_end = fields.Selection(selection='_get_year_options', string='Academic Year End', default='2024', tracking=True)
    academic_years_count = fields.Integer('Academic Years Count', compute='_compute_academic_years_count', store=True)
    
    def _get_year_options(self):
        """Generate year options from 2010 to 2050"""
        return [(str(year), str(year)) for year in range(2010, 2051)]

    def _ensure_semester_placeholders(self):
        """Synchronize semester slots with current academic year range.

        - Create missing slots for each (year, semester_number) pair.
        - Remove extra slots outside the range only when they are not used by
          any timetable template.
        """
        Slot = self.env['elearning.semester.slot']
        for dept in self:
            # Derive years count directly from selected academic years.
            years_count = 0
            if dept.academic_year_start and dept.academic_year_end:
                years_count = (int(dept.academic_year_end) - int(dept.academic_year_start)) + 1
            if years_count <= 0:
                continue

            desired_pairs = {(year, sem_num) for year in range(1, years_count + 1) for sem_num in (1, 2)}
            existing_slots = Slot.search([('department_id', '=', dept.id)])
            existing_pairs = {(slot.year, slot.semester_number) for slot in existing_slots}

            # Create missing slots.
            for year, sem_num in sorted(desired_pairs - existing_pairs):
                Slot.create({
                    'department_id': dept.id,
                    'year': year,
                    'semester_number': sem_num,
                })

            # Remove obsolete slots only if unused by timetable templates.
            obsolete_slots = existing_slots.filtered(lambda s: (s.year, s.semester_number) not in desired_pairs)
            removable_slots = obsolete_slots.filtered(lambda s: not s.timetable_template_ids)
            if removable_slots:
                removable_slots.unlink()
    
    # Computed fields for counts
    total_requirements = fields.Integer('Total Requirements', compute='_compute_total_requirements', store=True)
    total_semesters = fields.Integer('Total Semesters', compute='_compute_total_semesters', store=True)
    
    # Computed fields for available courses (excluding already used ones)
    available_requirement_course_ids = fields.Many2many('slide.channel', compute='_compute_available_course_ids', string='Available Courses for Requirements')
    available_semester_course_ids = fields.Many2many('slide.channel', compute='_compute_available_course_ids', string='Available Courses for Semesters')
    
    @api.depends('academic_year_start', 'academic_year_end')
    def _compute_academic_years_count(self):
        for dept in self:
            if dept.academic_year_start and dept.academic_year_end:
                # Calculate the difference in years between the selected years
                start_year = int(dept.academic_year_start)
                end_year = int(dept.academic_year_end)
                dept.academic_years_count = (end_year - start_year) + 1
            else:
                dept.academic_years_count = 0
    
    @api.depends('requirement_ids')
    def _compute_total_requirements(self):
        for dept in self:
            dept.total_requirements = len(dept.requirement_ids)
    
    @api.depends('semester_ids')
    def _compute_total_semesters(self):
        for dept in self:
            dept.total_semesters = len(dept.semester_ids)
    
    @api.depends('requirement_ids.course_id', 'semester_ids.course_id', 'department_course_ids')
    def _compute_available_course_ids(self):
        """Compute available courses for requirements and semesters (excluding already used ones)"""
        for dept in self:
            # Get all department courses
            all_course_ids = dept.department_course_ids.ids
            
            # Get courses already used in requirements
            used_in_requirements = dept.requirement_ids.mapped('course_id').ids
            
            # Get courses already used in semesters
            used_in_semesters = dept.semester_ids.mapped('course_id').ids
            
            # Available courses for requirements = all courses - courses used in requirements
            dept.available_requirement_course_ids = [(6, 0, [cid for cid in all_course_ids if cid not in used_in_requirements])]
            
            # Available courses for semesters = all courses - courses used in semesters
            dept.available_semester_course_ids = [(6, 0, [cid for cid in all_course_ids if cid not in used_in_semesters])]
    
    def action_view_requirements(self):
        """Action to view requirements of this department"""
        action = self.env['ir.actions.act_window']._for_xml_id('elearning_colleges.action_view_department_requirements')
        action['domain'] = [('department_id', '=', self.id)]
        action['context'] = {'default_department_id': self.id}
        return action
    
    def action_view_semesters(self):
        """Action to view semesters of this department"""
        action = self.env['ir.actions.act_window']._for_xml_id('elearning_colleges.action_view_department_semesters')
        action['domain'] = [('department_id', '=', self.id)]
        action['context'] = {'default_department_id': self.id}
        return action
    
    @api.constrains('academic_year_start', 'academic_year_end')
    def _check_academic_years(self):
        for dept in self:
            if dept.academic_year_start and dept.academic_year_end:
                start_year = int(dept.academic_year_start)
                end_year = int(dept.academic_year_end)
                if start_year >= end_year:
                    raise ValidationError("Academic year start must be before academic year end.")
                years_diff = end_year - start_year
                if years_diff > 5:  # 6 years maximum (0, 1, 2, 3, 4, 5 difference = 1, 2, 3, 4, 5, 6 years)
                    raise ValidationError("Academic program cannot exceed 6 years.")
                if years_diff < 0:
                    raise ValidationError("Academic program must be at least 1 year.")
    
    def _get_used_requirement_course_ids(self):
        """Get list of course IDs already used in requirements for this department"""
        self.ensure_one()
        return self.requirement_ids.mapped('course_id').ids
    
    def _get_used_semester_course_ids(self):
        """Get list of course IDs already used in semesters for this department"""
        self.ensure_one()
        return self.semester_ids.mapped('course_id').ids
    
    def _get_available_requirement_course_ids(self):
        """Get list of course IDs available for requirements (department courses not already used)"""
        self.ensure_one()
        used_ids = self._get_used_requirement_course_ids()
        all_course_ids = self.department_course_ids.ids
        return [cid for cid in all_course_ids if cid not in used_ids]
    
    def _get_available_semester_course_ids(self):
        """Get list of course IDs available for semesters (department courses not already used)"""
        self.ensure_one()
        used_ids = self._get_used_semester_course_ids()
        all_course_ids = self.department_course_ids.ids
        return [cid for cid in all_course_ids if cid not in used_ids]
    
    def _get_semesters_for_year(self, year):
        """Get semester records for a specific year"""
        self.ensure_one()
        return self.semester_ids.filtered(lambda s: s.year == year)
    
    def write(self, vals):
        """Override write to check for courses in semesters before reducing academic years"""
        # Check if academic years are being changed
        if 'academic_year_start' in vals or 'academic_year_end' in vals:
            for record in self:
                # Calculate old years count
                if record.academic_year_start and record.academic_year_end:
                    old_start = int(record.academic_year_start)
                    old_end = int(record.academic_year_end)
                    old_years_count = (old_end - old_start) + 1
                else:
                    old_years_count = 0
                
                # Calculate new years count
                new_start = int(vals.get('academic_year_start', record.academic_year_start or '2023'))
                new_end = int(vals.get('academic_year_end', record.academic_year_end or '2024'))
                new_years_count = (new_end - new_start) + 1
                
                # Check if reducing years
                if new_years_count < old_years_count:
                    # Get years that will be hidden
                    hidden_years = list(range(new_years_count + 1, old_years_count + 1))
                    
                    # Check each hidden year for courses
                    semesters_with_courses = []
                    for year in hidden_years:
                        year_semesters = record._get_semesters_for_year(year)
                        if year_semesters:
                            for sem in year_semesters:
                                if sem.course_id:
                                    semesters_with_courses.append(f"Year {year} Semester {sem.semester_number}: {sem.course_id.name}")
                    
                    if semesters_with_courses:
                        # Show validation error with list of semesters that have courses
                        semester_list = "\n".join([f"  • {name}" for name in semesters_with_courses])
                        raise UserError(
                            f"Cannot reduce academic years from {old_years_count} to {new_years_count}.\n\n"
                            f"The following semesters contain courses:\n{semester_list}\n\n"
                            f"Please remove these courses from the semesters first, then you can reduce the academic years count."
                        )

                    # Also block reduction if hidden-year slots are used in timetable templates.
                    used_slots = self.env['elearning.semester.slot'].search([
                        ('department_id', '=', record.id),
                        ('year', 'in', hidden_years),
                        ('timetable_template_ids', '!=', False),
                    ])
                    if used_slots:
                        slot_names = "\n".join(
                            [f"  • Y{s.year}S{s.semester_number}" for s in used_slots]
                        )
                        raise UserError(
                            f"Cannot reduce academic years from {old_years_count} to {new_years_count}.\n\n"
                            f"The following semester slots are already used in timetable templates:\n{slot_names}\n\n"
                            f"Please delete those timetable templates first, then reduce academic years."
                        )
        
        res = super().write(vals)
        # Keep semester slot placeholders in sync with academic years.
        if 'academic_year_start' in vals or 'academic_year_end' in vals:
            self._ensure_semester_placeholders()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._ensure_semester_placeholders()
        return records
