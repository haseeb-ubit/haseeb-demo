# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class USTResumeEN(models.Model):
    _name = "ust.resume.en"
    _description = "Faculty Member Curriculum Vitae (English)"
    _rec_name = "user_id"

    user_id = fields.Many2one('res.users', string="Name", required=True, default=lambda self: self.env.user,
                              readonly=True)
    job_title = fields.Char("Job Title")
    college_id = fields.Many2one('elearning.college', string="College")
    department_id = fields.Many2one('hr.department', string="Department", domain="[('college_id', '=', college_id)]")
    email = fields.Char("Official Email", readonly=True)
    scholar_link = fields.Char("Google Scholar or Other Database Link (e.g. Scopus)")
    photo = fields.Binary("Photo")
    resume_pdf = fields.Binary("Resume PDF File")
    website_published = fields.Boolean(string="Publish on Website", default=False)
    published_date = fields.Datetime(string="Published On", readonly=True)

    education_ids = fields.One2many('ust.resume.education.en', 'resume_id', string="Academic Qualifications")
    research_ids = fields.One2many('ust.resume.research.en', 'resume_id', string="Scientific Research")
    cert_ids = fields.One2many('ust.resume.certificate.en', 'resume_id',
                               string="Major Courses and Professional Certificates")
    exp_ids = fields.One2many('ust.resume.experience.en', 'resume_id', string="Academic and Professional Experience")
    award_ids = fields.One2many('ust.resume.award.en', 'resume_id', string="Awards and Achievements")

    create_uid = fields.Many2one('res.users', string='Created by')
    is_teacher = fields.Boolean(
        string="Is Teacher",
        compute="_compute_is_teacher",
        store=False
    )

    @api.depends_context('uid')
    def _compute_is_teacher(self):
        """Check if current user belongs to the teacher group"""
        for rec in self:
            rec.is_teacher = self.env.user.has_group('ust_resume_management.group_resume_teacher')

    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user
        for vals in vals_list:
            target_user_id = vals.get('user_id')

        if user.has_group('ust_resume_management.group_resume_teacher'):
            existing = self.search([('user_id', '=', user.id)], limit=1)
            if existing:
                raise ValidationError(_("You already have a CV. You cannot create another."))

            vals['user_id'] = user.id
            vals['email'] = user.email
        else:
            if target_user_id:
                existing = self.search([('user_id', '=', target_user_id)], limit=1)
                if existing:
                    raise ValidationError(_("This user already has a CV. You cannot create another."))

        resume = super().create(vals_list)
        if resume.website_published and not resume.published_date:
            resume.published_date = fields.Datetime.now()
        return resume

    def write(self, vals):
        res = super().write(vals)
        if 'website_published' in vals:
            for rec in self:
                if rec.website_published and not rec.published_date:
                    rec.published_date = fields.Datetime.now()
                elif not rec.website_published and rec.published_date:
                    rec.published_date = False
        return res

    def action_preview_pdf(self):
        """Preview the resume as PDF in new window"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/pdf/ust_resume_management.ust_resume_report_en/%s' % self.id,
        }

    @api.onchange('college_id')
    def _onchange_college_id(self):
        """Clear department when college changes"""
        if self.college_id:
            self.department_id = False
        else:
            self.department_id = False


class USTResumeEducationEN(models.Model):
    _name = "ust.resume.education.en"
    _description = "Academic Qualifications"
    _order = "id"

    resume_id = fields.Many2one('ust.resume.en', ondelete='cascade')
    degree = fields.Char("Academic Degree")
    specialization = fields.Char("Specialization")
    university = fields.Char("University")
    uni_link = fields.Char("University Link")


class USTResumeResearchEN(models.Model):
    _name = "ust.resume.research.en"
    _description = "Scientific Research"
    _order = "id"

    resume_id = fields.Many2one('ust.resume.en', ondelete='cascade')
    authors = fields.Char("Researcher(s)")
    title = fields.Char("Research Title")
    year = fields.Char("Year of Publication")
    journal = fields.Char("Journal/Conference")
    journal_link = fields.Char("Journal/Conference Link")
    impact_factor = fields.Char("Impact Factor (If available)")


class USTResumeCertificateEN(models.Model):
    _name = "ust.resume.certificate.en"
    _description = "Major Courses and Professional Certificates"
    _order = "id"

    resume_id = fields.Many2one('ust.resume.en', ondelete='cascade')
    name = fields.Char("Course/Certificate Name")
    institute = fields.Char("Institution/University")
    year = fields.Char("Year Obtained")
    link = fields.Char("Institution/University Link")


class USTResumeExperienceEN(models.Model):
    _name = "ust.resume.experience.en"
    _description = "Academic and Professional Experience"
    _order = "id"

    resume_id = fields.Many2one('ust.resume.en', ondelete='cascade')
    title = fields.Char("Job Title")
    organization = fields.Char("Employer")
    period = fields.Char("Period (From - To)")


class USTResumeAwardEN(models.Model):
    _name = "ust.resume.award.en"
    _description = "Awards and Achievements"
    _order = "id"

    resume_id = fields.Many2one('ust.resume.en', ondelete='cascade')
    name = fields.Char("Award/Achievement Name")
    issuer = fields.Char("Issuing Institution")
    year = fields.Char("Year Obtained")
    link = fields.Char("Institution Link")
