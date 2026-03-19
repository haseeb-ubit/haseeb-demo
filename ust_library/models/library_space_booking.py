# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LibrarySpaceBooking(models.Model):
    _name = "library.space.booking"
    _description = "Library Space Booking"
    _inherit = ["mail.thread"]
    _order = "date desc, start_time asc"

    name = fields.Char(default="New", readonly=True, copy=False)
    student_id = fields.Many2one(
        "res.users", string="Student", required=True,
        default=lambda self: self.env.user, tracking=True,
    )
    student_partner_id = fields.Many2one(
        "res.partner", related="student_id.partner_id", store=True, readonly=True,
    )
    space_id = fields.Many2one("library.space", string="Space", required=True, tracking=True)
    date = fields.Date(required=True, tracking=True)
    start_time = fields.Float(string="Start Time", required=True, help="24h format, e.g. 14.5 = 14:30")
    end_time = fields.Float(string="End Time", required=True, help="24h format, e.g. 16.0 = 16:00")
    state = fields.Selection(
        [
            ("requested", "Requested"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
            ("completed", "Completed"),
        ],
        default="confirmed",
        required=True,
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("library.space.booking") or "New"
                )
        return super().create(vals_list)

    @api.constrains("start_time", "end_time")
    def _check_times(self):
        for record in self:
            if record.start_time >= record.end_time:
                raise ValidationError("End time must be after start time.")
            if record.start_time < 0 or record.end_time > 24:
                raise ValidationError("Times must be between 0 and 24.")

    @api.constrains("date")
    def _check_past_date(self):
        for record in self:
            if record.date and record.date < fields.Date.today():
                raise ValidationError("You cannot book a space for a past date.")

    @api.constrains("space_id", "date", "start_time", "end_time", "state")
    def _check_double_booking(self):
        for record in self:
            if record.state in ("cancelled", "completed"):
                continue
            overlapping = self.search_count([
                ("id", "!=", record.id),
                ("space_id", "=", record.space_id.id),
                ("date", "=", record.date),
                ("state", "in", ("requested", "confirmed")),
                ("start_time", "<", record.end_time),
                ("end_time", ">", record.start_time),
            ])
            # Functional Spec Sync: Allow concurrent bookings up to the space's designated capacity
            if overlapping >= record.space_id.capacity:
                raise ValidationError(
                    f"This space has reached its maximum capacity ({record.space_id.capacity}) "
                    "for the selected time slot. Please choose a different time or space."
                )

    def action_confirm(self):
        for record in self:
            record.state = "confirmed"

    def action_cancel(self):
        for record in self:
            record.state = "cancelled"

    def action_complete(self):
        for record in self:
            record.state = "completed"

    @api.model
    def _cron_complete_past_bookings(self):
        """Auto-complete bookings whose date has passed."""
        today = fields.Date.today()
        past_bookings = self.search([
            ("state", "in", ("requested", "confirmed")),
            ("date", "<", today),
        ])
        past_bookings.write({"state": "completed"})
