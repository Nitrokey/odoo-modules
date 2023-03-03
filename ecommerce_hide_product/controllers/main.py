from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route(
        ['/shop/<model("product.template"):product>'],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def product(self, product, category="", search="", **kwargs):
        if product.hide_accessory_product:
            return request.render("website.page_404")
        return super().product(product=product, category=category, search=search)
