from odoo import http
from odoo.http import request
from odoo.tools import str2bool

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    @http.route(
        ["/shop/confirm_order"], type="http", auth="public", website=True, sitemap=False
    )
    def shop_confirm_order(self, **post):
        order = request.website.sale_get_order()
        country_id = order.partner_shipping_id.country_id
        if order and country_id:
            order.check_for_product_embargo(country_id, True)

        return super().shop_confirm_order(**post)

    @http.route(
        ["/shop/address"], type="http", methods=["GET"], auth="public", website=True, sitemap=False,
    )
    def shop_address(
        self,
        partner_id=None,
        address_type="billing",
        use_delivery_as_billing=None,
        **query_params
    ):
        order = request.website.sale_get_order()

        if redirection := self._check_cart(order):
            return redirection

        # Check if we're creating/editing a delivery address
        check_form_country = query_params.get("country_id", False)

        if check_form_country:
            country_id = request.env["res.country"].browse(int(check_form_country))
        else:
            country_id = order.partner_shipping_id.country_id

        # Only check embargo for delivery addresses
        if country_id and address_type == "delivery":
            embargo_status = order.check_for_product_embargo(country_id)
            if embargo_status:
                # Get the partner to edit, if any
                partner_sudo, address_type = self._prepare_address_update(
                    order, partner_id=partner_id and int(partner_id), address_type=address_type
                )

                # Get the base render values from parent
                render_values = self._prepare_address_form_values(
                    order,
                    partner_sudo,
                    address_type=address_type,
                    use_delivery_as_billing=str2bool(use_delivery_as_billing or "false"),
                    **query_params
                )

                # Add error information
                errors = {
                    "product_embargo": "error",
                    "error_message": [embargo_status],
                }
                render_values["error"] = errors

                return request.render("website_sale.address", render_values)

        return super().shop_address(
            partner_id=partner_id,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            **query_params
        )
