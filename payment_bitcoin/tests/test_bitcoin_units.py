from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.payment_bitcoin.controllers.bitcoin import get_bitcoin_render_values
from odoo.addons.payment_bitcoin.models.bitcoin import (
    bech32_decode,
    check_received,
    convertbits,
    decode_base58,
    validate_bitcoin_address,
    validate_bitcoin_address_old_format,
)

REQUESTS_GET = "odoo.addons.payment_bitcoin.models.bitcoin.requests.get"

# well known valid addresses (genesis block, BIP173 test vector)
LEGACY_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
LEGACY_ADDRESS_BAD_CHECKSUM = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNb"
P2SH_ADDRESS = "3N1MrpKTxGfb4CmTzgEYXfcDM9o2s3P5Q1"
BECH32_ADDRESS = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
TX_HASH = "6eb38d0fdf73c7c6ea30d5bc0e5378d9d1c81c1b5a6c4f0a8f595f7c7ad3c2a0"


def _response(json_data=None, status_code=200, content=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.content = content
    response.text = text
    return response


def _blockchain_mock(
    height=800000,
    block_height=799990,
    total_received=123400000,
    txs=None,
    tx_status=200,
):
    """Return a ``requests.get`` replacement emulating blockchain.info."""
    if txs is None:
        txs = [{"hash": TX_HASH}]

    def fake_get(url, *args, **kwargs):
        if "latestblock" in url:
            return _response({"height": height})
        if "rawaddr" in url:
            return _response({"total_received": total_received, "txs": txs})
        if "rawtx" in url:
            return _response({"block_height": block_height}, status_code=tx_status)
        return _response(status_code=404)

    return fake_get


@tagged("post_install", "-at_install")
class TestBitcoinAddressValidation(TransactionCase):
    def test_validate_segwit_address(self):
        self.assertTrue(validate_bitcoin_address(BECH32_ADDRESS))
        self.assertTrue(validate_bitcoin_address(BECH32_ADDRESS.upper()))

    def test_validate_segwit_address_invalid(self):
        # legacy address is not bech32
        self.assertFalse(validate_bitcoin_address(LEGACY_ADDRESS))
        # mixed case is rejected
        self.assertFalse(validate_bitcoin_address("Bc" + BECH32_ADDRESS[2:]))
        # broken checksum
        self.assertFalse(validate_bitcoin_address(BECH32_ADDRESS[:-1] + "5"))
        # wrong human readable part
        self.assertFalse(validate_bitcoin_address("tc" + BECH32_ADDRESS[2:]))

    def test_bech32_decode_invalid(self):
        self.assertEqual(bech32_decode("short"), (None, None))
        self.assertEqual(bech32_decode("bc1 " + "q" * 10), (None, None))
        self.assertEqual(bech32_decode("1" + "q" * 10), (None, None))
        self.assertEqual(bech32_decode("a" * 91), (None, None))
        self.assertEqual(bech32_decode("bc1bbbbbbbb"), (None, None))
        hrp, data = bech32_decode(BECH32_ADDRESS)
        self.assertEqual(hrp, "bc")
        self.assertEqual(data[0], 0)

    def test_convertbits(self):
        self.assertEqual(convertbits([255], 8, 5), [31, 28])
        self.assertIsNone(convertbits([256], 8, 5))
        self.assertIsNone(convertbits([-1], 8, 5))
        # non-zero padding is refused without pad
        self.assertIsNone(convertbits([31, 31], 5, 8, False))

    def test_validate_old_format(self):
        self.assertTrue(validate_bitcoin_address_old_format(LEGACY_ADDRESS))
        self.assertTrue(validate_bitcoin_address_old_format(P2SH_ADDRESS))
        self.assertFalse(
            validate_bitcoin_address_old_format(LEGACY_ADDRESS_BAD_CHECKSUM)
        )

    def test_validate_old_format_invalid_character(self):
        # "0", "O", "I" and "l" are not part of the base58 alphabet
        self.assertFalse(validate_bitcoin_address_old_format("1" + "0" * 33))
        self.assertFalse(validate_bitcoin_address_old_format("Il" + LEGACY_ADDRESS))

    def test_address_constraint_invalid_character(self):
        with self.assertRaises(ValidationError):
            self.env["bitcoin.address"].create({"name": "1" + "O" * 33})

    def test_address_constraint_multiple_records(self):
        addresses = self.env["bitcoin.address"].create(
            [{"name": LEGACY_ADDRESS}, {"name": P2SH_ADDRESS}]
        )
        with self.assertRaises(ValidationError):
            addresses[1].name = LEGACY_ADDRESS_BAD_CHECKSUM
            addresses.flush_recordset()

    def test_decode_base58(self):
        decoded = decode_base58(LEGACY_ADDRESS, 25)
        self.assertEqual(len(decoded), 25)
        self.assertEqual(decoded[0], 0)

    def test_address_constraint(self):
        Address = self.env["bitcoin.address"]
        for name in (LEGACY_ADDRESS, P2SH_ADDRESS, BECH32_ADDRESS):
            self.assertTrue(Address.create({"name": name}).exists())
        with self.assertRaises(ValidationError):
            Address.create({"name": LEGACY_ADDRESS_BAD_CHECKSUM})

    def test_address_unique(self):
        Address = self.env["bitcoin.address"]
        Address.create({"name": LEGACY_ADDRESS})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            with self.env.cr.savepoint():
                Address.create({"name": LEGACY_ADDRESS})

    def test_number_helpers(self):
        Address = self.env["bitcoin.address"]
        self.assertEqual(Address.convert_num_to_standard(5.836e-05), "0.00005836")
        self.assertEqual(Address.cnvrt_list_to_string(["a", 1, "b"]), "a, 1, b")
        self.assertEqual(Address.cnvrt_list_to_string([]), "")


@tagged("post_install", "-at_install")
class TestCheckReceived(TransactionCase):
    def test_confirmed_payment(self):
        with patch(REQUESTS_GET, side_effect=_blockchain_mock()):
            result = check_received(P2SH_ADDRESS)
        self.assertAlmostEqual(result["received"], 1.234)
        self.assertEqual(result["min_conf"], 9)
        self.assertEqual(result["transaction"], TX_HASH)
        self.assertIsInstance(result["when"], datetime)

    def test_latest_block_http_error(self):
        with patch(REQUESTS_GET, return_value=_response(status_code=500)):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)
        self.assertIsNone(result["transaction"])

    def test_latest_block_exception(self):
        with patch(REQUESTS_GET, side_effect=requests.exceptions.ConnectionError()):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)

    def test_latest_block_invalid_json(self):
        response = _response()
        response.json.side_effect = requests.exceptions.JSONDecodeError("x", "y", 0)
        with patch(REQUESTS_GET, return_value=response):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)

    def test_address_http_error(self):
        def fake_get(url, *args, **kwargs):
            if "latestblock" in url:
                return _response({"height": 800000})
            return _response(status_code=429)

        with patch(REQUESTS_GET, side_effect=fake_get):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)

    def test_address_exception(self):
        def fake_get(url, *args, **kwargs):
            if "latestblock" in url:
                return _response({"height": 800000})
            raise requests.exceptions.Timeout()

        with patch(REQUESTS_GET, side_effect=fake_get):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)

    def test_address_invalid_json(self):
        address_response = _response()
        address_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "x", "y", 0
        )

        def fake_get(url, *args, **kwargs):
            if "latestblock" in url:
                return _response({"height": 800000})
            return address_response

        with patch(REQUESTS_GET, side_effect=fake_get):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)

    def test_no_transactions(self):
        with patch(REQUESTS_GET, side_effect=_blockchain_mock(txs=[])):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)
        self.assertIsNone(result["transaction"])

    def test_not_enough_confirmations(self):
        # 800000 - 799998 - 1 = 1 confirmation
        with patch(REQUESTS_GET, side_effect=_blockchain_mock(block_height=799998)):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)

    def test_all_transaction_lookups_fail(self):
        def fake_get(url, *args, **kwargs):
            if "latestblock" in url:
                return _response({"height": 800000})
            if "rawaddr" in url:
                return _response({"total_received": 1, "txs": [{"hash": TX_HASH}]})
            return _response(status_code=500)

        with patch(REQUESTS_GET, side_effect=fake_get):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)
        self.assertIsNone(result["transaction"])

    def test_unconfirmed_transaction(self):
        with patch(REQUESTS_GET, side_effect=_blockchain_mock(block_height=None)):
            result = check_received(P2SH_ADDRESS)
        self.assertEqual(result["received"], 0)


@tagged("post_install", "-at_install")
class TestBitcoinRate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rate = cls.env["bitcoin.rate"].search([])
        assert len(cls.rate) == 1, "expected exactly one default bitcoin.rate"
        cls.rate.write({"markup": 0.0, "unit": "BTC", "digits": 8})
        cls.partner = cls.env["res.partner"].create({"name": "Rate Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Rate Product", "list_price": 100.0}
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                ],
            }
        )
        # make sure only our address is available
        cls.env["bitcoin.address"].search([]).unlink()
        cls.address = cls.env["bitcoin.address"].create({"name": P2SH_ADDRESS})

    def _rate_response(self, value=b"0.002"):
        return _response(content=value)

    def test_get_rate_new_lookup(self):
        with patch(REQUESTS_GET, return_value=self._rate_response()) as mocked:
            result = self.env["bitcoin.rate"].get_rate(order_id=self.order.id)
        self.assertEqual(result, (P2SH_ADDRESS, 0.002, "BTC"))
        url = mocked.call_args[0][0]
        self.assertIn(self.order.currency_id.name, url)
        self.assertIn(str(self.order.amount_total), url)
        self.assertEqual(self.address.order_id, self.order)
        line = self.env["bitcoin.rate.line"].search([("order_id", "=", self.order.id)])
        self.assertEqual(len(line), 1)
        self.assertAlmostEqual(line.rate, 0.002)
        self.assertEqual(line.name, self.order.name)

    def test_get_rate_cached(self):
        with patch(REQUESTS_GET, return_value=self._rate_response()):
            self.env["bitcoin.rate"].get_rate(order_id=self.order.id)
        with patch(REQUESTS_GET, side_effect=AssertionError("no lookup")):
            result = self.env["bitcoin.rate"].get_rate(order_ref=self.order.name)
        self.assertEqual(result, (P2SH_ADDRESS, 0.002, "BTC"))

    def test_get_rate_markup_and_mbtc(self):
        self.rate.write({"markup": 10.0, "unit": "mBTC", "digits": 4})
        with patch(REQUESTS_GET, return_value=self._rate_response()):
            address, amount, unit = self.env["bitcoin.rate"].get_rate(
                order_id=self.order.id
            )
        self.assertEqual(address, P2SH_ADDRESS)
        self.assertEqual(unit, "mBTC")
        self.assertAlmostEqual(amount, 2.2)

    def test_get_rate_http_error(self):
        with patch(REQUESTS_GET, return_value=_response(status_code=500)):
            self.assertFalse(self.env["bitcoin.rate"].get_rate(order_id=self.order.id))

    def test_get_rate_unknown_order_ref(self):
        self.assertFalse(self.env["bitcoin.rate"].get_rate(order_ref="DOES-NOT-EXIST"))

    def test_get_rate_unknown_invoice_ref(self):
        self.assertFalse(
            self.env["bitcoin.rate"].get_rate(invoice_ref="DOES-NOT-EXIST")
        )

    def test_get_rate_without_reference(self):
        with self.assertRaises(UserError):
            self.env["bitcoin.rate"].get_rate()

    def test_get_rate_requires_single_config(self):
        self.env["bitcoin.rate"].create({"markup": 1.0})
        self.assertFalse(self.env["bitcoin.rate"].get_rate(order_id=self.order.id))

    def test_get_rate_no_address(self):
        self.address.unlink()
        self.assertFalse(self.env["bitcoin.rate"].get_rate(order_id=self.order.id))

    def test_rate_test_button(self):
        with patch(REQUESTS_GET, return_value=self._rate_response()):
            self.assertTrue(self.rate.test_rate())


@tagged("post_install", "-at_install")
class TestBitcoinTransaction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env.ref("payment_bitcoin.payment_acquirer_bitcoin")
        cls.provider.deadline = 60.0
        cls.method = cls.env.ref("payment_bitcoin.payment_method_bitcoin")
        cls.partner = cls.env["res.partner"].create({"name": "Tx Partner"})
        cls.currency = cls.env.company.currency_id

    def _tx(self, **vals):
        values = {
            "provider_id": self.provider.id,
            "payment_method_id": self.method.id,
            "amount": 100.0,
            "currency_id": self.currency.id,
            "partner_id": self.partner.id,
            "reference": "BTC-TEST-{}".format(
                self.env["payment.transaction"].search_count([])
            ),
        }
        values.update(vals)
        return self.env["payment.transaction"].create(values)

    def test_create_fetches_bitcoin_rate(self):
        self.env["bitcoin.address"].search([]).unlink()
        self.env["bitcoin.address"].create({"name": P2SH_ADDRESS})
        self.env["bitcoin.rate"].search([]).write(
            {"markup": 0.0, "unit": "BTC", "digits": 8}
        )
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env["product.product"]
                            .create({"name": "P", "list_price": 10.0})
                            .id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )
        with patch(REQUESTS_GET, return_value=_response(content=b"0.002")):
            tx = self._tx(sale_order_ids=[(6, 0, order.ids)])
        self.assertEqual(tx.bitcoin_address, P2SH_ADDRESS)
        self.assertAlmostEqual(tx.bitcoin_amount, 0.002)
        self.assertEqual(tx.bitcoin_unit, "BTC")

    def test_compute_link_address(self):
        tx = self._tx(bitcoin_address=P2SH_ADDRESS)
        self.assertIn(P2SH_ADDRESS, str(tx.bitcoin_address_link))
        self.assertIn("blockchain.info/address", str(tx.bitcoin_address_link))

    def test_compute_time_remaining(self):
        tx = self._tx()
        tx.last_state_change = fields.Datetime.now()
        tx.invalidate_recordset(["duration"])
        self.assertTrue(0 < tx.duration <= 3600)

    def test_compute_time_remaining_expired(self):
        self.provider.deadline = 0.0
        tx = self._tx()
        tx.last_state_change = fields.Datetime.now()
        tx.invalidate_recordset(["duration"])
        self.assertEqual(tx.duration, 0)

    def test_format_bitcoin_amount(self):
        tx = self._tx()
        self.assertEqual(tx.format_bitcoin_amount(1.5), "1.50000000")
        self.assertEqual(tx.format_bitcoin_amount(1.5, 2), "1.50")

    def test_get_tx_from_notification_data(self):
        tx = self._tx(reference="BTC-NOTIF")
        found = self.env["payment.transaction"]._get_tx_from_notification_data(
            "bitcoin", {"reference": "BTC-NOTIF"}
        )
        self.assertEqual(found, tx)
        with self.assertRaises(ValidationError):
            self.env["payment.transaction"]._get_tx_from_notification_data(
                "bitcoin", {"reference": "BTC-UNKNOWN"}
            )

    def test_bitcoin_form_get_tx_from_data(self):
        tx = self._tx(reference="BTC-FORM")
        Tx = self.env["payment.transaction"]
        found = Tx._bitcoin_form_get_tx_from_data({"reference": "BTC-FORM"})
        self.assertEqual(found, tx)
        with self.assertRaises(ValidationError):
            Tx._bitcoin_form_get_tx_from_data({"reference": "BTC-UNKNOWN"})

    def test_process_notification_data(self):
        for status, expected in (
            ("pending", "pending"),
            ("done", "done"),
            ("cancel", "cancel"),
            ("bogus", "error"),
        ):
            with self.subTest(status=status):
                tx = self._tx(reference=f"BTC-PROC-{status}")
                tx._process_notification_data({"state": status})
                self.assertEqual(tx.state, expected)

    def test_specific_rendering_values(self):
        tx = self._tx()
        values = tx._get_specific_rendering_values({})
        self.assertEqual(values["reference"], tx.reference)
        self.assertEqual(values["return_url"], "/payment/bitcoin/feedback")
        self.assertEqual(values["currency_code"], self.currency.name)

    def test_render_values(self):
        lang = self.env["res.lang"]._lang_get("en_US")
        tx = self._tx(
            bitcoin_address=P2SH_ADDRESS, bitcoin_amount=0.5, bitcoin_unit="BTC"
        )
        tx.last_state_change = fields.Datetime.now()
        info, uri = get_bitcoin_render_values(tx, lang)
        self.assertEqual(
            uri, f"bitcoin:{P2SH_ADDRESS}$$amount=0.5*$message=Bitcoin Payment"
        )
        self.assertIn(P2SH_ADDRESS, info)
        self.assertIn("500.0 mBTC", info)

        tx.bitcoin_unit = "mBTC"
        tx.bitcoin_amount = 500.0
        order = SimpleNamespace(name="S001")
        info, uri = get_bitcoin_render_values(tx, lang, order=order)
        self.assertIn("amount=0.5*", uri)

    def test_account_payment_method_information(self):
        info = self.env["account.payment.method"]._get_payment_method_information()
        self.assertIn("bitcoin", info)
        self.assertEqual(info["bitcoin"]["mode"], "unique")


@tagged("post_install", "-at_install")
class TestBitcoinSettingsAndNotifications(TransactionCase):
    def _accountant_group(self):
        return self.env.ref("account.group_account_manager")

    def test_settings_roundtrip(self):
        settings = self.env["res.config.settings"].create({"min_unused_bitcoin": 7})
        settings.set_values()
        self.assertEqual(
            self.env["ir.config_parameter"].get_param(
                "payment_bitcoin.min_unused_bitcoin"
            ),
            "7",
        )
        self.assertEqual(
            self.env["res.config.settings"].get_values()["min_unused_bitcoin"], 7
        )

    def test_low_address_notification(self):
        self.env["bitcoin.address"].search([]).unlink()
        self.env["ir.config_parameter"].set_param(
            "payment_bitcoin.min_unused_bitcoin", "3"
        )
        user = self.env["res.users"].create(
            {
                "name": "Accountant",
                "login": "btc_accountant",
                "email": "btc_accountant@example.com",
                "groups_id": [(6, 0, self._accountant_group().ids)],
            }
        )
        self.env["bitcoin.address"].send_bitcoin_address_goes_low_notification()
        activity = self.env["mail.activity"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", user.partner_id.id),
                ("user_id", "=", user.id),
            ]
        )
        self.assertTrue(activity)

    def test_low_address_notification_not_needed(self):
        self.env["ir.config_parameter"].set_param(
            "payment_bitcoin.min_unused_bitcoin", "-1"
        )
        user = self.env["res.users"].create(
            {
                "name": "Accountant 2",
                "login": "btc_accountant2",
                "email": "btc_accountant2@example.com",
                "groups_id": [(6, 0, self._accountant_group().ids)],
            }
        )
        self.env["bitcoin.address"].send_bitcoin_address_goes_low_notification()
        self.assertFalse(
            self.env["mail.activity"].search(
                [
                    ("res_model", "=", "res.partner"),
                    ("res_id", "=", user.partner_id.id),
                    ("user_id", "=", user.id),
                ]
            )
        )
