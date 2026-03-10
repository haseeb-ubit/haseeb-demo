# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LibraryDashboard(models.Model):
    """
    Single-record model that computes live library KPIs.
    Used by the manager dashboard action (form view).
    """
    _name = "library.dashboard"
    _description = "Library Dashboard"
    _auto = False  # no DB table

    name = fields.Char(default="Library Dashboard", readonly=True)

    total_books = fields.Integer(compute="_compute_stats")
    total_copies = fields.Integer(compute="_compute_stats")
    copies_available = fields.Integer(compute="_compute_stats")
    copies_borrowed = fields.Integer(compute="_compute_stats")
    copies_reserved = fields.Integer(compute="_compute_stats")
    copies_damaged = fields.Integer(compute="_compute_stats")
    copies_lost = fields.Integer(compute="_compute_stats")
    total_borrows = fields.Integer(compute="_compute_stats")
    active_borrows = fields.Integer(compute="_compute_stats")
    overdue_borrows = fields.Integer(compute="_compute_stats")
    total_reservations = fields.Integer(compute="_compute_stats")
    active_reservations = fields.Integer(compute="_compute_stats")
    total_students = fields.Integer(compute="_compute_stats")
    total_penalties = fields.Float(compute="_compute_stats")
    total_incidents = fields.Integer(compute="_compute_stats")
    pending_incidents = fields.Integer(compute="_compute_stats")
    total_purchase_requests = fields.Integer(compute="_compute_stats")
    pending_purchase_requests = fields.Integer(compute="_compute_stats")
    total_reviews = fields.Integer(compute="_compute_stats")
    ebooks_available = fields.Integer(compute="_compute_stats")
    total_spaces = fields.Integer(compute="_compute_stats")
    active_space_bookings = fields.Integer(compute="_compute_stats")

    def _compute_stats(self):
        Copy = self.env["library.book.copy"].sudo()
        Borrow = self.env["library.borrow"].sudo()
        Reservation = self.env["library.reservation"].sudo()
        Incident = self.env["library.book.incident"].sudo()
        PurchaseReq = self.env["library.purchase.request"].sudo()
        Review = self.env["library.book.review"].sudo()
        Book = self.env["library.book"].sudo()
        Space = self.env["library.space"].sudo()
        SpaceBooking = self.env["library.space.booking"].sudo()

        for rec in self:
            rec.total_books = Book.search_count([])
            rec.total_copies = Copy.search_count([])
            rec.copies_available = Copy.search_count([("status", "=", "available")])
            rec.copies_borrowed = Copy.search_count([("status", "=", "borrowed")])
            rec.copies_reserved = Copy.search_count([("status", "=", "reserved")])
            rec.copies_damaged = Copy.search_count([("status", "=", "damaged")])
            rec.copies_lost = Copy.search_count([("status", "=", "lost")])
            rec.total_borrows = Borrow.search_count([])
            rec.active_borrows = Borrow.search_count(
                [("state", "in", ("borrowed", "overdue"))]
            )
            rec.overdue_borrows = Borrow.search_count([("state", "=", "overdue")])
            rec.total_reservations = Reservation.search_count([])
            rec.active_reservations = Reservation.search_count(
                [("state", "in", ("requested", "active"))]
            )
            rec.total_students = (
                self.env["res.users"]
                .sudo()
                .search_count([("group_ids", "in", [self.env.ref("ust_library.group_library_user").id])])
            )
            overdue_records = Borrow.search([("state", "=", "overdue")])
            rec.total_penalties = sum(overdue_records.mapped("penalty_amount"))
            rec.total_incidents = Incident.search_count([])
            rec.pending_incidents = Incident.search_count([("payment_status", "=", "pending")])
            rec.total_purchase_requests = PurchaseReq.search_count([])
            rec.pending_purchase_requests = PurchaseReq.search_count([("state", "=", "requested")])
            rec.total_reviews = Review.search_count([])
            rec.ebooks_available = Book.search_count([("ebook_available", "=", True)])
            rec.total_spaces = Space.search_count([])
            rec.active_space_bookings = SpaceBooking.search_count(
                [("state", "in", ("requested", "confirmed"))]
            )

    def init(self):
        """Create a single virtual record so the form view has something to display."""
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW library_dashboard AS (
                SELECT 1 AS id, 'Library Dashboard' AS name
            )
        """)
