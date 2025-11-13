from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    _inherit = "res.users"

    disable_password_login = fields.Boolean(
        compute="_compute_disable_password_login",
        store=True,
        readonly=False,
    )

    @api.depends("oauth_access_token")
    def _compute_disable_password_login(self):
        for rec in self:
            rec.disable_password_login = rec.oauth_access_token

    def _crypt_context(self):
        # The correct `_check_credentials` is not hookable because multiple modules
        # are overwritting them. Blocking the crypt context only infuences password
        # check. res.users.apikeys uses a static crypt context
        if self.disable_password_login:
            raise AccessDenied(_("Password login is disabled"))

        return super()._crypt_context()
