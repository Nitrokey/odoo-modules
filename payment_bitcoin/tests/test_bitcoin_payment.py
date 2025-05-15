from datetime import datetime
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class MockResponse:
    """Mock response object for requests.get"""

    def __init__(self, json_data, status_code=200, content=None):
        self.json_data = json_data
        self.status_code = status_code
        self.content = content

    def json(self):
        return self.json_data


@tagged("post_install", "-at_install")
class TestBitcoinPayment(TransactionCase):
    """Test Bitcoin payment flow with mocked blockchain.info responses"""

    def setUp(self):
        super().setUp()
        # Create a partner
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "test@example.com",
            }
        )

        # Create a product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
            }
        )

        # Get Bitcoin payment acquirer
        self.bitcoin_acquirer = self.env["payment.acquirer"].search(
            [("provider", "=", "bitcoin")], limit=1
        )

        if not self.bitcoin_acquirer:
            # Create Bitcoin payment acquirer if not found
            self.bitcoin_acquirer = self.env["payment.acquirer"].create(
                {
                    "name": "Bitcoin",
                    "provider": "bitcoin",
                    "company_id": self.env.company.id,
                    "state": "test",
                    "bitcoin_order_older_than": 6,
                    "deadline": 60.0,
                }
            )

        # Create a Bitcoin address
        self.bitcoin_address = self.env["bitcoin.address"].create(
            {
                "name": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
            }
        )

        # Create a Bitcoin rate
        self.bitcoin_rate = self.env["bitcoin.rate"].search([], limit=1)
        if not self.bitcoin_rate:
            self.bitcoin_rate = self.env["bitcoin.rate"].create(
                {
                    "url": "https://blockchain.info/tobtc?currency={CURRENCY}&value={AMOUNT}",
                    "markup": 0.0,
                    "unit": "BTC",
                    "digits": 8,
                    "valid_minutes": 20,
                }
            )

    def _mock_blockchain_info_rate(self, url, *args, **kwargs):
        """Mock blockchain.info rate API response"""
        # Return a fixed BTC rate (0.00001234 BTC per currency unit)
        return MockResponse({}, status_code=200, content=b"0.00001234")

    def _mock_blockchain_info_latest_block(self, url, *args, **kwargs):
        """Mock blockchain.info latest block API response"""
        return MockResponse(
            {
                "height": 800000,  # Current block height
            }
        )

    def _mock_blockchain_info_address_with_payment(self, url, *args, **kwargs):
        """Mock blockchain.info address API response with payment received"""
        return MockResponse(
            {
                "address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
                "total_received": 123400000,  # 1.234 BTC in satoshis
                "txs": [
                    {
                        "hash": (
                            "6eb38d0fdf73c7c6ea30d5bc0e5378d9d1c81c1b5a6c4f0a8f595f7c7ad3c2a0"
                        ),
                        "time": int(datetime.now().timestamp()),
                    }
                ],
            }
        )

    def _mock_blockchain_info_address_no_payment(self, url, *args, **kwargs):
        """Mock blockchain.info address API response with no payment received"""
        return MockResponse(
            {
                "address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
                "total_received": 0,  # No BTC received
                "txs": [],  # No transactions
            }
        )

    def _mock_blockchain_info_address_insufficient_payment(self, url, *args, **kwargs):
        """Mock blockchain.info address API response with insufficient payment"""
        return MockResponse(
            {
                "address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
                "total_received": 50000000,  # 0.5 BTC in satoshis (less than required)
                "txs": [
                    {
                        "hash": (
                            "6eb38d0fdf73c7c6ea30d5bc0e5378d9d1c81c1b5a6c4f0a8f595f7c7ad3c2a0"
                        ),
                        "time": int(datetime.now().timestamp()),
                    }
                ],
            }
        )

    def _mock_blockchain_info_address(self, url, *args, **kwargs):
        """Mock blockchain.info address API response (default implementation)"""
        return self._mock_blockchain_info_address_with_payment(url, *args, **kwargs)

    def _mock_blockchain_info_transaction(self, url, *args, **kwargs):
        """Mock blockchain.info transaction API response"""
        return MockResponse(
            {
                "hash": (
                    "6eb38d0fdf73c7c6ea30d5bc0e5378d9d1c81c1b5a6c4f0a8f595f7c7ad3c2a0"
                ),
                "block_height": 799990,  # Transaction block height
            }
        )

    def _get_mock_response(self, url, *args, **kwargs):
        """Return appropriate mock response based on the URL"""
        if "tobtc" in url:
            return self._mock_blockchain_info_rate(url, *args, **kwargs)
        elif "latestblock" in url:
            return self._mock_blockchain_info_latest_block(url, *args, **kwargs)
        elif "rawaddr" in url:
            return self._mock_blockchain_info_address(url, *args, **kwargs)
        elif "rawtx" in url:
            return self._mock_blockchain_info_transaction(url, *args, **kwargs)
        return MockResponse({}, status_code=404)

    @patch("odoo.addons.payment_bitcoin.models.bitcoin.requests.get")
    def test_bitcoin_payment_flow_successful(self, mock_get):
        """Test the Bitcoin payment flow with successful payment"""
        # Configure the mock to use our custom _get_mock_response method
        mock_get.side_effect = self._get_mock_response

        # Create a sale order (in quotation state)
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        # Check that the sale order is in 'draft' state (quotation)
        self.assertEqual(
            sale_order.state,
            "draft",
            "Sale order should be in 'draft' state (quotation)",
        )

        # Create a payment transaction
        transaction = self.env["payment.transaction"].create(
            {
                "acquirer_id": self.bitcoin_acquirer.id,
                "amount": sale_order.amount_total,
                "currency_id": sale_order.currency_id.id,
                "partner_id": self.partner.id,
                "reference": f"BTC-{sale_order.name}",
                "sale_order_ids": [(6, 0, [sale_order.id])],
            }
        )

        # Set Bitcoin address and amount on the transaction
        transaction.write(
            {
                "bitcoin_address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
                "bitcoin_amount": 0.00001234,  # Same as mocked rate
                "bitcoin_unit": "BTC",
            }
        )

        # Check that the transaction has a Bitcoin address and amount
        self.assertTrue(
            transaction.bitcoin_address, "Transaction should have a Bitcoin address"
        )
        self.assertTrue(
            transaction.bitcoin_amount > 0, "Transaction should have a Bitcoin amount"
        )

        # Create a Bitcoin rate line for the sale order
        self.env["bitcoin.rate.line"].create(
            {
                "rate_id": self.bitcoin_rate.id,
                "rate": 0.00001234,  # Same as mocked rate
                "amount": sale_order.amount_total,
                "currency_id": sale_order.currency_id.id,
                "order_id": sale_order.id,
                "name": sale_order.name,
            }
        )

        # Assign the Bitcoin address to the sale order
        self.bitcoin_address.write(
            {
                "order_id": sale_order.id,
            }
        )

        # Run the Bitcoin payment reconciliation cron job
        self.env["bitcoin.address"].cron_bitcoin_payment_reconciliation()

        # Check that the Bitcoin address is marked as used
        self.assertTrue(
            self.bitcoin_address.is_btc_used, "Bitcoin address should be marked as used"
        )

        # Check that the sale order is now in the 'sale' state (confirmed)
        self.assertEqual(
            sale_order.state, "sale", "Sale order should be in 'sale' state (confirmed)"
        )

        # Check that an invoice was created and confirmed
        self.assertTrue(sale_order.invoice_ids, "An invoice should have been created")
        invoice = sale_order.invoice_ids[0]
        self.assertEqual(invoice.state, "posted", "Invoice should be in 'posted' state")

        # Check that a payment was created and reconciled with the invoice
        payments = self.env["account.payment"].search(
            [
                ("partner_id", "=", self.partner.id),
                ("amount", "=", sale_order.amount_total),
            ]
        )
        self.assertTrue(payments, "A payment should have been created")
        payment = payments[0]
        self.assertEqual(payment.state, "posted", "Payment should be in 'posted' state")

        # Check that the invoice is paid
        self.assertEqual(
            invoice.payment_state, "paid", "Invoice should be marked as paid"
        )

    @patch("odoo.addons.payment_bitcoin.models.bitcoin.requests.get")
    def test_bitcoin_payment_flow_no_payment(self, mock_get):
        """Test the Bitcoin payment flow when no payment is received"""

        # Override the default mock to return no payment
        def mock_response_no_payment(url, *args, **kwargs):
            if "tobtc" in url:
                return self._mock_blockchain_info_rate(url, *args, **kwargs)
            elif "latestblock" in url:
                return self._mock_blockchain_info_latest_block(url, *args, **kwargs)
            elif "rawaddr" in url:
                return self._mock_blockchain_info_address_no_payment(
                    url, *args, **kwargs
                )
            elif "rawtx" in url:
                return self._mock_blockchain_info_transaction(url, *args, **kwargs)
            return MockResponse({}, status_code=404)

        mock_get.side_effect = mock_response_no_payment

        # Create a sale order (in quotation state)
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        # Check that the sale order is in 'draft' state (quotation)
        self.assertEqual(
            sale_order.state,
            "draft",
            "Sale order should be in 'draft' state (quotation)",
        )

        # Create a payment transaction
        transaction = self.env["payment.transaction"].create(
            {
                "acquirer_id": self.bitcoin_acquirer.id,
                "amount": sale_order.amount_total,
                "currency_id": sale_order.currency_id.id,
                "partner_id": self.partner.id,
                "reference": f"BTC-{sale_order.name}",
                "sale_order_ids": [(6, 0, [sale_order.id])],
            }
        )

        # Set Bitcoin address and amount on the transaction
        transaction.write(
            {
                "bitcoin_address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq2",
                "bitcoin_amount": 0.00001234,  # Same as mocked rate
                "bitcoin_unit": "BTC",
            }
        )

        # Check that the transaction has a Bitcoin address and amount
        self.assertTrue(
            transaction.bitcoin_address, "Transaction should have a Bitcoin address"
        )
        self.assertTrue(
            transaction.bitcoin_amount > 0, "Transaction should have a Bitcoin amount"
        )

        # Create a Bitcoin rate line for the sale order
        self.env["bitcoin.rate.line"].create(
            {
                "rate_id": self.bitcoin_rate.id,
                "rate": 0.00001234,  # Same as mocked rate
                "amount": sale_order.amount_total,
                "currency_id": sale_order.currency_id.id,
                "order_id": sale_order.id,
                "name": sale_order.name,
            }
        )

        # Assign the Bitcoin address to the sale order
        bitcoin_address = self.env["bitcoin.address"].create(
            {
                "name": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq2",
            }
        )
        bitcoin_address.write(
            {
                "order_id": sale_order.id,
            }
        )

        # Run the Bitcoin payment reconciliation cron job
        self.env["bitcoin.address"].cron_bitcoin_payment_reconciliation()

        # Check that the Bitcoin address is NOT marked as used
        self.assertFalse(
            bitcoin_address.is_btc_used, "Bitcoin address should NOT be marked as used"
        )

        # Check that the sale order is still in 'draft' state (quotation)
        self.assertEqual(
            sale_order.state,
            "draft",
            "Sale order should still be in 'draft' state (quotation)",
        )

        # Check that no invoice was created
        self.assertFalse(sale_order.invoice_ids, "No invoice should have been created")

    @patch("odoo.addons.payment_bitcoin.models.bitcoin.requests.get")
    def test_bitcoin_payment_flow_insufficient_payment(self, mock_get):
        """Test the Bitcoin payment flow when insufficient payment is received"""

        # Override the default mock to return insufficient payment
        def mock_response_insufficient_payment(url, *args, **kwargs):
            if "tobtc" in url:
                return self._mock_blockchain_info_rate(url, *args, **kwargs)
            elif "latestblock" in url:
                return self._mock_blockchain_info_latest_block(url, *args, **kwargs)
            elif "rawaddr" in url:
                return self._mock_blockchain_info_address_insufficient_payment(
                    url, *args, **kwargs
                )
            elif "rawtx" in url:
                return self._mock_blockchain_info_transaction(url, *args, **kwargs)
            return MockResponse({}, status_code=404)

        mock_get.side_effect = mock_response_insufficient_payment

        # Create a sale order (in quotation state)
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        # Check that the sale order is in 'draft' state (quotation)
        self.assertEqual(
            sale_order.state,
            "draft",
            "Sale order should be in 'draft' state (quotation)",
        )

        # Create a payment transaction
        transaction = self.env["payment.transaction"].create(
            {
                "acquirer_id": self.bitcoin_acquirer.id,
                "amount": sale_order.amount_total,
                "currency_id": sale_order.currency_id.id,
                "partner_id": self.partner.id,
                "reference": f"BTC-{sale_order.name}",
                "sale_order_ids": [(6, 0, [sale_order.id])],
            }
        )

        # Set Bitcoin address and amount on the transaction
        transaction.write(
            {
                "bitcoin_address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq3",
                "bitcoin_amount": 0.00001234,  # Same as mocked rate
                "bitcoin_unit": "BTC",
            }
        )

        # Check that the transaction has a Bitcoin address and amount
        self.assertTrue(
            transaction.bitcoin_address, "Transaction should have a Bitcoin address"
        )
        self.assertTrue(
            transaction.bitcoin_amount > 0, "Transaction should have a Bitcoin amount"
        )

        # Create a Bitcoin rate line for the sale order
        self.env["bitcoin.rate.line"].create(
            {
                "rate_id": self.bitcoin_rate.id,
                "rate": 1.234,  # Higher than the mocked payment (0.5 BTC)
                "amount": sale_order.amount_total,
                "currency_id": sale_order.currency_id.id,
                "order_id": sale_order.id,
                "name": sale_order.name,
            }
        )

        # Assign the Bitcoin address to the sale order
        bitcoin_address = self.env["bitcoin.address"].create(
            {
                "name": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq3",
            }
        )
        bitcoin_address.write(
            {
                "order_id": sale_order.id,
            }
        )

        # Run the Bitcoin payment reconciliation cron job
        self.env["bitcoin.address"].cron_bitcoin_payment_reconciliation()

        # Check that the Bitcoin address is NOT marked as used
        self.assertFalse(
            bitcoin_address.is_btc_used, "Bitcoin address should NOT be marked as used"
        )

        # Check that the sale order is still in 'draft' state (quotation)
        self.assertEqual(
            sale_order.state,
            "draft",
            "Sale order should still be in 'draft' state (quotation)",
        )

        # Check that no invoice was created
        self.assertFalse(sale_order.invoice_ids, "No invoice should have been created")

        # Check that a message was posted on the sale order about insufficient payment
        messages = self.env["mail.message"].search(
            [
                ("model", "=", "sale.order"),
                ("res_id", "=", sale_order.id),
                ("body", "ilike", "%missing%BTC%"),
            ]
        )
        self.assertTrue(
            messages, "A message about insufficient payment should have been posted"
        )
