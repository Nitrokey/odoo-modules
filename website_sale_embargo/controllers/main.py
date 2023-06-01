from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleEXT(WebsiteSale):
    @http.route(["/shop/confirm_order"], type="http", auth="public", website=True)
    def confirm_order(self, **post):
        order = request.website.sale_get_order()
        country_id = order.partner_shipping_id.country_id
        if country_id:
            order.check_for_product_embargo(country_id)

        return super(WebsiteSale, self).confirm_order()
