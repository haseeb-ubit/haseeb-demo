# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LibraryBorrow(models.Model):
    _name = "library.borrow"
    _description = "Library Borrow Transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(default="New", readonly=True, copy=False)
    student_id = fields.Many2one(
        "res.users",
        string="Student",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    student_partner_id = fields.Many2one(
        "res.partner", related="student_id.partner_id", store=True, readonly=True
    )
    copy_id = fields.Many2one("library.book.copy", required=True, tracking=True)
    book_id = fields.Many2one("library.book", related="copy_id.book_id", store=True, readonly=True)
    request_date = fields.Date(default=fields.Date.today, readonly=True)
    borrow_date = fields.Date(readonly=True)
    expected_return_date = fields.Date(required=True)
    return_date = fields.Date(readonly=True)
    state = fields.Selection(
        [
            ("request", "Request"),
            ("borrowed", "Borrowed"),
            ("overdue", "Overdue"),
            ("returned", "Returned"),
            ("cancelled", "Cancelled"),
        ],
        default="request",
        required=True,
        tracking=True,
    )
    late_days = fields.Integer(compute="_compute_late_days", store=False)
    penalty_rule_id = fields.Many2one("library.penalty.rule", compute="_compute_penalty_rule", store=False)
    penalty_amount = fields.Float(compute="_compute_penalty_amount", store=False)
    return_condition = fields.Selection(
        [
            ("good", "Good"),
            ("damaged", "Damaged"),
            ("lost", "Lost"),
        ],
        string="Return Condition",
        help="Condition of the book when returned (set by manager).",
    )
    replacement_cost = fields.Float(compute="_compute_replacement_cost", store=True, readonly=True)
    replacement_paid = fields.Boolean(default=False, string="Replacement Paid")
    incident_id = fields.Many2one("library.book.incident", string="Incident", readonly=True, copy=False)
    due_reminder_sent = fields.Boolean(default=False)
    overdue_notice_sent = fields.Boolean(default=False)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("library.borrow") or "New"
        return super().create(vals_list)

    @api.constrains("expected_return_date", "request_date")
    def _check_dates(self):
        for record in self:
            if record.expected_return_date and record.request_date and record.expected_return_date < record.request_date:
                raise ValidationError("Expected return date cannot be earlier than request date.")

    @api.depends("state", "expected_return_date", "return_date")
    def _compute_late_days(self):
        for record in self:
            comparison_date = record.return_date or fields.Date.today()
            if record.expected_return_date and comparison_date > record.expected_return_date:
                record.late_days = (comparison_date - record.expected_return_date).days
            else:
                record.late_days = 0

    @api.depends_context("uid")
    def _compute_penalty_rule(self):
        default_rule = self.env["library.penalty.rule"].search([("active", "=", True)], limit=1)
        for record in self:
            record.penalty_rule_id = default_rule

    @api.depends("late_days")
    def _compute_penalty_amount(self):
        default_rule = self.env["library.penalty.rule"].search([("active", "=", True)], limit=1)
        fine = default_rule.fine_per_day if default_rule else 0.0
        for record in self:
            record.penalty_amount = record.late_days * fine

    @api.depends("return_condition", "copy_id.book_price")
    def _compute_replacement_cost(self):
        for record in self:
            price = record.copy_id.book_price or 0.0
            if record.return_condition == "lost":
                record.replacement_cost = price  # full replacement
            elif record.return_condition == "damaged":
                record.replacement_cost = price * 0.5  # 50% for damaged
            else:
                record.replacement_cost = 0.0

    def action_approve(self):
        for record in self:
            if record.copy_id.status not in ("available", "reserved"):
                raise ValidationError("Only available/reserved copies can be approved for borrow.")
            record.write({"state": "borrowed", "borrow_date": fields.Date.today()})
            record.copy_id.status = "borrowed"

    def action_mark_returned(self):
        for record in self:
            condition = record.return_condition or "good"
            record.write({"state": "returned", "return_date": fields.Date.today()})
            if condition == "lost":
                record.copy_id.status = "lost"
                self._create_incident(record, "lost")
            elif condition == "damaged":
                record.copy_id.status = "damaged"
                self._create_incident(record, "damaged")
            else:
                if record.copy_id.status not in ("lost", "damaged"):
                    record.copy_id.status = "available"
                    record.copy_id._notify_next_reservation_available()

    def action_mark_lost(self):
        """Quick action: mark as lost without returning."""
        for record in self:
            record.write({
                "return_condition": "lost",
                "state": "returned",
                "return_date": fields.Date.today(),
            })
            record.copy_id.status = "lost"
            self._create_incident(record, "lost")

    def action_mark_damaged(self):
        """Quick action: mark as damaged on return."""
        for record in self:
            record.write({
                "return_condition": "damaged",
                "state": "returned",
                "return_date": fields.Date.today(),
            })
            record.copy_id.status = "damaged"
            self._create_incident(record, "damaged")

    def _create_incident(self, borrow, incident_type):
        """Create a library.book.incident record linked to this borrow."""
        price = borrow.copy_id.book_price or 0.0
        cost = price if incident_type == "lost" else price * 0.5
        incident = self.env["library.book.incident"].create({
            "student_id": borrow.student_id.id,
            "copy_id": borrow.copy_id.id,
            "book_id": borrow.book_id.id,
            "borrow_id": borrow.id,
            "incident_type": incident_type,
            "replacement_cost": cost,
        })
        borrow.incident_id = incident

    def action_cancel(self):
        for record in self:
            record.state = "cancelled"
            if record.copy_id.status == "reserved":
                record.copy_id.status = "available"

    @api.model
    def _cron_mark_overdue_and_penalties(self):
        today = fields.Date.today()
        overdue_records = self.search(
            [("state", "=", "borrowed"), ("expected_return_date", "<", today)]
        )
        overdue_records.write({"state": "overdue"})

    def _send_borrow_mail(self, template_xmlid):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            return
        for record in self:
            if record.student_partner_id.email:
                template.sudo().send_mail(record.id, force_send=True)

    @api.model
    def _cron_send_due_reminders(self):
        tomorrow = fields.Date.today() + timedelta(days=1)
        due_records = self.search(
            [
                ("state", "=", "borrowed"),
                ("expected_return_date", "=", tomorrow),
                ("due_reminder_sent", "=", False),
            ]
        )
        due_records._send_borrow_mail("ust_library.mail_template_library_due_reminder")
        due_records.write({"due_reminder_sent": True})

    @api.model
    def _cron_send_overdue_alerts(self):
        overdue_records = self.search(
            [("state", "=", "overdue"), ("overdue_notice_sent", "=", False)]
        )
        overdue_records._send_borrow_mail("ust_library.mail_template_library_overdue_notice")
        overdue_records.write({"overdue_notice_sent": True})