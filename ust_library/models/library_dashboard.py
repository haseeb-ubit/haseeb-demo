# -*- coding: utf-8 -*-
from odoo import api, fields, models
import calendar
from datetime import date

class LibraryDashboard(models.Model):
    _name = "library.dashboard"
    _description = "Library Dashboard"
    _auto = False

    name = fields.Char(default="Library Dashboard", readonly=True)
    name = fields.Char(string="Title", required=True)
    # --- Backend Fields (Required so XML doesn't crash) ---
    #name = fields.Char(string="Title", required=True)
    is_favorite = fields.Boolean(string="Favorite", default=False)
    total_books = fields.Integer(readonly=True)
    total_copies = fields.Integer(readonly=True)
    total_students = fields.Integer(readonly=True)
    ebooks_available = fields.Integer(readonly=True)
    copies_available = fields.Integer(readonly=True)
    copies_borrowed = fields.Integer(readonly=True)
    copies_reserved = fields.Integer(readonly=True)
    copies_damaged = fields.Integer(readonly=True)
    copies_lost = fields.Integer(readonly=True)
    total_borrows = fields.Integer(readonly=True)
    active_borrows = fields.Integer(readonly=True)
    overdue_borrows = fields.Integer(readonly=True)
    total_penalties = fields.Float(readonly=True)
    total_reservations = fields.Integer(readonly=True)
    active_reservations = fields.Integer(readonly=True)
    total_reviews = fields.Integer(readonly=True)
    total_spaces = fields.Integer(readonly=True)
    pending_incidents = fields.Integer(readonly=True)
    total_incidents = fields.Integer(readonly=True)
    pending_purchase_requests = fields.Integer(readonly=True)
    active_space_bookings = fields.Integer(readonly=True)

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW library_dashboard AS (
                SELECT 1 AS id, 'Library Dashboard' AS name,
                0 AS total_books, 0 AS total_copies, 0 AS total_students, 0 AS ebooks_available,
                0 AS copies_available, 0 AS copies_borrowed, 0 AS copies_reserved, 0 AS copies_damaged, 0 AS copies_lost,
                0 AS total_borrows, 0 AS active_borrows, 0 AS overdue_borrows, 0 AS total_penalties,
                0 AS total_reservations, 0 AS active_reservations, 0 AS total_reviews, 0 AS total_spaces,
                0 AS pending_incidents, 0 AS total_incidents, 0 AS pending_purchase_requests, 0 AS active_space_bookings
            )
        """)

class LibraryDashboardAPI(models.AbstractModel):
    _name = "library.dashboard.api"
    _description = "Library Dashboard API"

    @api.model
    def get_dashboard_data(self):
        # 1. Force identify the models
        Book = self.env["library.book"].sudo()
        Copy = self.env["library.book.copy"].sudo()
        Borrow = self.env["library.borrow"].sudo()
        Reservation = self.env["library.reservation"].sudo()
        PurchaseReq = self.env["library.purchase.request"].sudo()
        Review = self.env["library.book.review"].sudo()
        Space = self.env["library.space"].sudo()
        SpaceBooking = self.env["library.space.booking"].sudo()
        total_favorites = Book.search_count([("is_favorite", "=", True)])

        # 2. Basic Counts (Checking for your specific field names)
        data = {
            "total_books": Book.search_count([]),
            "total_favorites": total_favorites,
            "total_copies": Copy.search_count([]),
            "ebooks_available": Book.search_count([("ebook_available", "=", True)]),
            "total_students": self.env["res.users"].sudo().search_count([]),
            "total_favorites": Book.search_count([("is_favorite", "=", True)]),
            "active_borrows": Borrow.search_count([("state", "in", ("borrowed", "overdue"))]),
            "overdue_borrows": Borrow.search_count([("state", "=", "overdue")]),
            "active_reservations": Reservation.search_count([("state", "in", ("requested", "active"))]),
            "total_reviews": Review.search_count([]),
            "total_spaces": Space.search_count([]),
            "active_space_bookings": SpaceBooking.search_count([("state", "in", ("requested", "confirmed"))]),
            "pending_requests": PurchaseReq.search_count([("state", "=", "requested")]),
        }

        # 3. Top Borrowed Books (SQL Logic)
        self.env.cr.execute("""
            SELECT bk.name, COUNT(b.id) as count
            FROM library_borrow b
            JOIN library_book_copy cp ON b.copy_id = cp.id
            JOIN library_book bk ON cp.book_id = bk.id
            GROUP BY bk.name ORDER BY count DESC LIMIT 5
        """)
        data["top_books"] = [{"name": r[0], "count": r[1]} for r in self.env.cr.fetchall()]

        # 4. Donut Chart (Copy Status)
        data["copy_status"] = {
            "labels": ["Available", "Borrowed", "Reserved", "Damaged", "Lost"],
            "values": [
                Copy.search_count([("status", "=", "available")]),
                Copy.search_count([("status", "=", "borrowed")]),
                Copy.search_count([("status", "=", "reserved")]),
                Copy.search_count([("status", "=", "damaged")]),
                Copy.search_count([("status", "=", "lost")]),
            ],
        }

        # 5. Monthly Bar Chart
        current_year = date.today().year
        self.env.cr.execute("""
            SELECT EXTRACT(MONTH FROM borrow_date)::int AS month, COUNT(id)
            FROM library_borrow
            WHERE EXTRACT(YEAR FROM borrow_date) = %s
            GROUP BY 1
        """, (current_year,))
        monthly = {row[0]: row[1] for row in self.env.cr.fetchall()}
        data["monthly_borrows"] = {
            "labels": [calendar.month_abbr[i] for i in range(1, 13)],
            "values": [monthly.get(i, 0) for i in range(1, 13)],
        }

        # 6. Top Categories
        self.env.cr.execute("""
            SELECT c.name, COUNT(b.id) AS cnt
            FROM library_borrow b
            JOIN library_book_copy cp ON b.copy_id = cp.id
            JOIN library_book bk ON cp.book_id = bk.id
            LEFT JOIN library_category c ON bk.category_id = c.id
            GROUP BY c.name ORDER BY cnt DESC LIMIT 5
        """)
        cat_rows = self.env.cr.fetchall()
        data["top_categories"] = {
            "labels": [r[0] or "Uncategorized" for r in cat_rows],
            "values": [r[1] for r in cat_rows],
        }

        # 7. Top Rated
        self.env.cr.execute("SELECT name, avg_rating FROM library_book WHERE avg_rating > 0 ORDER BY avg_rating DESC LIMIT 5")
        data["top_rated_books"] = [{"name": r[0], "rating": r[1]} for r in self.env.cr.fetchall()]

        return data

