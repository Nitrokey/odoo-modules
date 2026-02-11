from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        """Add or set product quantity, add_qty can be negative"""
        self.ensure_one()
        # Retrieve config session ID from kwargs or from existing order line
        config_session_id = kwargs.get("config_session_id")
        if not config_session_id and line_id:
            order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]
            config_session_id = order_line.config_session_id.id
        if config_session_id:
            ctx = {
                "current_sale_line": line_id,
                "default_config_session_id": int(config_session_id),
            }
            self = self.with_context(**ctx)
        # Call base method to handle the cart update
        result = super()._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            **kwargs,
        )
        # If a linked line exists (e.g., configuration line), update its description
        if result.get("line_id"):
            line = self.order_line.browse(result["line_id"])
            if line.linked_line_id:
                product = line.linked_line_id.product_id
                line.linked_line_id.name = (
                    line.linked_line_id._get_sale_order_line_multiline_description_sale(
                        product
                    )
                )
        return result

    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        """Include Config session in search."""
        order_line = super()._cart_find_product_line(
            product_id=product_id, line_id=line_id, **kwargs
        )
        # Onchange quantity in cart
        if line_id:
            return order_line

        config_session_id = kwargs.get("config_session_id", False)
        if not config_session_id:
            return order_line

        order_line = order_line.filtered(
            lambda p: p.config_session_id.id == int(config_session_id)
        )
        return order_line
