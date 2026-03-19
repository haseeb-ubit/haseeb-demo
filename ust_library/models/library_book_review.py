# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LibraryBookReview(models.Model):
    _name = "library.book.review"
    _description = "Library Book Review"
    _order = "create_date desc"

    student_id = fields.Many2one(
        "res.users", string="Student", required=True,
        default=lambda self: self.env.user,
    )
    student_partner_id = fields.Many2one(
        "res.partner", related="student_id.partner_id", store=True, readonly=True
    )
    book_id = fields.Many2one("library.book", string="Book", required=True, ondelete="cascade")
    rating = fields.Integer(string="Rating (1-5)", required=True)
    review_text = fields.Text(string="Review", required=True)

    _sql_constraints = [
        (
            "library_review_student_book_uniq",
            "unique(student_id, book_id)",
            "You can only write one review per book.",
        ),
    ]

    @api.constrains("rating")
    def _check_rating(self):
        for record in self:
            if record.rating < 1 or record.rating > 5:
                raise ValidationError("Rating must be between 1 and 5.")
