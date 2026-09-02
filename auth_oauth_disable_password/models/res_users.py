from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    _inherit = "res.users"

    disable_password_login = fields.Boolean(
        compute="_compute_disable_password_login",
        store=True,
        readonly=False,
    )

    @api.depends(
        lambda self: [
            "oauth_access_token",
            *(
                ["oauth_access_token_ids"]
                if "oauth_access_token_ids" in self._fields
                else []
            ),
        ]
    )
    def _compute_disable_password_login(self):
        # auth_oauth_multi_token makes oauth_access_token a required master UUID
        # set for every user, so use oauth_access_token_ids when available.
        for rec in self:
            if "oauth_access_token_ids" in rec._fields:
                rec.disable_password_login = bool(rec.oauth_access_token_ids)
            else:
                rec.disable_password_login = bool(rec.oauth_access_token)

    def _crypt_context(self):
        # The correct `_check_credentials` is not hookable because multiple modules
        # are overwritting them. Blocking the crypt context only infuences password
        # check. res.users.apikeys uses a static crypt context
        if self.disable_password_login:
            raise AccessDenied(_("Password login is disabled"))

        return super()._crypt_context()
