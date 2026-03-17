# -*- coding: utf-8 -*-
from odoo import fields, models


class LibrarySpace(models.Model):
    _name = "library.space"
    _description = "Library Study Space"
    _order = "name"

    name = fields.Char(required=True)
    space_type = fields.Selection(
        [
            ("study_room", "Study Room"),
            ("quiet_seat", "Quiet Seat"),
            ("meeting_room", "Meeting Room"),
        ],
        required=True,
        default="study_room",
    )
    capacity = fields.Integer(required=True, default=1)
    location = fields.Char()
    active = fields.Boolean(default=True)
    image = fields.Image(string="Image")
    booking_ids = fields.One2many("library.space.booking", "space_id", string="Bookings")
