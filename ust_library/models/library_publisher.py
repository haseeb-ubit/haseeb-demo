# -*- coding: utf-8 -*-
from odoo import fields, models


class LibraryPublisher(models.Model):
    _name = "library.publisher"
    _description = "Library Publisher"
    _order = "name"

    name = fields.Char(required=True)
    contact_information = fields.Char()
    address = fields.Text()
    book_ids = fields.One2many("library.book", "publisher_id", string="Published Books")
