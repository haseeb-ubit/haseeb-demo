# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class LibraryReservation(models.Model):
    _name = "library.reservation"
    _description = "Library Reservation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date asc, id asc"

    name = fields.Char(default="New", readonly=True, copy=False)
    student_id = fields.Many2one(
        "res.users",
        string="Student",
        default=lambda self: self.env.user,
        required=True,
    )
    student_partner_id = fields.Many2one(
        "res.partner", related="student_id.partner_id", store=True, readonly=True
    )
    book_id = fields.Many2one("library.book", required=True)
    copy_id = fields.Many2one("library.book.copy", required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    state = fields.Selection(
        [
            ("requested", "Requested"),
            ("active", "Active"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="requested",
        required=True,
        tracking=True,
    )
    availability_notified = fields.Boolean(default=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("library.reservation") or "New"
        return super().create(vals_list)

    @api.onchange("book_id")
    def _onchange_book_id(self):
        self.copy_id = False
        if self.book_id:
            return {
                "domain": {
                    "copy_id": [("book_id", "=", self.book_id.id), ("status", "!=", "lost")]
                }
            }
        return {"domain": {"copy_id": [("id", "=", False)]}}

    @api.constrains("start_date", "end_date")
    def _check_date_range(self):
        for record in self:
            if record.end_date < record.start_date:
                raise ValidationError("Reservation end date must be on or after start date.")

    @api.constrains("copy_id", "start_date", "end_date", "state")
    def _check_overlap(self):
        for record in self:
            if record.state in ("cancelled", "done"):
                continue
            conflict_domain = [
                ("id", "!=", record.id),
                ("copy_id", "=", record.copy_id.id),
                ("state", "in", ["requested", "active"]),
                ("start_date", "<=", record.end_date),
                ("end_date", ">=", record.start_date),
            ]
            if self.search_count(conflict_domain):
                raise ValidationError("Reservation dates overlap with another active/requested reservation.")

    def action_activate(self):
        for record in self:
            record.state = "active"
            if record.copy_id.status == "available":
                record.copy_id.status = "reserved"

    def action_done(self):
        for record in self:
            record.state = "done"
            if record.copy_id.status == "reserved":
                record.copy_id.status = "available"

    def action_cancel(self):
        for record in self:
            record.state = "cancelled"
            if record.copy_id.status == "reserved":
                record.copy_id.status = "available"
