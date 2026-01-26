# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class USTResume(models.Model):
    _name = "ust.resume"
    _description = "سيرة ذاتية عضو هيئة تدريس"
    _rec_name = "user_id"

    user_id = fields.Many2one('res.users', string="الاسم", required=True, default=lambda self: self.env.user,
                              readonly=True)
    job_title = fields.Char("المسمى الوظيفي")
    college_id = fields.Many2one('elearning.college', string="الكلية")
    department_id = fields.Many2one('hr.department', string="القسم", domain="[('college_id', '=', college_id)]")
    email = fields.Char("الايميل الرسمي", readonly=True)
    scholar_link = fields.Char("رابط جوجل اسكولار أو أي قاعدة بيانات أخرى")
    photo = fields.Binary("الصورة")
    resume_pdf = fields.Binary("ملف السيرة الذاتية (PDF)")
    website_published = fields.Boolean(string="نشر على الموقع", default=False)
    published_date = fields.Datetime(string="تاريخ النشر", readonly=True)

    education_ids = fields.One2many('ust.resume.education', 'resume_id', string="المؤهلات العلمية")
    research_ids = fields.One2many('ust.resume.research', 'resume_id', string="الأبحاث العلمية")
    cert_ids = fields.One2many('ust.resume.certificate', 'resume_id', string="الدورات والشهادات")
    exp_ids = fields.One2many('ust.resume.experience', 'resume_id', string="الخبرات العلمية والعملية")
    award_ids = fields.One2many('ust.resume.award', 'resume_id', string="الجوائز والإنجازات")

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
        # Normalize to list of dicts
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        if user.has_group('ust_resume_management.group_resume_teacher'):
            # Teacher can only have one CV
            existing = self.search([('user_id', '=', user.id)], limit=1)
            if existing:
                raise ValidationError(_("You already have a CV. You cannot create another."))
            # Force user and email on all records being created
            for vals in vals_list:
                vals['user_id'] = user.id
                vals['email'] = user.email
        else:
            # Admin/manager: ensure target user does not already have a CV
            for vals in vals_list:
                target_user_id = vals.get('user_id')
                if target_user_id:
                    existing = self.search([('user_id', '=', target_user_id)], limit=1)
                    if existing:
                        raise ValidationError(_("This user already has a CV. You cannot create another."))

        records = super().create(vals_list)
        for rec in records:
            if rec.website_published and not rec.published_date:
                rec.published_date = fields.Datetime.now()
        return records

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
            'url': '/report/pdf/ust_resume_management.ust_resume_report/%s' % self.id,
        }

    @api.onchange('college_id')
    def _onchange_college_id(self):
        """Clear department when college changes"""
        if self.college_id:
            self.department_id = False
        else:
            self.department_id = False


class USTResumeEducation(models.Model):
    _name = "ust.resume.education"
    _description = "المؤهلات العلمية"
    _order = "id"

    resume_id = fields.Many2one('ust.resume', ondelete='cascade')
    degree = fields.Char("الدرجة الأكاديمية")
    specialization = fields.Char("التخصص")
    university = fields.Char("الجامعة")
    uni_link = fields.Char("رابط الجامعة")


class USTResumeResearch(models.Model):
    _name = "ust.resume.research"
    _description = "الأبحاث العلمية"
    _order = "id"

    resume_id = fields.Many2one('ust.resume', ondelete='cascade')
    authors = fields.Char("اسم الباحث أو الباحثين")
    title = fields.Char("عنوان البحث")
    year = fields.Char("سنة النشر")
    journal = fields.Char("المجلة/المؤتمر")
    journal_link = fields.Char("رابط المجلة/المؤتمر")
    impact_factor = fields.Char("Impact factor (إن وجد)")


class USTResumeCertificate(models.Model):
    _name = "ust.resume.certificate"
    _description = "الدورات والشهادات"
    _order = "id"

    resume_id = fields.Many2one('ust.resume', ondelete='cascade')

    name = fields.Char("اسم الدورة/الشهادة")
    institute = fields.Char("المعهد/الجامعة")
    year = fields.Char("سنة الحصول عليها")
    link = fields.Char("رابط المعهد/الجامعة")


class USTResumeExperience(models.Model):
    _name = "ust.resume.experience"
    _description = "الخبرات العلمية والعملية"
    _order = "id"

    resume_id = fields.Many2one('ust.resume', ondelete='cascade')
    title = fields.Char("المسمى الوظيفي")
    organization = fields.Char("جهة العمل")
    period = fields.Char("الفترة (من - إلى)")


class USTResumeAward(models.Model):
    _name = "ust.resume.award"
    _description = "الجوائز والإنجازات"
    _order = " id"

    resume_id = fields.Many2one('ust.resume', ondelete='cascade')
    name = fields.Char("اسم الجائزة/الانجاز")
    issuer = fields.Char("اسم الجهة")
    year = fields.Char("سنة الحصول عليها")
    link = fields.Char("رابط الجهة")