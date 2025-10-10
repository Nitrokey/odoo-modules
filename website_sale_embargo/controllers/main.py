from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route(["/shop/confirm_order"], type="http", auth="public", website=True)
    def confirm_order(self, **post):
        order = request.website.sale_get_order()
        country_id = order.partner_shipping_id.country_id
        if country_id:
            order.check_for_product_embargo(country_id, True)

        return super().confirm_order()

    def get_mode(self, order, **kw):
        Partner = request.env["res.partner"].with_context(show_address=1).sudo()
        mode = (False, False)
        partner_id = int(kw.get("partner_id", -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ("new", "billing")
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ("edit", "billing")
                else:
                    shippings = Partner.search(
                        [("id", "child_of", order.partner_id.commercial_partner_id.ids)]
                    )
                    if order.partner_id.commercial_partner_id.id == partner_id:
                        mode = ("new", "shipping")
                        partner_id = -1
                    elif partner_id in shippings.mapped("id"):
                        mode = ("edit", "shipping")
            elif partner_id == -1:
                mode = ("new", "shipping")
        return mode

    @http.route(
        ["/shop/address"],
        type="http",
        methods=["GET", "POST"],
        auth="public",
        website=True,
        sitemap=False,
    )
    def address(self, **kw):
        order = request.website.sale_get_order()

        check_form_country = kw.get("country_id", False)

        if check_form_country:
            country_id = request.env["res.country"].browse(int(check_form_country))
        else:
            country_id = order.partner_shipping_id.country_id

        mode = self.get_mode(order, **kw)

        if country_id and mode[1] == "shipping":
            embargo_status = order.check_for_product_embargo(country_id)
            if embargo_status:
                errors = {
                    "product_embargo": "error",
                    "error_message": [embargo_status],
                }

                render_values = {
                    "website_sale_order": order,
                    "partner_id": order.partner_id.id,
                    "checkout": kw,
                    "mode": mode,
                    "error": errors,
                    "callback": kw.get("callback"),
                    "only_services": order and order.only_services,
                }
                render_values.update(
                    self._get_country_related_render_values(kw, render_values)
                )
                return request.render("website_sale.address", render_values)

        return super().address(**kw)
