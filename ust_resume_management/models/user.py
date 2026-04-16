from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    # role_names = fields.Char(
    # compute='_compute_role_names',
    # inverse='_set_role_names',
    # string="User Roles",
    # store=False,
    # ompute_sudo=True,
    # )

# @api.depends("role_line_ids.is_enabled", "role_line_ids.role_id", "role_line_ids.role_id.name")
# def _compute_role_names(self):
#   for user in self.sudo():
#      enabled_lines = user.role_line_ids.filtered(lambda l: l.is_enabled)
#     names = enabled_lines.mapped("role_id.name")
#    user.role_names = ", ".join(names) if names else ""

# def _set_role_names(self):
#   for user in self:
#      if not user.role_names:
#          user.role_line_ids = [(5, 0, 0)]  # Unlink all existing role lines
#         continue

#    role_names = [name.strip() for name in user.role_names.split(",") if name.strip()]
#   existing_roles = self.env['res.users.role'].search([('name', 'in', role_names)])
#  existing_role_names = existing_roles.mapped('name')

# invalid_roles = [name for name in role_names if name not in existing_role_names]
# if invalid_roles:
#   raise ValidationError(f"Invalid role(s) specified: {', '.join(invalid_roles)}. Please ensure these roles exist in the system.")

# new_role_lines = []
# for role_name in role_names:
#   role = existing_roles.filtered(lambda r: r.name == role_name)
#  new_role_lines.append((0, 0, {
#     'role_id': role.id,
#    'date_from': False,
#   'date_to': False,
#  'is_enabled': True,
# }))

# user.role_line_ids = [(5, 0, 0)] + new_role_lines
