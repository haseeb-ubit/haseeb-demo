# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Noticeboard(models.Model):
    _name = 'elearning.noticeboard'
    _description = 'Department Noticeboard'
    _order = 'priority desc, publish_date desc'
    _rec_name = 'title'

    # Relationships
    department_id = fields.Many2one('hr.department', string='Department', required=True, tracking=True,
                                     default=lambda self: self.env.context.get('default_department_id'))
    college_id = fields.Many2one('elearning.college', string='College',
                                  related='department_id.college_id', store=True, readonly=True)
    
    # Notice fields
    title = fields.Char('Title', required=True, tracking=True)
    message = fields.Html('Message', required=True, tracking=True)
    
    # Publishing
    publish_date = fields.Datetime('Publish Date', default=fields.Datetime.now, required=True, tracking=True)
    author_id = fields.Many2one('res.users', string='Author', default=lambda self: self.env.user, 
                                required=True, tracking=True, readonly=True)
    website_published = fields.Boolean('Published on Website', default=False, tracking=True)
    
    # Priority
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1', required=True, tracking=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-populate fields"""
        for vals in vals_list:
            # Auto-populate department_id from context if not provided
            if not vals.get('department_id'):
                department_id = self.env.context.get('default_department_id')
                if department_id:
                    vals['department_id'] = department_id
            
            # Auto-set author if not provided
            if not vals.get('author_id'):
                vals['author_id'] = self.env.user.id
            
            # Auto-set publish_date if not provided
            if not vals.get('publish_date'):
                vals['publish_date'] = fields.Datetime.now()
        
        return super().create(vals_list)
    
    def write(self, vals):
        """Handle updates"""
        return super().write(vals)
    
    def toggle_website_published(self):
        """Toggle website published status"""
        for record in self:
            record.website_published = not record.website_published
        return True
