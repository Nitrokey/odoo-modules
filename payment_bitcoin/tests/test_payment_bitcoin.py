import codecs
from datetime import datetime
from datetime import timedelta as td
from hashlib import sha256
from ..models.bitcoin import validate_bitcoin_address, check_received

DIGITS58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

import requests
from .common import BitcoinCommon

_no_payment_addr = "3FNJPXykZ38UkFBTGLncMQaHxaS7xjm83X"
_payment_addr = "3NYbDtMSN84qz71WLaZu1unXrkjew2KrEq"

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

def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + DIGITS58.index(char)
    return codecs.decode(("%%0%dx" % (length << 1) % n), "hex_codec")[-length:]


def validate_bitcoin_address_old_format(self, address):
    bcbytes = self.decode_base58(address, 25)
    return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]


class TestBitcoinNoPayment(BitcoinCommon):
    def setUp(self):
        super(TestBitcoinNoPayment, self).setUp()
        self.website = self.env.ref("website.default_website")

        # Initialize the bitcoin acceptance duration 10 years in hours
        self.env['ir.config_parameter'].sudo().create({'key': 'payment_bitcoin.bit_coin_order_older_than','value': 87600})
        self.env.ref("payment_bitcoin.mail_template_data_bit_coin_order_notification").write({"auto_delete": False})

    def _create_sale_order(self, amount, partner_id=None):
        return self.env["sale.order"].create(
            {
                "partner_id": partner_id,
                "website_id": self.website.id,
                "amount_total": amount,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env["product.product"]
                            .create({"name": "Product Test", "list_price": amount})
                            .id,
                            "name": "Product Test",
                        },
                    )
                ],
            }
        )

    def remove_acceptance_hours_params(self):
        # Unlink the acceptance duration of the bitcoin
        return self.env['ir.config_parameter'].sudo().search([('key','=','payment_bitcoin.bit_coin_order_older_than')]).unlink()

    def create_bitcoin_address_data(self, addr, order):
        # Check that bitcoin address's record is available if not then create
        bitcoin_addr = self.env["bitcoin.address"].sudo().search([('name','=',addr)])
        if not bitcoin_addr:
            bitcoin_addr = self.env["bitcoin.address"].sudo().create({
                "name" : addr,
                "order_id": order.id,
                })
        else:
            bitcoin_addr.write({"order_id": order.id})
        return bitcoin_addr

    def test_bitcoin_no_payment(self):
        '''This method tests when no payment is received from bitcoin'''
        partner_id = self.env.user.partner_id
        so = self._create_sale_order(500, partner_id.id)
        self.btc_adr = self.create_bitcoin_address_data(_no_payment_addr, so)
        tx = self.env["payment.transaction"].create({
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "acquirer_id": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "sale_order_ids": [(6, 0, [so.id])],
            "bitcoin_address_link": f"https://www.blockchain.com/btc/address{_no_payment_addr}",
            "callback_res_id": so.id,
            "tx_url": "/payment/bitcoin/feedback",
            "amount": so.amount_total
        })
        address_id = self.env["bitcoin.address"].search([("name", "=", _no_payment_addr)])

        # Executing cron for bitcoin payment
        if address_id:
            address_id.cron_bitcoin_payment_reconciliation()

        # Checks that no invoice is created for no payment
        invoice_objs = so.mapped("invoice_ids")
        self.assertFalse(invoice_objs)

    def test_bitcoin_payment(self):
        '''This method tests payment is received from bitcoin'''
        partner_id = self.env.user.partner_id
        so = self._create_sale_order(500, partner_id.id)
        self.btc_adr = self.create_bitcoin_address_data(_payment_addr, so)
        tx = self.env["payment.transaction"].create({
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "acquirer_id": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "sale_order_ids": [(6, 0, [so.id])],
            "bitcoin_address_link": f"https://www.blockchain.com/btc/address{_payment_addr}",
            "callback_res_id": so.id,
            "return_url": "/shop/payment/validate",
            "amount": so.amount_total,
        })
        address_id = self.env["bitcoin.address"].search([("name","=",_payment_addr)])

        # Executing cron for bitcoin payment
        if address_id:
            address_id.cron_bitcoin_payment_reconciliation()

        # Checks that invoice is paid
        invoice_objs = so.mapped("invoice_ids")
        self.assertEqual(invoice_objs.state, "paid")

    def test_insufficient_payment(self):
        '''This method checks if insufficient payment received from bitcoin'''
        partner_id = self.env.user.partner_id
        so = self._create_sale_order(800, partner_id.id)
        self.btc_adr = self.create_bitcoin_address_data(_payment_addr, so)
        tx = self.env["payment.transaction"].create({
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "acquirer_id": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "sale_order_ids": [(6, 0, [so.id])],
            "bitcoin_address_link": f"https://www.blockchain.com/btc/address{_payment_addr}",
            "callback_res_id": so.id,
            "return_url": "/shop/payment/validate",
            "amount": so.amount_total,
        })
        address_id = self.env["bitcoin.address"].search([("name", "=", _payment_addr)])

        # Executing cron for bitcoin payment
        if address_id:
            address_id.cron_bitcoin_payment_reconciliation()

        # Checks that insufficient payment mail
        mail = self.env['mail.mail'].search([('res_id','=',so.id),('model','=',so._name)])
        self.assertTrue(mail)

        # Checks that no invoice is created due to insufficient payment
        invoice_objs = so.mapped("invoice_ids")
        self.assertFalse(invoice_objs)

    def tearDown(self):
        super(TestBitcoinNoPayment, self).tearDown()

        # Unlink the initialized bitcoin acceptance duration
        self.remove_acceptance_hours_params()

        # Unlink the bitcoin address record
        self.btc_adr.unlink()

        self.env.ref("payment_bitcoin.mail_template_data_bit_coin_order_notification").write({"auto_delete": True})