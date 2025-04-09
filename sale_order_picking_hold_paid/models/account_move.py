# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        """Check if pickings should be created when invoice is posted."""
        result = super()._post(soft=soft)
        self._check_sale_order_pickings()
        return result

    def write(self, vals):
        """Check if pickings should be created when payment state changes."""
        result = super().write(vals)
        if "payment_state" in vals:
            self._check_sale_order_pickings()
        return result
        
    def action_invoice_paid(self):
        """Check if pickings should be created when invoice is paid directly."""
        _logger.info("action_invoice_paid called for invoices: %s", self.ids)
        result = super().action_invoice_paid()
        self._check_sale_order_pickings()
        return result

    def _check_sale_order_pickings(self):
        """Create pickings for sale orders if they are now fully paid."""
        _logger.info("_check_sale_order_pickings called for invoices: %s", self.ids)
        
        # Try multiple approaches to find related sale orders
        orders = self.env["sale.order"]
        
        # 1. Try through invoice lines
        line_orders = self.mapped("invoice_line_ids.sale_line_ids.order_id")
        orders |= line_orders
        _logger.info("Orders found through invoice lines: %s", line_orders.ids)
        
        # 2. Try through invoice origin (often contains sale order name)
        for move in self.filtered(lambda m: m.move_type == "out_invoice" and m.state == "posted"):
            if move.invoice_origin:
                origin_orders = self.env["sale.order"].search(
                    [("name", "=", move.invoice_origin)]
                )
                orders |= origin_orders
                _logger.info(
                    "Orders found through invoice origin %s: %s", 
                    move.invoice_origin, 
                    origin_orders.ids
                )
        
        # 3. Try through direct relationship in sale.order
        for move in self:
            related_orders = self.env["sale.order"].search(
                [("invoice_ids", "in", move.id)]
            )
            orders |= related_orders
            _logger.info(
                "Orders found through direct relationship for invoice %s: %s", 
                move.id, 
                related_orders.ids
            )
        
        _logger.info("Total found related sale orders: %s", orders.ids)

        # Only process orders with hold_picking_until_paid
        orders_to_check = orders.filtered(lambda o: o.picking_hold_until_paid)
        _logger.info("Orders with hold_picking_until_paid: %s", orders_to_check.ids)

        if not orders_to_check:
            _logger.info("No orders with hold_picking_until_paid found, returning")
            return

        # Find orders that are fully invoiced
        fully_invoiced = orders_to_check.filtered(
            lambda o: o.invoice_status == "invoiced"
        )
        _logger.info("Fully invoiced orders: %s", fully_invoiced.ids)

        # From fully invoiced orders, find those where all invoices are paid
        fully_paid = self.env["sale.order"]
        for order in fully_invoiced:
            _logger.info(
                "Checking order %s, invoice_ids: %s", 
                order.id, 
                order.invoice_ids.ids
            )
            posted_invoices = order.invoice_ids.filtered(lambda i: i.state == "posted")
            _logger.info(
                "Posted invoices for order %s: %s", 
                order.id, 
                posted_invoices.ids
            )

            all_paid = all(inv.payment_state == "paid" for inv in posted_invoices)
            _logger.info(
                "All invoices paid for order %s: %s", 
                order.id, 
                all_paid
            )

            if all_paid:
                fully_paid += order

        _logger.info("Fully paid orders: %s", fully_paid.ids)

        # Create pickings for fully paid orders
        if fully_paid:
            _logger.info("Calling create_pickings_if_paid for orders: %s", fully_paid.ids)
            fully_paid.create_pickings_if_paid()
