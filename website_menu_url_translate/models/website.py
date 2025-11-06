from odoo import fields, models


class WebsiteMenu(models.Model):
    _inherit = "website.menu"

    url = fields.Char(translate=True)


class WebsitePage(models.Model):
    _inherit = "website.page"

    url = fields.Char("Page URL", translate=True)

    def action_edit_page_form(self):
        """Open the page in form view from tree."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Edit Website Page",
            "res_model": "website.page",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }
