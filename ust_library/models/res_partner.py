# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    library_borrow_ids = fields.One2many("library.borrow", "student_partner_id", string="Library Borrows")
    library_reservation_ids = fields.One2many(
        "library.reservation", "student_partner_id", string="Library Reservations"
    )
