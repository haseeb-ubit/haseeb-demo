# -*- coding: utf-8 -*-
from odoo import fields, models


class LibraryPenaltyRule(models.Model):
    _name = "library.penalty.rule"
    _description = "Library Late Penalty Rule"

    name = fields.Char(required=True, default="Default Penalty Rule")
    fine_per_day = fields.Float(required=True, default=1.0)
    active = fields.Boolean(default=True)
