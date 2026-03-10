# -*- coding: utf-8 -*-
from odoo import fields, models


class LibraryAuthor(models.Model):
    _name = "library.author"
    _description = "Library Author"
    _order = "name"

    name = fields.Char(required=True)
    biography = fields.Text()
    date_of_birth = fields.Date()
    nationality = fields.Char()
    book_ids = fields.Many2many("library.book", string="Published Books")
