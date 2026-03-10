# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LibraryPurchaseRequest(models.Model):
    _name = "library.purchase.request"
    _description = "Library Book Purchase Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(default="New", readonly=True, copy=False)
    student_id = fields.Many2one(
        "res.users", string="Student", required=True,
        default=lambda self: self.env.user, tracking=True,
    )
    student_partner_id = fields.Many2one(
        "res.partner", related="student_id.partner_id", store=True, readonly=True,
    )
    book_title = fields.Char(string="Requested Book Title", required=True)
    author_name = fields.Char(string="Author")
    publisher_name = fields.Char(string="Publisher")
    isbn = fields.Char(string="ISBN")
    reason = fields.Text(string="Reason for Request")
    state = fields.Selection(
        [
            ("requested", "Requested"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("on_hold", "On Hold"),
            ("purchased", "Purchased"),
        ],
        default="requested",
        required=True,
        tracking=True,
    )
    created_book_id = fields.Many2one(
        "library.book", string="Created Book",
        help="Link to the book record once purchased and added to catalog.",
    )
    request_count = fields.Integer(
        compute="_compute_request_count", store=False,
        string="Similar Requests",
    )
    manager_notes = fields.Text(string="Manager Notes")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("library.purchase.request") or "New"
                )
        return super().create(vals_list)

    def _compute_request_count(self):
        for record in self:
            if record.book_title:
                record.request_count = self.search_count([
                    ("book_title", "ilike", record.book_title),
                    ("id", "!=", record.id),
                ])
            else:
                record.request_count = 0

    def action_approve(self):
        for record in self:
            record.state = "approved"

    def action_reject(self):
        for record in self:
            record.state = "rejected"

    def action_hold(self):
        for record in self:
            record.state = "on_hold"

    def action_mark_purchased(self):
        """Mark as purchased and notify all students who requested the same title."""
        template = self.env.ref(
            "ust_library.mail_template_library_purchase_available", raise_if_not_found=False
        )
        for record in self:
            record.state = "purchased"
            if template:
                # Notify all students who requested the same title
                similar = self.search([
                    ("book_title", "ilike", record.book_title),
                    ("state", "in", ("requested", "approved", "on_hold")),
                ])
                for req in similar:
                    if req.student_partner_id.email:
                        template.sudo().send_mail(req.id, force_send=True)
                    req.state = "purchased"
                    req.created_book_id = record.created_book_id
