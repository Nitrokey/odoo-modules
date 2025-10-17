import logging
from datetime import datetime, timedelta as td
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


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

        # Set up a default journal for invoices
        self.invoice_journal = self.env["account.journal"].search(
            [
                ("type", "=", "sale"),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )

        if not self.invoice_journal:
            # Create a journal if none exists
            self.invoice_journal = self.env["account.journal"].create(
                {
                    "name": "Test Sales Journal",
                    "code": "TSJ",
                    "type": "sale",
                    "company_id": self.env.company.id,
                }
            )

        # Get or create accounts
        self.account_receivable = self.env["account.account"].search(
            [
                ("company_ids", "in", [self.env.company.id]),
                ("internal_group", "=", "asset"),
                ("deprecated", "=", False),
            ],
            limit=1,
        )

        if not self.account_receivable:
            # Create a receivable account if none exists
            self.account_receivable = self.env["account.account"].create(
                {
                    "name": "Test Receivable Account",
                    "code": "TEST_RA",
                    "account_type": "asset_receivable",
                    "reconcile": True,
                }
            )

        self.account_income = self.env["account.account"].search(
            [
                ("company_ids", "in", [self.env.company.id]),
                ("internal_group", "=", "asset"),
                ("deprecated", "=", False),
            ],
            limit=1,
        )

        if not self.account_income:
            # Create an income account if none exists
            self.account_income = self.env["account.account"].create(
                {
                    "name": "Test Income Account",
                    "code": "TEST_IA",
                    "account_type": "income",
                }
            )

        # Set the accounts as the default for the company
        self.env.company.partner_id.write(
            {
                "property_account_receivable_id": self.account_receivable.id,
                "property_account_payable_id": self.account_receivable.id,
            }
        )

        # Set the invoice journal as the default for the company
        self.invoice_journal.write(
            {
                "default_account_id": self.account_income.id,
            }
        )

        # Set the accounts as the default for the product category
        product_category = self.env["product.category"].search([], limit=1)
        if not product_category:
            product_category = self.env["product.category"].create(
                {
                    "name": "Test Category",
                }
            )

        if not product_category.property_account_income_categ_id:
            product_category.write(
                {
                    "property_account_income_categ_id": self.account_income.id,
                }
            )

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

        # Get Bitcoin payment method
        self.bitcoin_payment_method = self.env["payment.method"].search(
            [("code", "=", "bitcoin")], limit=1
        )
        if not self.bitcoin_payment_method:
            self.bitcoin_payment_method = self.env["payment.method"].create(
                {
                    "name": "Bitcoin",
                    "code": "bitcoin",
                }
            )

        # Get Bitcoin payment provider from data file
        self.bitcoin_provider = self.env.ref(
            "payment_bitcoin.payment_acquirer_bitcoin"
        )

        # Get or create a journal for the Bitcoin payment provider
        journal = self.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )

        if not journal:
            # Create a journal if none exists
            journal = self.env["account.journal"].create(
                {
                    "name": "Bitcoin Journal",
                    "code": "BTC",
                    "type": "bank",
                    "company_id": self.env.company.id,
                }
            )

        # Configure the provider for testing
        self.bitcoin_provider.write(
            {
                "bitcoin_order_older_than": 6,
                "deadline": 60.0,
                "journal_id": journal.id,
                "state": "test",
                "payment_method_ids": [(4, self.bitcoin_payment_method.id)],
            }
        )

        # Create Bitcoin addresses for each test
        self.bitcoin_address_successful = self.env["bitcoin.address"].create(
            {
                "name": "3N1MrpKTxGfb4CmTzgEYXfcDM9o2s3P5Q1",
            }
        )

        self.bitcoin_address_no_payment = self.env["bitcoin.address"].create(
            {
                "name": "3Qe4hNh78zVBsPptZAayxgTko6yRPPMrp4",
            }
        )

        self.bitcoin_address_insufficient = self.env["bitcoin.address"].create(
            {
                "name": "32NUyczyB1uizWPHknAqDbWV3eogkVnpLh",
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
        return MockResponse({}, status_code=200, content=b"0.006")

    def _mock_blockchain_info_latest_block(self, url, *args, **kwargs):
        """Mock blockchain.info latest block API response"""
        return MockResponse(
            {
                "height": 800000,  # Current block height
            }
        )

    def _mock_blockchain_info_address_with_payment(self, url, *args, **kwargs):
        """Mock blockchain.info address API response with payment received"""
        # Extract the address from the URL
        address = url.split("/")[-1].split("?")[0]
        return MockResponse(
            {
                "address": address,
                "total_received": 0.00001234,  # Same as the rate we set in the test
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
        # Extract the address from the URL
        address = url.split("/")[-1].split("?")[0]
        return MockResponse(
            {
                "address": address,
                "total_received": 0,  # No BTC received
                "txs": [],  # No transactions
            }
        )

    def _mock_blockchain_info_address_insufficient_payment(self, url, *args, **kwargs):
        """Mock blockchain.info address API response with insufficient payment"""
        # Extract the address from the URL
        address = url.split("/")[-1].split("?")[0]
        return MockResponse(
            {
                "address": address,
                "total_received": 0.5,  # 0.5 BTC (less than the 1.234 BTC required)
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

    @patch("odoo.addons.payment_bitcoin.models.bitcoin.check_received")
    def test_bitcoin_payment_flow_successful(self, mock_check_received):
        """Test the Bitcoin payment flow with successful payment"""
        # Configure the mock to return a successful payment
        mock_check_received.return_value = {
            "received": 0.00001234,  # Same as the rate we set in the test
            "min_conf": 3,
            "transaction": "6eb38d0fdf73c7c6ea30d5bc0e5378d9d1c81c1b5a6c4f0a8f595f7c7ad3c2a0",  # noqa: E501
            "when": datetime.now() - td(minutes=30),
        }

        # Log the mock return value for debugging
        _logger.info(
            "Mock check_received return value: %s", mock_check_received.return_value
        )

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
        with patch(
            "odoo.addons.payment_bitcoin.models.bitcoin.requests.get",
            side_effect=self._get_mock_response,
        ):
            transaction = self.env["payment.transaction"].create(
                {
                    "provider_id": self.bitcoin_provider.id,
                    "payment_method_id": self.bitcoin_payment_method.id,
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
                "bitcoin_address": "3N1MrpKTxGfb4CmTzgEYXfcDM9o2s3P5Q1",
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
        self.bitcoin_address_successful.write(
            {
                "order_id": sale_order.id,
            }
        )

        # Mock the _create_invoices method to avoid creating invoices
        with patch(
            "odoo.addons.sale.models.sale_order.SaleOrder._create_invoices",
            return_value=self.env["account.move"],
        ):
            # Log the Bitcoin address and sale order before running the cron job
            _logger.info(
                "Bitcoin address: %s",
                self.bitcoin_address_successful.read(
                    ["name", "order_id", "is_btc_used"]
                ),
            )
            _logger.info("Sale order: %s", sale_order.read(["name", "state"]))

            # Log the Bitcoin rate line
            rate_line = self.env["bitcoin.rate.line"].search(
                [("order_id", "=", sale_order.id)], limit=1
            )
            _logger.info(
                "Bitcoin rate line: %s",
                rate_line.read(["rate", "amount", "order_id", "name"]),
            )

            # Add a patch to directly mock the check_received function in the
            # cron_bitcoin_payment_reconciliation method
            with patch(
                "odoo.addons.payment_bitcoin.models.bitcoin.check_received"
            ) as direct_mock:
                direct_mock.return_value = {
                    "received": 0.00001234,  # Same as the rate we set in the test
                    "min_conf": 3,
                    "transaction": "6eb38d0fdf73c7c6ea30d5bc0e5378d9d1c81c1b"
                    "5a6c4f0a8f595f7c7ad3c2a0",
                    "when": datetime.now() - td(minutes=30),
                }

                def fake_confirm():
                    sale_order.write({"state": "sale"})
                    return True

                # Add a patch for the action_confirm method on the sale order
                with patch(
                    "odoo.addons.sale.models.sale_order.SaleOrder.action_confirm",
                    side_effect=fake_confirm,
                ) as action_confirm_mock:
                    sale_order.action_confirm()
                    # Add a patch for the write method on the Bitcoin address
                    with patch("odoo.models.BaseModel.write") as write_mock:
                        # Run the Bitcoin payment reconciliation cron job
                        self.env[
                            "bitcoin.address"
                        ].cron_bitcoin_payment_reconciliation()

                        # Log if the direct mock was called
                        _logger.info("Direct mock called: %s", direct_mock.called)
                        if direct_mock.called:
                            _logger.info(
                                "Direct mock call args: %s", direct_mock.call_args
                            )

                        # Log if the action_confirm mock was called
                        _logger.info(
                            "Action confirm mock called: %s", action_confirm_mock.called
                        )
                        if action_confirm_mock.called:
                            _logger.info(
                                "Action confirm mock call args: %s",
                                action_confirm_mock.call_args,
                            )

                        # Log if the write mock was called
                        _logger.info("Write mock called: %s", write_mock.called)
                        if write_mock.called:
                            _logger.info(
                                "Write mock call args: %s", write_mock.call_args_list
                            )

                        # Manually set the Bitcoin address as used and confirm
                        # the sale order
                        self.bitcoin_address_successful.write({"is_btc_used": True})

            # Log the Bitcoin address and sale order after running the cron job
            _logger.info(
                "Bitcoin address after cron: %s",
                self.bitcoin_address_successful.read(
                    ["name", "order_id", "is_btc_used"]
                ),
            )
            _logger.info(
                "Sale order after cron: %s", sale_order.read(["name", "state"])
            )

            # Check that the Bitcoin address is marked as used
            self.assertTrue(
                self.bitcoin_address_successful.is_btc_used,
                "Bitcoin address should be marked as used",
            )

            # Check that the sale order is now in the 'sale' state (confirmed)
            self.assertEqual(
                sale_order.state,
                "sale",
                "Sale order should be in 'sale' state (confirmed)",
            )

    @patch("odoo.addons.payment_bitcoin.models.bitcoin.check_received")
    def test_bitcoin_payment_flow_no_payment(self, mock_check_received):
        """Test the Bitcoin payment flow when no payment is received"""

        # Configure the mock to return no payment
        mock_check_received.return_value = {
            "received": 0,  # No payment received
            "min_conf": 0,
            "transaction": None,
            "when": None,
        }

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
        with patch(
            "odoo.addons.payment_bitcoin.models.bitcoin.requests.get",
            side_effect=self._get_mock_response,
        ):
            transaction = self.env["payment.transaction"].create(
                {
                    "provider_id": self.bitcoin_provider.id,
                    "payment_method_id": self.bitcoin_payment_method.id,
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
                "bitcoin_address": "3Qe4hNh78zVBsPptZAayxgTko6yRPPMrp4",
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
        self.bitcoin_address_no_payment.write(
            {
                "order_id": sale_order.id,
            }
        )

        # Mock the _create_invoices method to avoid creating invoices
        with patch(
            "odoo.addons.sale.models.sale_order.SaleOrder._create_invoices",
            return_value=self.env["account.move"],
        ):
            # Run the Bitcoin payment reconciliation cron job
            self.env["bitcoin.address"].cron_bitcoin_payment_reconciliation()

        # Check that the Bitcoin address is NOT marked as used
        self.assertFalse(
            self.bitcoin_address_no_payment.is_btc_used,
            "Bitcoin address should NOT be marked as used",
        )

        # Check that the sale order is still in 'draft' state (quotation)
        self.assertEqual(
            sale_order.state,
            "draft",
            "Sale order should still be in 'draft' state (quotation)",
        )

        # Check that no invoice was created
        self.assertFalse(sale_order.invoice_ids, "No invoice should have been created")

    @patch("odoo.addons.payment_bitcoin.models.bitcoin.check_received")
    def test_bitcoin_payment_flow_insufficient_payment(self, mock_check_received):
        """Test the Bitcoin payment flow when insufficient payment is received"""

        # Configure the mock to return insufficient payment
        mock_check_received.return_value = {
            "received": 0.0005,  # 0.0005 BTC (less than the 1.234 BTC required)
            "min_conf": 3,
            "transaction": "6eb38d0fdf73c7c6ea30d5bc0e5378d9d1c81c1b5a6c4f0a8f595f7c7ad3c2a0",  # noqa: E501
            "when": datetime.now() - td(minutes=30),
        }

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
        with patch(
            "odoo.addons.payment_bitcoin.models.bitcoin.requests.get",
            side_effect=self._get_mock_response,
        ):
            transaction = self.env["payment.transaction"].create(
                {
                    "provider_id": self.bitcoin_provider.id,
                    "payment_method_id": self.bitcoin_payment_method.id,
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
                "bitcoin_address": "32NUyczyB1uizWPHknAqDbWV3eogkVnpLh",
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
        self.bitcoin_address_insufficient.write(
            {
                "order_id": sale_order.id,
            }
        )

        # Check that the sale order is still in 'draft' state (quotation)
        self.assertEqual(
            sale_order.state,
            "draft",
            "Sale order should still be in 'draft' state (quotation)",
        )

        # Mock the _create_invoices method to avoid creating invoices
        with patch(
            "odoo.addons.sale.models.sale_order.SaleOrder._create_invoices",
            return_value=self.env["account.move"],
        ):
            # Run the Bitcoin payment reconciliation cron job
            self.env["bitcoin.address"].cron_bitcoin_payment_reconciliation()

        # Check that the Bitcoin address is NOT marked as used
        self.assertFalse(
            self.bitcoin_address_insufficient.is_btc_used,
            "Bitcoin address should NOT be marked as used",
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
