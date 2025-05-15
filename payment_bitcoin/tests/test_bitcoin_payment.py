from datetime import datetime, timedelta as td
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
                ("company_id", "=", self.env.company.id),
                ("internal_type", "=", "receivable"),
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
                    "user_type_id": self.env.ref(
                        "account.data_account_type_receivable"
                    ).id,
                    "company_id": self.env.company.id,
                    "reconcile": True,
                }
            )

        self.account_income = self.env["account.account"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("internal_type", "=", "other"),
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
                    "user_type_id": self.env.ref(
                        "account.data_account_type_revenue"
                    ).id,
                    "company_id": self.env.company.id,
                }
            )

        # Set the accounts as the default for the company
        self.env.company.write(
            {
                "account_journal_payment_debit_account_id": self.account_receivable.id,
                "account_journal_payment_credit_account_id": self.account_receivable.id,
            }
        )

        # Set the invoice journal as the default for the company
        self.invoice_journal.write(
            {
                "default_account_id": self.account_income.id,
            }
        )

        # Set the accounts as the default for the partner
        # First, check if the properties already exist
        receivable_property = self.env["ir.property"].search(
            [
                ("name", "=", "property_account_receivable_id"),
                ("company_id", "=", self.env.company.id),
                ("res_id", "=", False),
            ],
            limit=1,
        )

        if receivable_property:
            # Update the existing property
            receivable_property.write(
                {
                    "value_reference": f"account.account, {self.account_receivable.id}",
                }
            )
        else:
            # Create a new property
            self.env["ir.property"].create(
                {
                    "name": "property_account_receivable_id",
                    "company_id": self.env.company.id,
                    "type": "many2one",
                    "fields_id": self.env["ir.model.fields"]
                    .search(
                        [
                            ("model", "=", "res.partner"),
                            ("name", "=", "property_account_receivable_id"),
                        ],
                        limit=1,
                    )
                    .id,
                    "value_reference": f"account.account, {self.account_receivable.id}",
                }
            )

        payable_property = self.env["ir.property"].search(
            [
                ("name", "=", "property_account_payable_id"),
                ("company_id", "=", self.env.company.id),
                ("res_id", "=", False),
            ],
            limit=1,
        )

        if payable_property:
            # Update the existing property
            payable_property.write(
                {
                    "value_reference": f"account.account, {self.account_receivable.id}",
                }
            )
        else:
            # Create a new property
            self.env["ir.property"].create(
                {
                    "name": "property_account_payable_id",
                    "company_id": self.env.company.id,
                    "type": "many2one",
                    "fields_id": self.env["ir.model.fields"]
                    .search(
                        [
                            ("model", "=", "res.partner"),
                            ("name", "=", "property_account_payable_id"),
                        ],
                        limit=1,
                    )
                    .id,
                    "value_reference": f"account.account, {self.account_receivable.id}",
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

        income_property = self.env["ir.property"].search(
            [
                ("name", "=", "property_account_income_categ_id"),
                ("company_id", "=", self.env.company.id),
                ("res_id", "=", False),
            ],
            limit=1,
        )

        if income_property:
            # Update the existing property
            income_property.write(
                {
                    "value_reference": f"account.account, {self.account_income.id}",
                }
            )
        else:
            # Create a new property
            self.env["ir.property"].create(
                {
                    "name": "property_account_income_categ_id",
                    "company_id": self.env.company.id,
                    "type": "many2one",
                    "fields_id": self.env["ir.model.fields"]
                    .search(
                        [
                            ("model", "=", "product.category"),
                            ("name", "=", "property_account_income_categ_id"),
                        ],
                        limit=1,
                    )
                    .id,
                    "value_reference": f"account.account, {self.account_income.id}",
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

        # Get Bitcoin payment acquirer
        self.bitcoin_acquirer = self.env["payment.acquirer"].search(
            [("provider", "=", "bitcoin")], limit=1
        )

        if not self.bitcoin_acquirer:
            # Create Bitcoin payment acquirer if not found
            # First, get a journal for the Bitcoin payment acquirer
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

            # Make sure the journal has at least one payment method
            inbound_payment_method = self.env.ref(
                "account.account_payment_method_manual_in"
            )
            if inbound_payment_method.id not in journal.inbound_payment_method_ids.ids:
                journal.write(
                    {"inbound_payment_method_ids": [(4, inbound_payment_method.id)]}
                )

            self.bitcoin_acquirer = self.env["payment.acquirer"].create(
                {
                    "name": "Bitcoin",
                    "provider": "bitcoin",
                    "company_id": self.env.company.id,
                    "state": "test",
                    "bitcoin_order_older_than": 6,
                    "deadline": 60.0,
                    "journal_id": journal.id,
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
            "transaction": "6eb38d0fdf73c7c6ea30d5bc0e5378d9d1c81c1b5a6c4f0a8f595f7c7ad3c2a0",
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
            # Run the Bitcoin payment reconciliation cron job
            self.env["bitcoin.address"].cron_bitcoin_payment_reconciliation()

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
            "received": 0.5,  # 0.5 BTC (less than the 1.234 BTC required)
            "min_conf": 3,
            "transaction": "6eb38d0fdf73c7c6ea30d5bc0e5378d9d1c81c1b5a6c4f0a8f595f7c7ad3c2a0",
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
