# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LibraryBookIncident(models.Model):
    _name = "library.book.incident"
    _description = "Library Book Incident (Lost / Damaged)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(default="New", readonly=True, copy=False)
    student_id = fields.Many2one("res.users", string="Student", required=True, readonly=True)
    student_partner_id = fields.Many2one(
        "res.partner", related="student_id.partner_id", store=True, readonly=True
    )
    copy_id = fields.Many2one("library.book.copy", string="Book Copy", required=True, readonly=True)
    book_id = fields.Many2one("library.book", string="Book", required=True, readonly=True)
    borrow_id = fields.Many2one("library.borrow", string="Borrow Record", readonly=True)
    incident_type = fields.Selection(
        [
            ("lost", "Lost"),
            ("damaged", "Damaged"),
        ],
        string="Incident Type",
        required=True,
        tracking=True,
    )
    replacement_cost = fields.Float(string="Replacement Cost", tracking=True)
    payment_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("paid", "Paid"),
            ("waived", "Waived"),
        ],
        default="pending",
        required=True,
        tracking=True,
    )
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("library.book.incident") or "New"
        return super().create(vals_list)

    def action_mark_paid(self):
        for record in self:
            record.payment_status = "paid"

    def action_waive(self):
        for record in self:
            record.payment_status = "waived"
