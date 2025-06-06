# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleOrderPickingHoldPaid(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "invoice_policy": "order",
            }
        )

        # Create payment terms
        self.payment_term_normal = self.env["account.payment.term"].create(
            {
                "name": "Normal Payment Term",
                "hold_picking_until_paid": False,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 30,
                        },
                    ),
                ],
            }
        )

        self.payment_term_hold = self.env["account.payment.term"].create(
            {
                "name": "Hold Until Paid",
                "hold_picking_until_paid": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 30,
                        },
                    ),
                ],
            }
        )

        # Create a customer
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Customer",
                "email": "test@example.com",
            }
        )

        # Create MTO + Manufacturing product
        self.mto_route = self.env.ref("stock.route_warehouse0_mto")
        self.manufacture_route = self.env.ref("mrp.route_warehouse0_manufacture")

        self.product_mto_mfg = self.env["product.product"].create(
            {
                "name": "Test MTO+MFG Product",
                "type": "product",
                "invoice_policy": "order",
                "route_ids": [(6, 0, [self.mto_route.id, self.manufacture_route.id])],
            }
        )

        # Create BOM for the MTO+MFG product
        bom_form = Form(self.env["mrp.bom"])
        bom_form.product_tmpl_id = self.product_mto_mfg.product_tmpl_id
        bom_form.product_qty = 1.0
        with bom_form.bom_line_ids.new() as line:
            line.product_id = self.product
            line.product_qty = 1.0
        self.bom = bom_form.save()

    def _create_sale_order(self, payment_term, products=None):
        """Helper to create a sale order with specific payment term."""
        if products is None:
            products = [(self.product, 1)]

        so_form = Form(self.env["sale.order"])
        so_form.partner_id = self.partner
        so_form.payment_term_id = payment_term

        for product, qty in products:
            with so_form.order_line.new() as line:
                line.product_id = product
                line.product_uom_qty = qty

        return so_form.save()

    def _create_invoice(self, sale_order):
        """Helper to create and post an invoice for a sale order."""
        # Create invoice
        wiz = (
            self.env["sale.advance.payment.inv"]
            .with_context(active_ids=sale_order.ids, active_model="sale.order")
            .create({"advance_payment_method": "delivered"})
        )
        wiz.create_invoices()

        # Get the invoice and post it
        invoice = sale_order.invoice_ids[0]
        invoice.action_post()

        return invoice

    def test_normal_payment_term(self):
        """Test that pickings are created normally with regular payment terms."""
        # Create and confirm sale order with normal payment term
        sale_order = self._create_sale_order(self.payment_term_normal)
        sale_order.action_confirm()

        # Check that no delivery block was set
        self.assertFalse(
            sale_order.delivery_block_id,
            "No delivery block should be set with normal payment term",
        )

        # Check that picking was created
        self.assertTrue(
            sale_order.picking_ids, "Picking should be created with normal payment term"
        )

    def test_hold_payment_term(self):
        """Test that pickings are held with hold_picking_until_paid payment term."""
        # Create and confirm sale order with hold payment term
        sale_order = self._create_sale_order(self.payment_term_hold)
        sale_order.action_confirm()

        # Check that delivery block was automatically set
        self.assertTrue(
            sale_order.delivery_block_id,
            "Delivery block should be set with hold payment term",
        )

        # Check that the delivery block has remove_on_payment enabled
        self.assertTrue(
            sale_order.delivery_block_id.remove_on_payment,
            "Delivery block should have remove_on_payment enabled",
        )

        # Check that no picking was created
        self.assertFalse(
            sale_order.picking_ids, "No picking should be created with delivery block"
        )

        # Create and post invoice
        invoice = self._create_invoice(sale_order)

        # Still no picking as invoice is not paid
        self.assertFalse(
            sale_order.picking_ids,
            "No picking should be created when invoice is not paid",
        )

        # Register payment
        self._register_payment(invoice)

        # Now delivery block should be removed and picking should be created
        self.assertFalse(
            sale_order.delivery_block_id,
            "Delivery block should be removed after payment",
        )
        self.assertTrue(
            sale_order.picking_ids, "Picking should be created after invoice is paid"
        )

    def test_manufacturing_orders(self):
        """Test that manufacturing orders are created even with hold payment term."""
        # Create and confirm sale order with hold payment term and MTO+MFG product
        sale_order = self._create_sale_order(
            self.payment_term_hold, products=[(self.product_mto_mfg, 1)]
        )
        sale_order.action_confirm()

        # Check that delivery block was set
        self.assertTrue(
            sale_order.delivery_block_id,
            "Delivery block should be set with hold payment term",
        )

        # Check that no picking was created
        self.assertFalse(
            sale_order.picking_ids, "No picking should be created with delivery block"
        )

        # Create and post invoice
        invoice = self._create_invoice(sale_order)

        # Register payment
        self._register_payment(invoice)

        # Check that manufacturing order was created
        production = self.env["mrp.production"].search(
            [("origin", "like", sale_order.name)]
        )
        self.assertTrue(
            production, "Manufacturing order should be created despite delivery block"
        )

    def test_delivery_block_reason_creation(self):
        """Test that delivery block reason is created automatically."""
        # Get the delivery block reason for the hold payment term
        block_reason = self.payment_term_hold.get_delivery_block_reason()

        self.assertTrue(block_reason, "Delivery block reason should be created")
        self.assertTrue(
            block_reason.remove_on_payment,
            "Delivery block reason should have remove_on_payment enabled",
        )
        self.assertIn(
            "Hold until paid",
            block_reason.name,
            "Delivery block reason name should contain 'Hold until paid'",
        )

    def _register_payment(self, invoice):
        """Helper to register full payment for an invoice."""
        # Get a bank journal
        bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )

        # Find a valid payment method for this journal
        payment_method_line = bank_journal.inbound_payment_method_line_ids[0]

        # Create and post payment
        payment_register = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .create(
                {
                    "payment_date": invoice.date,
                    "journal_id": bank_journal.id,
                    "payment_method_line_id": payment_method_line.id,
                    "amount": invoice.amount_total,
                }
            )
        )
        payment_register._create_payments()
