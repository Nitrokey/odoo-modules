import json

from odoo import http
from odoo.http import request

from odoo.addons.sale_product_configurator.controllers.main import (
    ProductConfiguratorController,
)
from odoo.addons.website_sale_product_configurator.controllers.main import WebsiteSale


class ProductConfigurator(ProductConfiguratorController):
    @http.route(
        ["/sale_product_configurator/show_advanced_configurator_website"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def show_advanced_configurator_website(self, product_id, variant_values, **kw):
        """Special route to use website logic in get_combination_info override.
        This route is called in JS by appending _website to the base route.
        """
        product = request.env["product.product"].browse(int(product_id))
        res = super().show_advanced_configurator_website(
            product_id, variant_values, **kw
        )
        if not res and product.mandatory_product_ids:
            kw.pop("pricelist_id")
            pricelist = request.website.get_current_pricelist()
            return self.show_advanced_configurator(
                product_id, variant_values, pricelist, **kw
            )
        return res

    def _show_advanced_configurator(
        self, product_id, variant_values, pricelist, handle_stock, **kw
    ):
        product = request.env["product.product"].browse(product_id)
        if (
            product.mandatory_product_ids
            and "kwargs" in kw
            and not kw["kwargs"]["context"].get("display_optional")
        ):
            product = request.env["product.product"].browse(int(product_id))
            combination = request.env["product.template.attribute.value"].browse(
                variant_values
            )
            add_qty = int(kw.get("add_qty", 1))

            no_variant_attribute_values = combination.filtered(
                lambda product_template_attribute_value: product_template_attribute_value.attribute_id.create_variant  # noqa : E501
                == "no_variant"
            )
            if no_variant_attribute_values:
                product = product.with_context(
                    no_variant_attribute_values=no_variant_attribute_values
                )
            return request.env["ir.ui.view"]._render_template(
                "product_mandatory_products.mandatory_products_modal",
                {
                    "product": product,
                    "combination": combination,
                    "add_qty": add_qty,
                    "parent_name": product.name,
                    "variant_values": variant_values,
                    "pricelist": pricelist,
                    "handle_stock": handle_stock,
                    "already_configured": kw.get("already_configured", False),
                },
            )
        return super()._show_advanced_configurator(
            product_id, variant_values, pricelist, handle_stock, **kw
        )


class WebsiteSaleExtend(WebsiteSale):
    KW = []

    def update_product_and_options(self, product_and_options):
        # Set new parent_unique_id
        uid = json.loads(product_and_options)[0]["unique_id"]
        for i in self.KW:
            i["parent_unique_id"] = uid
        # Update old root product with new values
        self.KW[0].update(json.loads(product_and_options)[0])
        # Add new variants in list
        self.KW.extend(json.loads(product_and_options)[1:])
        return json.dumps(self.KW)

    @http.route(
        ["/shop/cart/update_option"],
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        multilang=False,
    )
    def cart_options_update_json(
        self, product_and_options, goto_shop=None, lang=None, **kwargs
    ):
        if goto_shop == "true":
            if self.KW:
                # Call only when there is mandatory products.
                product_and_options = self.update_product_and_options(
                    product_and_options
                )
            res = super().cart_options_update_json(
                product_and_options, goto_shop=goto_shop, lang=lang, **kwargs
            )
            self.KW = []
            return res
        else:
            self.KW.clear()
            self.KW.extend(json.loads(product_and_options))
            return True

    @http.route(["/shop/check_mendatory_product"], type="json", auth="public")
    def check_mendatory_product(self, *args, **product_data):
        context = product_data["current_context"]
        if context.get("display_optional"):
            return {"has_mandatory": True, "display_optional": False}
        if product_data.get("root_product"):
            root_product_id = (
                request.env["product.product"]
                .sudo()
                .browse(int(product_data["root_product"]))
            )
            is_optional_prod = root_product_id.optional_product_ids
            if root_product_id.mandatory_product_ids:
                if "products" not in product_data:
                    return {"has_mandatory": False}
                product_in_cart = [
                    i
                    for i in root_product_id.mandatory_product_ids.product_variant_ids.ids
                    if i in product_data["products"]
                ]
                if product_in_cart:
                    return {
                        "has_mandatory": True,
                        "display_optional": True if is_optional_prod else False,
                    }
                else:
                    return {
                        "has_mandatory": True,
                        "display_optional": True if is_optional_prod else False,
                    }
            else:
                return {
                    "has_mandatory": False,
                    "display_optional": True if is_optional_prod else False,
                }
        else:
            return True
