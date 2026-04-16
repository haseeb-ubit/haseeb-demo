# -*- coding: utf-8 -*-
# noinspection PyMethodMayBeStatic
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LibraryBook(models.Model):
    _name = "library.book"
    _description = "Library Book Title"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # views_count = fields.Integer(string="Total Views", default=0)
    #name = fields.Char(string="Title", required=True)
    #rating = fields.Float(string="Rating", default=0.0)
    favorite_user_ids = fields.Many2many('res.users', string="Users who favorited this book")
    rating = fields.Float(string="Rating", compute="_compute_rating", store=True)
    name = fields.Char("Title", required=True, tracking=True)
    author_ids = fields.Many2many("library.author", string="Authors", required=True)
    publisher_id = fields.Many2one("library.publisher", string="Publisher")
    isbn = fields.Char(string="ISBN", tracking=True, required=True)
    edition = fields.Char()
    language = fields.Char()
    number_of_pages = fields.Integer()
    category_id = fields.Many2one("library.category", string="Category", required=True)
    description = fields.Text()
    cover_image = fields.Image()
    publication_year = fields.Integer()
    # E-Book fields
    ebook_file = fields.Binary(string="E-Book File", attachment=True)
    ebook_filename = fields.Char(string="E-Book Filename")
    ebook_available = fields.Boolean(compute="_compute_ebook_available", store=True, string="E-Book Available")
    ebook_download_allowed = fields.Boolean(string="Allow Download", default=True)

    copy_ids = fields.One2many("library.book.copy", "book_id", string="Copies")
    review_ids = fields.One2many("library.book.review", "book_id", string="Reviews")
    avg_rating = fields.Float(compute="_compute_rating", store=True, string="Avg Rating")
    review_count = fields.Integer(compute="_compute_rating", store=True, string="Reviews")

    total_copies = fields.Integer(compute="_compute_copy_metrics", store=True)
    available_copies = fields.Integer(compute="_compute_copy_metrics", store=True)
    borrowed_copies = fields.Integer(compute="_compute_copy_metrics", store=True)
    reserved_copies = fields.Integer(compute="_compute_copy_metrics", store=True)
    damaged_copies = fields.Integer(compute="_compute_copy_metrics", store=True)
    lost_copies = fields.Integer(compute="_compute_copy_metrics", store=True)
    is_favorite = fields.Boolean(string="Is Favorite", default=False)
    #favorite_user_ids = fields.Many2many('res.users', string='Favorited By')
    #favorite_user_ids = fields.Many2many('res.users', string='Favorited By')
    _sql_constraints = [
        ("library_book_isbn_uniq", "unique(isbn)", "ISBN must be unique."),
    ]

    @api.depends("ebook_file")
    def _compute_ebook_available(self):
        for record in self:
            record.ebook_available = bool(record.ebook_file)

    @api.depends("review_ids", "review_ids.rating")
    def _compute_rating(self):
        for record in self:
            reviews = record.review_ids
            record.review_count = len(reviews)
            record.avg_rating = (
                sum(reviews.mapped("rating")) / len(reviews) if reviews else 0.0
            )

        for book in self:
            # Look for all reviews linked to this book
            reviews = self.env['library.book.review'].search([('book_id', '=', book.id)])
            if reviews:
                # Calculate the average (e.g., 4 + 5 / 2 = 4.5)
                book.rating = sum(reviews.mapped('rating')) / len(reviews)
            else:
                book.rating = 0.0

    @api.depends("copy_ids", "copy_ids.status")
    def _compute_copy_metrics(self):
        for record in self:
            record.total_copies = len(record.copy_ids)
            record.available_copies = len(record.copy_ids.filtered(lambda c: c.status == "available"))
            record.borrowed_copies = len(record.copy_ids.filtered(lambda c: c.status == "borrowed"))
            record.reserved_copies = len(record.copy_ids.filtered(lambda c: c.status == "reserved"))
            record.damaged_copies = len(record.copy_ids.filtered(lambda c: c.status == "damaged"))
            record.lost_copies = len(record.copy_ids.filtered(lambda c: c.status == "lost"))

    # ------------------------------------------------------------------
    # Recommendation helpers
    # ------------------------------------------------------------------
    @api.model
    def _get_popular_books(self, limit=10):
        """Books with the most borrow records (all-time)."""
        self.env.cr.execute("""
            SELECT b.book_id, COUNT(*) as cnt
            FROM library_borrow b
            WHERE b.state IN ('borrowed', 'overdue', 'returned')
            GROUP BY b.book_id
            ORDER BY cnt DESC
            LIMIT %s
        """, (limit,))
        rows = self.env.cr.fetchall()
        book_ids = [r[0] for r in rows]
        return self.browse(book_ids)

    @api.model
    def _get_recommended_for_user(self, user_id, limit=10):
        """Books in categories the user has borrowed from, excluding already-borrowed, ordered by avg_rating."""
        Borrow = self.env["library.borrow"].sudo()
        user_borrows = Borrow.search([("student_id", "=", user_id)])
        borrowed_book_ids = user_borrows.mapped("book_id").ids
        categories = user_borrows.mapped("book_id.category_id").ids
        if not categories:
            return self.browse()
        domain = [
            ("category_id", "in", categories),
            ("id", "not in", borrowed_book_ids),
        ]
        return self.search(domain, order="avg_rating desc", limit=limit)

    @api.model
    def _get_trending_books(self, limit=10):
        """Most borrowed in last 30 days."""
        cutoff = fields.Date.today() - timedelta(days=30)
        self.env.cr.execute("""
            SELECT b.book_id, COUNT(*) as cnt
            FROM library_borrow b
            WHERE b.state IN ('borrowed', 'overdue', 'returned')
              AND b.borrow_date >= %s
            GROUP BY b.book_id
            ORDER BY cnt DESC
            LIMIT %s
        """, (cutoff, limit))
        rows = self.env.cr.fetchall()
        book_ids = [r[0] for r in rows]
        return self.browse(book_ids)

