import codecs
import logging
from datetime import datetime
from datetime import timedelta as td
from hashlib import sha256


DIGITS58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

import requests

_LOGGER = logging.getLogger(__name__)

from .common import BitcoinCommon
_logger = logging.getLogger(__name__)

def bech32_polymod(values):
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def bech32_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def bech32_verify_checksum(self, hrp, data):
    """Verify a checksum given HRP and converted data characters."""
    return self.bech32_polymod(self.bech32_hrp_expand(hrp) + data) == 1


def bech32_decode(self, bech):
    """Validate a Bech32 string, and determine HRP and data."""
    if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
            (bech.lower() != bech and bech.upper() != bech)):
        return (None, None)
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return (None, None)
    if not all(x in CHARSET for x in bech[pos + 1:]):
        return (None, None)
    hrp = bech[:pos]
    data = [CHARSET.find(x) for x in bech[pos + 1:]]
    if not self.bech32_verify_checksum(hrp, data):
        return (None, None)
    return (hrp, data[:-6])


def convertbits(self, data, frombits, tobits, pad=True):
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


def validate_bitcoin_address(self, addr):
    """Decode a segwit address."""
    hrpgot, data = self.bech32_decode(addr)
    if hrpgot not in ["bc", "tb"]:
        return False

    decoded = self.convertbits(data[1:], 5, 8, False)
    if decoded is None or len(decoded) < 2 or len(decoded) > 40:
        return False
    if data[0] > 16:
        return False
    if data[0] == 0 and len(decoded) != 20 and len(decoded) != 32:
        return False
    return True  # (data[0], decoded)


def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + DIGITS58.index(char)
    return codecs.decode(("%%0%dx" % (length << 1) % n), "hex_codec")[-length:]


def validate_bitcoin_address_old_format(self, address):
    bcbytes = self.decode_base58(address, 25)
    return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]


def check_received(addr):
    addr_info_url = "https://blockchain.info/rawaddr/{addr}"
    tx_info_url = "https://blockchain.info/rawtx/{tx}"
    latest_block_url = "https://blockchain.info/latestblock"

    needed_confirms = 3

    current_height = requests.get(latest_block_url).json()["height"]

    addr_info = requests.get(addr_info_url.format(addr=addr))

    txs = addr_info.json()["txs"]
    # no transactions -> nothing received
    if not txs:
        return {"received": 0, "min_conf": 0, "when": None}

    received = 0
    min_conf = None
    for tx in txs:
        tx_info = requests.get(tx_info_url.format(tx=tx["hash"]))

        b_height = tx_info.json()["block_height"]
        conf = current_height - b_height - 1 if b_height else 0
        if conf < needed_confirms:
            _LOGGER.info("\n\n ******* if Conf < needed_confirms *********************")
            return {"received": 0, "min_conf": 0, "when": None}
        min_conf = min(conf, min_conf) if min_conf is not None else conf

    out = {"received": addr_info.json()["total_received"] / 1e8, "min_conf": min_conf}
    out["when"] = datetime.now() - td(minutes=10) * (min_conf - needed_confirms)
    return out


class TestBitcoinNoPayment(BitcoinCommon):
    def setUp(self):
        super(TestBitcoinNoPayment, self).setUp()
        self.website = self.env.ref("website.default_website")

    def _create_sale_order(self, partner_id=None):
        return self.env["sale.order"].create(
            {
                "partner_id": partner_id,
                "website_id": self.website.id,
                "amount_total": 11305,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env["product.product"]
                            .create({"name": "Product Test", "list_price": 9500})
                            .id,
                            "name": "Product Test",
                        },
                    )
                ],
            }
        )

    def test_bitcoin_no_payment(self):
        partner_id = self.env.user.partner_id
        so = self._create_sale_order(partner_id.id)

        tx = self.env["payment.transaction"].create({
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "acquirer_id": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "sale_order_ids": [(6, 0, [so.id])],
            "bitcoin_address_link": "https://www.blockchain.com/btc/address/3FNJPXykZ38UkFBTGLncMQaHxaS7xjm83X",
            "callback_res_id": so.id,
            "tx_url": "/payment/bitcoin/feedback",
            "amount": so.amount_total
        })

        values = {
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "currency": self.currency_euro.name,
            "acquirer": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "website_id": self.website,
            "callback_res_id": so.id,
            "return_url": "/shop/payment/validate",
            "amount": so.amount_total,
            "tx_url": "/payment/bitcoin/feedback",
        }
        tx.form_feedback(values, "bitcoin")
        addr = check_received("3FNJPXykZ38UkFBTGLncMQaHxaS7xjm83X")
        address_id = self.env["bitcoin.address"].search([("name", "=", "3FNJPXykZ38UkFBTGLncMQaHxaS7xjm83X")])
        if address_id:
            address_id.cron_bitcoin_payment_reconciliation()
        invoice_objs = addr.order_id.mapped("invoice_ids")
        self.assertEqual(invoice_objs, "draft")
        self.assertEqual(tx.state, "pending")

    def test_bitcoin_payment(self):
        partner_id = self.env.user.partner_id
        so = self._create_sale_order(partner_id.id)
        tx = self.env["payment.transaction"].create({
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "acquirer_id": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "sale_order_ids": [(6, 0, [so.id])],
            "bitcoin_address_link": "https://www.blockchain.com/btc/address/3NYbDtMSN84qz71WLaZu1unXrkjew2KrEq",
            "callback_res_id": so.id,
            "return_url": "/shop/payment/validate",
            "amount": so.amount_total,
        })

        values = {
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "currency": self.currency_euro.name,
            "acquirer": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "website_id": self.website,
            "callback_res_id": so.id,
            "return_url": "/shop/payment/validate",
            "amount": so.amount_total,
            "tx_url": "/payment/bitcoin/feedback",
        }
        tx.form_feedback(values,"bitcoin")
        addr = check_received("3NYbDtMSN84qz71WLaZu1unXrkjew2KrEq")
        address_id = self.env["bitcoin.address"].search([("name","=","3NYbDtMSN84qz71WLaZu1unXrkjew2KrEq")])
        if address_id:
            address_id.cron_bitcoin_payment_reconciliation()
        tx._set_transaction_done()
        invoice_objs = addr.order_id.mapped("invoice_ids")
        self.assertEqual(invoice_objs, "paid")
        self.assertEqual(tx.state, "done")

    def test_insuficient_payment(self):
        partner_id = self.env.user.partner_id
        so = self._create_sale_order(partner_id.id)
        tx = self.env["payment.transaction"].create({
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "acquirer_id": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "sale_order_ids": [(6, 0, [so.id])],
            "bitcoin_address_link": "https://www.blockchain.com/btc/address/3NYbDtMSN84qz71WLaZu1unXrkjew2KrEq",
            "callback_res_id": so.id,
            "return_url": "/shop/payment/validate",
            "amount": 300,
        })

        values = {
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "currency": self.currency_euro.name,
            "acquirer": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "website_id": self.website,
            "callback_res_id": so.id,
            "return_url": "/shop/payment/validate",
            "amount": 300,
            "tx_url": "/payment/bitcoin/feedback",
        }
        tx.form_feedback(values,"bitcoin")
        check_received("3NYbDtMSN84qz71WLaZu1unXrkjew2KrEq")
        address_id = self.env["bitcoin.address"].search([("name", "=", "3NYbDtMSN84qz71WLaZu1unXrkjew2KrEq")])
        if address_id:
            address_id.cron_bitcoin_payment_reconciliation()
        self.assertNotEqual(tx.amount, so.amount_total)