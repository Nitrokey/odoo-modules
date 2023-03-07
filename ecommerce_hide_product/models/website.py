from odoo import models


class Website(models.Model):
    _inherit = "website"

    def sale_product_domain(self):
        domain = super().sale_product_domain()
        domain += [("hide_accessory_product", "=", False)]
        return domain
