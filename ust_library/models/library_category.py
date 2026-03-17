# -*- coding: utf-8 -*-
from odoo import fields, models


class LibraryCategory(models.Model):
    _name = "library.category"
    _description = "Library Book Category"
    _order = "name"

    name = fields.Char(required=True)
    description = fields.Text()
    book_ids = fields.One2many("library.book", "category_id")


