from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

from ..models.phone_validation_mixin import phone_format


class WebsiteSaleExt(WebsiteSale):
    @http.route(
        ["/shop/address"],
        type="http",
        methods=["GET", "POST"],
        auth="public",
        website=True,
        sitemap=False,
    )
    def address(self, **kw):
        response = super().address(**kw)
        Partner = request.env["res.partner"].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()
        errors = {}
        partner_id = int(kw.get("partner_id", -1))

        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ("new", "billing")
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ("edit", "billing")
                else:
                    shippings = Partner.search(
                        [("id", "child_of", order.partner_id.commercial_partner_id.ids)]
                    )
                    if partner_id in shippings.mapped("id"):
                        mode = ("edit", "shipping")
                    else:
                        return Forbidden()
                if mode:
                    Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ("new", "shipping")
            else:  # no mode - refresh without post?
                return request.redirect("/shop/checkout")

        # IF POSTED
        if "submitted" in kw:
            if kw.get("phone") and kw.get("country_id"):
                country_id = request.env["res.country"].browse(
                    int(kw.get("country_id"))
                )
                formated_vals = phone_format(
                    kw.get("phone"),
                    country_id.code if country_id else None,
                    country_id.phone_code if country_id else None,
                    force_format="E164",
                    raise_exception=False,
                )
                kw.update({"phone": formated_vals})

            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(
                order, mode, pre_values, errors, error_msg
            )

            if errors:
                errors["error_message"] = error_msg
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                if mode[1] == "billing":
                    order.partner_id = partner_id
                    order.onchange_partner_id()
                    order.partner_invoice_id = partner_id
                    if not kw.get("use_same"):
                        kw["callback"] = kw.get("callback") or (
                            not order.only_services
                            and (
                                mode[0] == "edit"
                                and "/shop/checkout"
                                or "/shop/address"
                            )
                        )
                elif mode[1] == "shipping":
                    order.partner_shipping_id = partner_id

                if not errors:
                    return request.redirect(kw.get("callback") or "/shop/confirm_order")

        return response
