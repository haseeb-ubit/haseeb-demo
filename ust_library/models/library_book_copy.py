# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LibraryBookCopy(models.Model):
    _name = "library.book.copy"
    _description = "Library Physical Book Copy"
    _order = "id desc"

    name = fields.Char(required=True, default="New", copy=False)
    book_id = fields.Many2one("library.book", required=True, ondelete="cascade")
    status = fields.Selection(
        [
            ("available", "Available"),
            ("borrowed", "Borrowed"),
            ("reserved", "Reserved"),
            ("damaged", "Damaged"),
            ("lost", "Lost"),
        ],
        default="available",
        required=True,
        tracking=True,
    )
    location = fields.Char()
    book_price = fields.Float(string="Replacement Price", required=True, help="Price used to calculate replacement cost if lost or damaged.")
    borrow_ids = fields.One2many("library.borrow", "copy_id", string="Borrows")
    reservation_ids = fields.One2many("library.reservation", "copy_id", string="Reservations")
    current_borrower_id = fields.Many2one("res.users", compute="_compute_current_borrower", store=False)
    next_available_date = fields.Date(compute="_compute_next_available_date", store=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                next_id = self.search_count([("book_id", "=", vals.get("book_id"))]) + 1
                vals["name"] = "Copy %s" % next_id
        return super().create(vals_list)

    @api.depends("borrow_ids.state", "borrow_ids.student_id")
    def _compute_current_borrower(self):
        for copy in self:
            open_borrow = copy.borrow_ids.filtered(lambda b: b.state in ("borrowed", "overdue"))[:1]
            copy.current_borrower_id = open_borrow.student_id if open_borrow else False

    @api.depends("borrow_ids.expected_return_date", "borrow_ids.state", "reservation_ids.start_date")
    def _compute_next_available_date(self):
        for copy in self:
            open_borrow = copy.borrow_ids.filtered(lambda b: b.state in ("borrowed", "overdue"))[:1]
            active_reservation = copy.reservation_ids.filtered(
                lambda r: r.state in ("requested", "active")
            ).sorted(key=lambda r: r.start_date or fields.Date.today())
            if open_borrow:
                copy.next_available_date = open_borrow.expected_return_date
            elif active_reservation:
                copy.next_available_date = active_reservation[0].start_date
            else:
                copy.next_available_date = fields.Date.today()

    def _notify_next_reservation_available(self):
        template = self.env.ref(
            "ust_library.mail_template_library_reservation_available", raise_if_not_found=False
        )
        if not template:
            return
        for copy in self:
            reservation = copy.reservation_ids.filtered(
                lambda r: r.state == "requested" and not r.availability_notified
            ).sorted(key=lambda r: (r.start_date or fields.Date.today(), r.id))[:1]
            if reservation and reservation.student_partner_id.email:
                template.sudo().send_mail(reservation.id, force_send=True)
                reservation.availability_notified = True
