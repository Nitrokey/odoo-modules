from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo.exceptions import UserError

import logging

logger = logging.getLogger(__name__)


class WebsiteSaleEXT(WebsiteSale):
    @http.route(
        ["/shop/checkout"], type="http", auth="public", website=True, sitemap=False
    )
    def checkout(self, **post):
        order = request.website.sale_get_order()
        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            country_code = request.session["geoip"].get("country_code")
            if country_code:
                country_id = request.env["res.country"].search(
                    [("code", "=", country_code)], limit=1
                )
            else:
                country_id = request.website.user_id.sudo().country_id
        else:
            country_id = request.env.user.country_id or order.partner_id.country_id

        for rec in order.mapped("order_line"):
            hs_code = rec.product_id.product_tmpl_id.hs_code_id
            if hs_code and hs_code.embargo and country_id == hs_code.country_id:
                raise UserError(
                    _(
                        "Product %s is not available in country %s",
                        rec.product_id.name,
                        hs_code.country_id.name,
                    )
                )

        return super().checkout(**post)
