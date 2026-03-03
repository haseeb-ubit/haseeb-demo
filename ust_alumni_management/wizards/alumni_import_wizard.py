# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import csv
import io


class AlumniImportWizard(models.TransientModel):
    _name = 'alumni.import.wizard'
    _description = 'Alumni Import Wizard'

    file = fields.Binary(string='CSV/Excel File', required=True)
    filename = fields.Char(string='Filename')
    import_type = fields.Selection([
        ('csv', 'CSV File'),
        ('excel', 'Excel File')
    ], string='File Type', default='csv', required=True)
    
    # Field mapping
    name_column = fields.Char(string='Name Column', default='name', required=True)
    email_column = fields.Char(string='Email Column', default='email', required=True)
    department_column = fields.Char(string='Department Column', default='department')
    graduation_year_column = fields.Char(string='Graduation Year Column', default='graduation_year')
    degree_column = fields.Char(string='Degree Column', default='degree')
    major_column = fields.Char(string='Major Column', default='major')
    phone_column = fields.Char(string='Phone Column', default='phone')
    country_column = fields.Char(string='Country Column', default='country')
    
    preview_data = fields.Html(string='Preview', readonly=True)
    
    def action_preview(self):
        """Preview the import data"""
        self.ensure_one()
        if not self.file:
            raise ValidationError(_("Please upload a file first."))
        
        try:
            file_content = base64.b64decode(self.file)
            if self.import_type == 'csv':
                file_text = file_content.decode('utf-8-sig')
                csv_reader = csv.DictReader(io.StringIO(file_text))
                rows = list(csv_reader)
            else:
                # For Excel, we'd need xlrd or openpyxl
                raise ValidationError(_("Excel import requires additional libraries. Please use CSV format."))
            
            if not rows:
                raise ValidationError(_("No data found in file."))
            
            # Generate preview HTML
            preview_html = '<table class="table table-bordered"><thead><tr>'
            if rows:
                for col in rows[0].keys():
                    preview_html += f'<th>{col}</th>'
                preview_html += '</tr></thead><tbody>'
                for row in rows[:10]:  # Show first 10 rows
                    preview_html += '<tr>'
                    for col in rows[0].keys():
                        preview_html += f'<td>{row.get(col, "")}</td>'
                    preview_html += '</tr>'
                preview_html += '</tbody></table>'
                if len(rows) > 10:
                    preview_html += f'<p>... and {len(rows) - 10} more rows</p>'
            
            self.preview_data = preview_html
            return {
                'type': 'ir.actions.act_window',
                'name': _('Import Preview'),
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        except Exception as e:
            raise ValidationError(_("Error reading file: %s") % str(e))
    
    def action_import(self):
        """Import alumni from file"""
        self.ensure_one()
        if not self.file:
            raise ValidationError(_("Please upload a file first."))
        
        try:
            file_content = base64.b64decode(self.file)
            if self.import_type == 'csv':
                file_text = file_content.decode('utf-8-sig')
                csv_reader = csv.DictReader(io.StringIO(file_text))
                rows = list(csv_reader)
            else:
                raise ValidationError(_("Excel import requires additional libraries. Please use CSV format."))
            
            if not rows:
                raise ValidationError(_("No data found in file."))
            
            # Get department mapping
            departments = self.env['hr.department'].search([])
            dept_map = {dept.name.lower(): dept.id for dept in departments}
            
            # Get country mapping
            countries = self.env['res.country'].search([])
            country_map = {country.name.lower(): country.id for country in countries}
            country_code_map = {country.code.lower(): country.id for country in countries}
            
            created = 0
            errors = []
            
            for idx, row in enumerate(rows, start=2):  # Start at 2 (row 1 is header)
                try:
                    with self.env.cr.savepoint():
                        # Get values from columns
                        name = row.get(self.name_column, '').strip()
                        email = row.get(self.email_column, '').strip()
                        
                        if not name or not email:
                            errors.append(_("Row %d: Name and email are required.") % idx)
                            continue
                        
                        # Check for duplicate email
                        existing = self.env['alumni.profile'].search([('email', '=', email)], limit=1)
                        if existing:
                            errors.append(_("Row %d: Alumni with email %s already exists.") % (idx, email))
                            continue
                        
                        # Prepare values
                        vals = {
                            'name': name,
                            'email': email,
                        }
                        
                        # Department
                        dept_name = row.get(self.department_column, '').strip()
                        if dept_name:
                            dept_id = dept_map.get(dept_name.lower())
                            if not dept_id:
                                # Try to find by partial match
                                dept = departments.filtered(lambda d: dept_name.lower() in d.name.lower())
                                dept_id = dept[0].id if dept else False
                            if dept_id:
                                vals['department_id'] = dept_id
                            else:
                                errors.append(_("Row %d: Department '%s' not found.") % (idx, dept_name))
                                continue # Prevent creation if required dept is missing
                        else:
                            errors.append(_("Row %d: Department is required.") % idx)
                            continue
                        
                        # Graduation year
                        grad_year = row.get(self.graduation_year_column, '').strip()
                        if grad_year:
                            try:
                                vals['graduation_year'] = int(grad_year)
                            except ValueError:
                                errors.append(_("Row %d: Invalid graduation year '%s'.") % (idx, grad_year))
                                continue
                        else:
                            errors.append(_("Row %d: Graduation year is required.") % idx)
                            continue
                        
                        # Degree
                        degree = row.get(self.degree_column, '').strip()
                        if degree:
                            vals['degree'] = degree
                        
                        # Major
                        major = row.get(self.major_column, '').strip()
                        if major:
                            vals['major'] = major
                        
                        # Phone
                        phone = row.get(self.phone_column, '').strip()
                        if phone:
                            vals['phone'] = phone
                        
                        # Country
                        country_name = row.get(self.country_column, '').strip()
                        if country_name:
                            country_id = country_map.get(country_name.lower()) or country_code_map.get(country_name.lower())
                            if country_id:
                                vals['country_id'] = country_id
                        
                        # Create alumni profile
                        self.env['alumni.profile'].create(vals)
                        created += 1
                        
                except Exception as e:
                    errors.append(_("Row %d: %s") % (idx, str(e)))
            
            # Show results
            message = _("Import completed: %d alumni created.") % created
            if errors:
                message += "\n\nErrors:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    message += f"\n... and {len(errors) - 10} more errors"
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Results'),
                    'message': message,
                    'type': 'success' if not errors else 'warning',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            raise ValidationError(_("Error importing file: %s") % str(e))
