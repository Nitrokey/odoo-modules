from odoo.tests.common import TransactionCase


class TestDefaultPaymentTerm(TransactionCase):
    """Test the default payment term functionality."""

    def setUp(self):
        super().setUp()
        # Create test data
        self.payment_term_1 = self.env["account.payment.term"].create(
            {
                "name": "Test Payment Term 1",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 0,
                        },
                    )
                ],
            }
        )
        self.payment_term_2 = self.env["account.payment.term"].create(
            {
                "name": "Test Payment Term 2",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 30,
                        },
                    )
                ],
            }
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

    def test_default_payment_term(self):
        """Test that the first payment term is set as default for new sales orders."""
        # Get the first payment term from the system using default ordering (sequence, id)
        first_payment_term = self.env["account.payment.term"].search([], limit=1)

        # Make sure we have the actual ID for comparison
        self.assertTrue(
            first_payment_term.exists(),
            "At least one payment term must exist in the system",
        )

        # Create a new sales order
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        # Check that the payment term is set to the first payment term
        self.assertEqual(
            sale_order.payment_term_id.id,
            first_payment_term.id,
            "The default payment term should be the first one in the system",
        )

    def test_manual_payment_term_selection(self):
        """Test that a manually selected payment term is respected."""
        # Create a new sales order with a specific payment term
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "payment_term_id": self.payment_term_2.id,
            }
        )

        # Check that the payment term is set to the specified payment term
        self.assertEqual(
            sale_order.payment_term_id,
            self.payment_term_2,
            "The payment term should be the one specified during creation",
        )

    def test_partner_payment_term(self):
        """Test that the partner's payment term is used when available."""
        # Set a payment term on the partner
        self.partner.property_payment_term_id = self.payment_term_2

        # Verify the partner's payment term is set correctly
        self.assertEqual(
            self.partner.property_payment_term_id.id,
            self.payment_term_2.id,
            "Partner's payment term should be set correctly",
        )

        # Create a new sales order with this partner
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        # Debug: Log payment term IDs
        import logging

        _logger = logging.getLogger(__name__)
        _logger.info(
            "Partner payment term ID: %s", self.partner.property_payment_term_id.id
        )
        _logger.info("Sale order payment term ID: %s", sale_order.payment_term_id.id)
        _logger.info("Test payment term 2 ID: %s", self.payment_term_2.id)

        # Our module sets the default payment term, but the standard Odoo behavior
        # should prioritize the partner's payment term if it exists.
        # This test verifies that the standard behavior is preserved.
        self.assertEqual(
            sale_order.payment_term_id.id,
            self.payment_term_2.id,
            "The payment term should be the one from the partner's property_payment_term_id",
        )

        # Clean up: Unset the payment term on the partner to avoid influencing other tests
        self.partner.property_payment_term_id = False
