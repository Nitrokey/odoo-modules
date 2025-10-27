import logging

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestWebsiteSaleEmbargo(TransactionCase):
    """Test website_sale_embargo module functionality"""

    def setUp(self):
        super().setUp()

        # Create countries
        self.country_us = self.env.ref("base.us")
        self.country_de = self.env.ref("base.de")
        self.country_cn = self.env.ref("base.cn")

        # Create HS Code without embargo
        self.hs_code_allowed = self.env["hs.code"].create(
            {
                "local_code": "8523491000",
                "description": "Non-embargoed product code",
            }
        )

        # Create HS Code with embargo (China embargoed)
        self.hs_code_embargoed = self.env["hs.code"].create(
            {
                "local_code": "9999999999",
                "description": "Embargoed product code",
                "country_id": [(6, 0, [self.country_cn.id])],
            }
        )

        # Create products
        self.product_allowed = self.env["product.product"].create(
            {
                "name": "Allowed Product",
                "type": "consu",
                "list_price": 100.0,
                "hs_code_id": self.hs_code_allowed.id,
            }
        )

        self.product_embargoed = self.env["product.product"].create(
            {
                "name": "Embargoed Product",
                "type": "consu",
                "list_price": 200.0,
                "hs_code_id": self.hs_code_embargoed.id,
            }
        )

        self.product_no_hs_code = self.env["product.product"].create(
            {
                "name": "Product Without HS Code",
                "type": "consu",
                "list_price": 50.0,
            }
        )

        # Create partners
        self.partner_us = self.env["res.partner"].create(
            {
                "name": "US Customer",
                "email": "us@example.com",
                "country_id": self.country_us.id,
            }
        )

        self.partner_de = self.env["res.partner"].create(
            {
                "name": "DE Customer",
                "email": "de@example.com",
                "country_id": self.country_de.id,
            }
        )

        self.partner_cn = self.env["res.partner"].create(
            {
                "name": "CN Customer",
                "email": "cn@example.com",
                "country_id": self.country_cn.id,
            }
        )

    def _create_sale_order(self, partner, products):
        """Helper method to create a sale order with products

        Args:
            partner: res.partner record for the customer
            products: list of tuples (product, quantity)

        Returns:
            sale.order record
        """
        order_lines = [
            (
                0,
                0,
                {
                    "product_id": product.id,
                    "product_uom_qty": qty,
                    "price_unit": product.list_price,
                },
            )
            for product, qty in products
        ]

        return self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "partner_invoice_id": partner.id,
                "partner_shipping_id": partner.id,
                "order_line": order_lines,
            }
        )

    # ========================================================================
    # MODEL TESTS: SaleOrder.check_for_product_embargo()
    # ========================================================================

    def test_check_for_product_embargo_with_embargoed_country(self):
        """Test embargo detection for embargoed country"""
        order = self._create_sale_order(self.partner_cn, [(self.product_embargoed, 1)])

        # Check that embargo is detected
        embargo_msg = order.check_for_product_embargo(self.country_cn)

        self.assertTrue(embargo_msg, "Embargo should be detected")
        self.assertIn(
            "Embargoed Product", embargo_msg, "Error message should mention product"
        )
        self.assertIn("China", embargo_msg, "Error message should mention country")

    def test_check_for_product_embargo_with_allowed_country(self):
        """Test no embargo for allowed country"""
        order = self._create_sale_order(self.partner_us, [(self.product_embargoed, 1)])

        # Check that no embargo is detected for US
        embargo_msg = order.check_for_product_embargo(self.country_us)

        self.assertFalse(embargo_msg, "No embargo should be detected for allowed country")

    def test_check_for_product_embargo_without_hs_code(self):
        """Test products without HS code are allowed"""
        order = self._create_sale_order(self.partner_cn, [(self.product_no_hs_code, 1)])

        # Check that products without HS code are allowed
        embargo_msg = order.check_for_product_embargo(self.country_cn)

        self.assertFalse(
            embargo_msg, "Products without HS code should be allowed everywhere"
        )

    def test_check_for_product_embargo_mixed_products(self):
        """Test order with both allowed and embargoed products"""
        order = self._create_sale_order(
            self.partner_cn,
            [(self.product_allowed, 1), (self.product_embargoed, 1)],
        )

        # Check that embargo is detected even with mixed products
        embargo_msg = order.check_for_product_embargo(self.country_cn)

        self.assertTrue(
            embargo_msg, "Embargo should be detected when any product is embargoed"
        )
        self.assertIn(
            "Embargoed Product", embargo_msg, "Error should mention embargoed product"
        )

    def test_check_for_product_embargo_raises_validation_error(self):
        """Test that embargo check can raise ValidationError"""
        order = self._create_sale_order(self.partner_cn, [(self.product_embargoed, 1)])

        # Check that ValidationError is raised when raise_validation=True
        with self.assertRaises(ValidationError) as cm:
            order.check_for_product_embargo(self.country_cn, raise_error=True)

        self.assertIn("Embargoed Product", str(cm.exception))
        self.assertIn("China", str(cm.exception))

    # ========================================================================
    # MODEL TESTS: SaleOrder._action_confirm()
    # ========================================================================

    def test_action_confirm_with_embargo_raises_validation_error(self):
        """Test that order confirmation is blocked for embargoed countries"""
        order = self._create_sale_order(self.partner_cn, [(self.product_embargoed, 1)])

        # Check that ValidationError is raised on confirmation
        with self.assertRaises(ValidationError) as cm:
            order.action_confirm()

        self.assertIn("Embargoed Product", str(cm.exception))
        self.assertIn("China", str(cm.exception))

        # Verify order is still in draft state
        self.assertEqual(order.state, "draft", "Order should remain in draft state")

    def test_action_confirm_without_embargo_succeeds(self):
        """Test that order confirmation succeeds for allowed countries"""
        order = self._create_sale_order(self.partner_us, [(self.product_embargoed, 1)])

        # Check that confirmation succeeds
        order.action_confirm()

        # Verify order is confirmed
        self.assertEqual(order.state, "sale", "Order should be confirmed")

    def test_action_confirm_allowed_product_to_any_country(self):
        """Test that products without embargo can be sold to any country"""
        order = self._create_sale_order(self.partner_cn, [(self.product_allowed, 1)])

        # Check that confirmation succeeds
        order.action_confirm()

        # Verify order is confirmed
        self.assertEqual(order.state, "sale", "Order should be confirmed")

    def test_action_confirm_no_hs_code_to_any_country(self):
        """Test that products without HS code can be sold to any country"""
        order = self._create_sale_order(self.partner_cn, [(self.product_no_hs_code, 1)])

        # Check that confirmation succeeds
        order.action_confirm()

        # Verify order is confirmed
        self.assertEqual(order.state, "sale", "Order should be confirmed")

    # ========================================================================
    # MODEL TESTS: Multiple Embargoed Countries
    # ========================================================================

    def test_multiple_embargoed_countries(self):
        """Test product embargoed to multiple countries"""
        # Add US to embargoed countries for the product
        self.hs_code_embargoed.write(
            {"country_id": [(6, 0, [self.country_cn.id, self.country_us.id])]}
        )

        # Test embargo for China
        order_cn = self._create_sale_order(
            self.partner_cn, [(self.product_embargoed, 1)]
        )
        embargo_msg_cn = order_cn.check_for_product_embargo(self.country_cn)
        self.assertTrue(embargo_msg_cn, "Embargo should be detected for China")

        # Test embargo for US
        order_us = self._create_sale_order(
            self.partner_us, [(self.product_embargoed, 1)]
        )
        embargo_msg_us = order_us.check_for_product_embargo(self.country_us)
        self.assertTrue(embargo_msg_us, "Embargo should be detected for US")

        # Test no embargo for Germany
        order_de = self._create_sale_order(
            self.partner_de, [(self.product_embargoed, 1)]
        )
        embargo_msg_de = order_de.check_for_product_embargo(self.country_de)
        self.assertFalse(
            embargo_msg_de, "No embargo should be detected for non-listed country"
        )

    # ========================================================================
    # MODEL TESTS: Edge Cases
    # ========================================================================

    def test_check_for_product_embargo_empty_order(self):
        """Test embargo check on order without lines"""
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_cn.id,
                "partner_invoice_id": self.partner_cn.id,
                "partner_shipping_id": self.partner_cn.id,
            }
        )

        # Check that no embargo is detected for empty order
        embargo_msg = order.check_for_product_embargo(self.country_cn)

        self.assertFalse(embargo_msg, "Empty order should not trigger embargo")

    def test_check_for_product_embargo_without_country(self):
        """Test embargo check handles missing country gracefully"""
        order = self._create_sale_order(self.partner_cn, [(self.product_embargoed, 1)])

        # Create a partner without country
        partner_no_country = self.env["res.partner"].create(
            {
                "name": "No Country Partner",
                "email": "nocountry@example.com",
            }
        )
        order.partner_shipping_id = partner_no_country

        # Check that it handles missing country without error
        embargo_msg = order.check_for_product_embargo(self.env["res.country"])

        # Should return False since there's no country to check against
        self.assertFalse(
            embargo_msg, "Should handle missing country without error"
        )

    def test_hs_code_country_field_many2many(self):
        """Test that HS code country_id is a proper Many2many field"""
        # Verify the field is Many2many
        hs_code_field = self.env["hs.code"]._fields.get("country_id")
        self.assertIsNotNone(hs_code_field, "country_id field should exist")
        self.assertEqual(
            hs_code_field.type, "many2many", "country_id should be Many2many"
        )

        # Test adding multiple countries
        self.hs_code_allowed.write(
            {"country_id": [(6, 0, [self.country_us.id, self.country_de.id])]}
        )

        self.assertEqual(
            len(self.hs_code_allowed.country_id),
            2,
            "Should have 2 embargoed countries",
        )
        self.assertIn(
            self.country_us, self.hs_code_allowed.country_id, "US should be in list"
        )
        self.assertIn(
            self.country_de, self.hs_code_allowed.country_id, "DE should be in list"
        )

    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================

    def test_full_order_lifecycle_with_embargo(self):
        """Test complete order lifecycle with embargo blocking"""
        # Create order with embargoed product to embargoed country
        order = self._create_sale_order(self.partner_cn, [(self.product_embargoed, 2)])

        # Verify order is in draft
        self.assertEqual(order.state, "draft")

        # Verify embargo detection in check method
        embargo_msg = order.check_for_product_embargo(self.country_cn)
        self.assertTrue(embargo_msg)

        # Verify confirmation is blocked
        with self.assertRaises(ValidationError):
            order.action_confirm()

        # Verify order remains in draft
        self.assertEqual(order.state, "draft")

    def test_full_order_lifecycle_without_embargo(self):
        """Test complete order lifecycle for allowed scenario"""
        # Create order with allowed product
        order = self._create_sale_order(
            self.partner_us,
            [(self.product_allowed, 1), (self.product_no_hs_code, 1)],
        )

        # Verify order is in draft
        self.assertEqual(order.state, "draft")

        # Verify no embargo detected
        embargo_msg = order.check_for_product_embargo(self.country_us)
        self.assertFalse(embargo_msg)

        # Verify confirmation succeeds
        order.action_confirm()

        # Verify order is confirmed
        self.assertEqual(order.state, "sale")

    def test_change_shipping_address_triggers_embargo(self):
        """Test changing shipping address from allowed to embargoed country"""
        # Create order to allowed country
        order = self._create_sale_order(self.partner_us, [(self.product_embargoed, 1)])

        # Verify no embargo for US
        embargo_msg = order.check_for_product_embargo(self.country_us)
        self.assertFalse(embargo_msg)

        # Change shipping to embargoed country
        order.partner_shipping_id = self.partner_cn

        # Verify embargo is now detected
        embargo_msg = order.check_for_product_embargo(self.country_cn)
        self.assertTrue(embargo_msg)

        # Verify confirmation is blocked
        with self.assertRaises(ValidationError):
            order.action_confirm()
