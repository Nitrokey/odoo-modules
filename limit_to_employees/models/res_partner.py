from odoo import api, models
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_mention_suggestions(self, search, limit=8):
        """override the default method and customize the search filter"""
        search_dom = expression.OR(
            [[("name", "ilike", search)], [("email", "ilike", search)]]
        )
        search_dom = expression.AND([[("active", "=", True)], search_dom])
        fields = ["id", "name", "email"]

        # Search users
        search_dom += [
            ("user_ids", "!=", []),
            ("user_ids.share", "=", False),
            ("user_ids.active", "=", True),
        ]
        users = self.search_read(search_dom, fields, limit=limit)
        return list(users)
