import codecs
import logging
from datetime import date, datetime, timedelta as td
from hashlib import sha256

import requests
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

DIGITS58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def bech32_polymod(values):
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def bech32_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def bech32_verify_checksum(hrp, data):
    """Verify a checksum given HRP and converted data characters."""
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == 1


def bech32_decode(bech):
    """Validate a Bech32 string, and determine HRP and data."""
    if (any(ord(x) < 33 or ord(x) > 126 for x in bech)) or (
        bech.lower() != bech and bech.upper() != bech
    ):
        return (None, None)
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return (None, None)
    if not all(x in CHARSET for x in bech[pos + 1 :]):
        return (None, None)
    hrp = bech[:pos]
    data = [CHARSET.find(x) for x in bech[pos + 1 :]]
    if not bech32_verify_checksum(hrp, data):
        return (None, None)
    return (hrp, data[:-6])


def convertbits(data, frombits, tobits, pad=True):
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


def validate_bitcoin_address(addr):
    """Decode a segwit address."""
    hrpgot, data = bech32_decode(addr)
    if hrpgot not in ["bc", "tb"]:
        return False

    decoded = convertbits(data[1:], 5, 8, False)
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


def validate_bitcoin_address_old_format(address):
    bcbytes = decode_base58(address, 25)
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
        return {"received": 0, "min_conf": 0, "when": None, "transaction": None}

    min_conf = None
    for tx in txs:
        tx_info = requests.get(tx_info_url.format(tx=tx["hash"]))

        b_height = tx_info.json()["block_height"]
        # confirmations = current_block_height - transaction_block_height - 1
        conf = current_height - b_height - 1 if b_height else 0
        if conf < needed_confirms:
            return {"received": 0, "min_conf": 0, "when": None, "transaction": None}
        min_conf = min(conf, min_conf) if min_conf is not None else conf
        last_trans = tx

    # here all transactions are >= 10 times confirmed,
    # we consider total_received" as "received" btc
    out = {
        "received": addr_info.json()["total_received"] / 1e8,
        "min_conf": min_conf,
        "transaction": last_trans.get("hash"),
    }

    # let's define the "transaction-finalized" when the last transaction
    # reached needed_confirms confirmations
    # so the time when this happened is ~ 10minutes * )confirmations - needed_confirms)
    out["when"] = datetime.now() - td(minutes=10) * (min_conf - needed_confirms)
    return out


class BitcoinAddress(models.Model):
    # Store Bitcoin addresses,  address will be checked for Unique and Valid
    # Bitcoin address
    # once used, it'll have order_id assigned, so it won't use again.
    _name = "bitcoin.address"
    _description = "Bitcoin Address"

    name = fields.Char("Address", required=True)
    create_date = fields.Datetime("Created")
    create_uid = fields.Many2one("res.users", "Created by")

    order_id = fields.Many2one("sale.order", "Order Assigned", ondelete="set null")
    invoice_id = fields.Many2one(
        "account.move", "Invoice Assigned", ondelete="set null"
    )
    is_btc_used = fields.Boolean("Is Bitcoin used?")

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Bitcoin Address must be unique"),
    ]

    def convert_num_to_standard(self, scientific_num):
        """This function converts scientific number to standard number
        (e.g. 5.836e-05 -> 0.00005836)"""
        return ("%.17f" % scientific_num).rstrip("0")

    def cnvrt_list_to_string(self, ldata):
        return ", ".join([str(data) for data in ldata])

    @api.model
    def cron_bitcoin_payment_reconciliation(self):  # noqa: C901
        acquirer_obj = self.env["payment.acquirer"].search(
            [("provider", "=", "bitcoin")]
        )
        payment_journal_obj = acquirer_obj.journal_id
        check_hours = acquirer_obj.bitcoin_order_older_than
        check_date = datetime.now() - td(hours=int(check_hours))
        for bit_add_obj in self.search(
            [
                "|",
                ("order_id", "!=", False),
                ("invoice_id", "!=", False),
                ("is_btc_used", "=", False),
            ]
        ):
            if bit_add_obj.order_id.create_date < check_date:
                continue

            address_info = check_received(bit_add_obj.name)
            if not address_info:
                continue

            if bit_add_obj.order_id:
                domain = [
                    ("order_id", "=", bit_add_obj.order_id.id),
                    ("name", "=", bit_add_obj.order_id.name),
                ]
            elif bit_add_obj.invoice_id:
                domain = [
                    ("invoice_id", "=", bit_add_obj.invoice_id.id),
                    ("name", "=", bit_add_obj.invoice_id.name),
                ]
            else:
                continue

            recs_to_post = list(
                filter(None, (bit_add_obj.order_id, bit_add_obj.invoice_id))
            )

            valid_rate_exists = (
                self.env["bitcoin.rate.line"].sudo().search(domain, limit=1)
            )
            valid_rate = 0.0
            if valid_rate_exists:
                valid_rate = valid_rate_exists.rate

            amount_received = self.convert_num_to_standard(address_info["received"])
            if valid_rate and address_info["received"] >= valid_rate:
                open_invoice_objs = None
                if bit_add_obj.order_id and bit_add_obj.order_id.state == "cancel":
                    if bit_add_obj.order_id.state not in ("done", "sale"):
                        bit_add_obj.order_id.action_confirm()

                    if not bit_add_obj.order_id.invoice_ids:
                        bit_add_obj.order_id._create_invoices()

                    invoice_objs = bit_add_obj.order_id.mapped("invoice_ids").filtered(
                        lambda r: r.state == "draft"
                    )

                    if invoice_objs:
                        invoice_objs.action_post()

                    open_invoice_objs = bit_add_obj.order_id.mapped(
                        "invoice_ids"
                    ).filtered(lambda r: r.state == "posted")

                if bit_add_obj.invoice_id:
                    invoice_objs = bit_add_obj.invoice_id.filtered(
                        lambda r: r.state == "draft"
                    )

                    open_invoice_objs = bit_add_obj.invoice_id.filtered(
                        lambda r: r.state == "posted"
                    )

                if open_invoice_objs:
                    line_to_reconcile = self.env["account.move.line"]
                    payment_line = self.env["account.move.line"]

                    payment_methods = (
                        payment_journal_obj.available_payment_method_ids.ids
                    )
                    payment_vals = {
                        "partner_id": bit_add_obj.order_id.partner_id.id,
                        "payment_type": "inbound",
                        "partner_type": "customer",
                        "amount": bit_add_obj.order_id.amount_total,
                        "date": fields.Date.today(),
                        "journal_id": payment_journal_obj.id,
                        "payment_method_id": payment_methods
                        and payment_methods[0]
                        or False,
                    }
                    payment_obj = (
                        self.env["account.payment"].sudo().create(payment_vals)
                    )
                    payment_obj.action_post()
                    payment_move = payment_obj
                    payment_line = payment_move.line_ids.filtered(
                        lambda r: not r.reconciled
                        and r.account_id.internal_type in ("payable", "receivable")
                    )

                    for inv in open_invoice_objs:
                        line_to_reconcile += inv.line_ids.filtered(
                            lambda r: not r.reconciled
                            and r.account_id.internal_type in ("payable", "receivable")
                        )

                    (line_to_reconcile + payment_line).reconcile()
                    bit_add_obj.write({"is_btc_used": True})
                    if float(address_info["received"]) == float(valid_rate):
                        for rec in recs_to_post:
                            rec.message_post(
                                body=_(
                                    "Bitcoin transaction %(transaction)s for \
                                    %(address)s with %(amount)s BTC has been\
                                     confirmed. The corresponding payment is \
                                     posted: %(invoices)s"
                                )
                                % {
                                    "transaction": address_info.get("transaction"),
                                    "address": bit_add_obj.name,
                                    "amount": amount_received,
                                    "invoices": self.cnvrt_list_to_string(
                                        invoice_objs.mapped("name")
                                    ),
                                }
                            )
                    elif float(address_info["received"]) > float(valid_rate):
                        max_amount_received = float(address_info["received"]) - float(
                            valid_rate
                        )
                        log_max_amt = (
                            _(
                                "Bitcoin transaction %(transaction)s \
                                for %(address)s \
                                with %(amount)s BTC has \
                            been confirmed. This is  %(max_amount_received)s \
                            BTC too much. The \
                            corresponding payment is posted: %(invoices)s"
                            )
                            % {
                                "transaction": address_info.get("transaction"),
                                "address": bit_add_obj.name,
                                "amount": amount_received,
                                "max_amount_received": self.convert_num_to_standard(
                                    max_amount_received
                                ),
                                "invoices": self.cnvrt_list_to_string(
                                    invoice_objs.mapped("name")
                                ),
                            }
                        )
                        for rec in recs_to_post:
                            rec.message_post(body=log_max_amt)
            else:
                insufficiant_amount = float(valid_rate) - float(
                    address_info["received"]
                )
                if address_info.get("transaction") and float(amount_received) > 0.0:
                    for rec in recs_to_post:
                        rec.message_post(
                            body=_(
                                "Bitcoin transaction %(transaction)s for \
                                %(address)s with %(amount)s \
                                BTC has been confirmed. It is missing \
                                %(insufficiant_amount)s BTC."
                            )
                            % {
                                "transaction": address_info.get("transaction"),
                                "address": bit_add_obj.name,
                                "amount": amount_received,
                                "insufficiant_amount": self.convert_num_to_standard(
                                    insufficiant_amount
                                ),
                            }
                        )

                if acquirer_obj.bitcoin_send_email and bit_add_obj.order_id:
                    template_obj = self.env.ref(
                        "payment_bitcoin.mail_template_data_bit_coin_order_notification"
                    )
                    template_obj.send_mail(
                        bit_add_obj.order_id.id,
                        force_send=True,
                        raise_exception=True,
                    )

    @api.model
    def send_bitcoin_address_goes_low_notification(self):
        unused_address_count = self.search_count([("order_id", "=", False)])
        min_unused_bitcoin = safe_eval(
            self.env["ir.config_parameter"].get_param(
                "payment_bitcoin.min_unused_bitcoin",
                "3",
            )
        )
        if unused_address_count <= min_unused_bitcoin:
            groups = self.env["res.groups"].browse()

            group = self.sudo().env.ref("account.group_account_invoice", False)
            if group:
                groups += group
            group = self.sudo().env.ref("account.group_account_user", False)
            if group:
                groups += group

            for user in groups.mapped("users"):
                user.partner_id.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=_("Bitcoin addresses running low"),
                    user_id=user.id,
                    date_deadline=date.today(),
                )

        return

    @api.constrains("name")
    def _check_bitcoin_address(self):
        if not validate_bitcoin_address(self.name):
            if not validate_bitcoin_address_old_format(self.name):
                raise ValidationError(
                    _("Bitcoin Address '%s' doesn't seem to valid " "Bitcoin Address")
                    % self.name
                )


class BitcoinRate(models.Model):
    # This stores URL for rate lookup and other related key configuration.
    _name = "bitcoin.rate"
    _description = "Bitcoin Rate"

    url = fields.Char(
        "Bitcoin Rate URL",
        default="https://blockchain.info/tobtc?" "currency={CURRENCY}&value={AMOUNT}",
    )
    rate_lines = fields.One2many(
        "bitcoin.rate.line",
        "rate_id",
        "Rates",
    )

    markup = fields.Float("Markup (%)")
    unit = fields.Selection(
        [("BTC", "BTC"), ("mBTC", "mBTC")], "Display Unit", default="BTC"
    )
    digits = fields.Integer("Round to Digits", default=4)
    valid_minutes = fields.Integer(
        "Rate Valid For (Minutes)",
        default=20,
        help="after this minutes rate will be checked again for same amount",
    )

    @api.model
    def get_rate(  # noqa: C901
        self, order_id=False, order_ref=False, invoice_id=False, invoice_ref=False
    ):
        # function returns bitcoin rate and address for the order currency
        # and total amount

        sobj = self.search([])
        if len(sobj) != 1:
            return False

        order = invoice = None
        if order_id:
            order = self.env["sale.order"].sudo().browse(int(order_id))
        elif order_ref:
            order = self.env["sale.order"].search([("name", "=", order_ref)], limit=1)
            if not order:
                _logger.warning("Sale Order with ref %s is missing" % order_ref)
                return False

        if invoice_id:
            invoice = self.env["account.move"].sudo().browse(int(invoice_id))
        elif invoice_ref:
            invoice = self.env["account.move"].search(
                [("name", "=", invoice_ref)], limit=1
            )
            if not invoice:
                _logger.warning("Invoice with ref %s is missing" % order_ref)
                return False

        if order:
            domain = [("order_id", "=", order.id)]
            currency = order.pricelist_id.currency_id
            amount_total = order.amount_total
            name = order.name
        elif invoice:
            domain = [("invoice_id", "=", invoice.id)]
            currency = invoice.currency_id
            amount_total = invoice.amount_total
            name = invoice.name
        else:
            raise UserError(_("Payment reference required"))

        addr_ids = self.env["bitcoin.address"].search(domain, limit=1)
        if not addr_ids:
            addr_ids = self.env["bitcoin.address"].search(
                [("order_id", "=", False), ("invoice_id", "=", False)], limit=1
            )
            if not addr_ids:
                _logger.error("No Bitcoin Address configured")
                return False

        domain.extend(
            [
                ("currency_id", "=", currency.id),
                ("amount", "=", amount_total),
                (
                    "create_date",
                    ">=",
                    (
                        datetime.now() - relativedelta(minutes=sobj.valid_minutes)
                    ).strftime("%Y-%m-%d %H:%M:00"),
                ),
            ]
        )

        valid_rate_exists = self.env["bitcoin.rate.line"].sudo().search(domain, limit=1)
        if valid_rate_exists:
            # Rate was looked up within valid time limit, so we are using the
            # valid one
            rate = valid_rate_exists[0].rate
        else:
            # Check for New Rate
            url = sobj.url.replace("{CURRENCY}", currency.name)
            url = url.replace("{AMOUNT}", str(amount_total))
            response = requests.get(url)
            if response.status_code != 200:
                _logger.error("can not find Bitcoin exchange rate")
                return False

            rate = float(response.content)
            # rate lookup entry saves in logs
            self.env["bitcoin.rate.line"].sudo().create(
                {
                    "rate_id": sobj.id,
                    "rate": rate,
                    "amount": amount_total,
                    "currency_id": currency.id,
                    "order_id": order.id if order else None,
                    "invoice_id": invoice.id if invoice else None,
                    "name": name,
                }
            )
            order.message_post(
                body=_(
                    """Bitcoin Address: <span><a target="_blank" \
                    href="https://www.blockchain.com/btc/address/%(address_id)s?\
                    filter=5">%(address_id1)s</a></span>, <span>%(rate)s </span> BTC"""
                )
                % {
                    "address_id": addr_ids[0].name,
                    "address_id1": addr_ids[0].name,
                    "rate": rate,
                }
            )
        if addr_ids and rate:
            addr_ids.sudo().write(
                {
                    "order_id": order.id if order else None,
                    "invoice_id": invoice.id if invoice else None,
                }
            )
            b_addr = addr_ids.name

            if sobj.markup:
                b_amount = (rate * (sobj.markup / 100)) + rate
            else:
                b_amount = rate

            if sobj.unit == "mBTC":
                b_amount = b_amount * 1000.0

        return (b_addr, round(b_amount, sobj.digits), sobj.unit)

    def test_rate(self):
        order = self.env["sale.order"].search([], limit=1)
        if order:
            self.env["bitcoin.rate"].get_rate(order.id)
        return True


class BitcoinRateLine(models.Model):
    # Store Log Rate lookup lines
    _name = "bitcoin.rate.line"
    _order = "create_date desc"
    _description = "Bitcoin Rate Lines"

    rate_id = fields.Many2one("bitcoin.rate", "Bitcoin Rate")
    create_date = fields.Datetime()
    rate = fields.Float("BTC", digits=(20, 8))

    currency_id = fields.Many2one("res.currency", "Currency")
    amount = fields.Float(digits=(20, 6))
    order_id = fields.Integer("Order ID")
    invoice_id = fields.Integer("Invoice ID")
    name = fields.Char("Origin")
