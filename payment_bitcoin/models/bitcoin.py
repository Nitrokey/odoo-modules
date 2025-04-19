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
    """
    Validate a segwit Bitcoin address.

    This function checks if the given address is a valid segwit Bitcoin address.

    Args:
        addr (str): The Bitcoin address to validate

    Returns:
        bool: True if the address is valid, False otherwise
    """
    _logger.debug("Validating segwit Bitcoin address: %s", addr)

    try:
        hrpgot, data = bech32_decode(addr)

        if hrpgot is None or data is None:
            _logger.debug("Invalid bech32 encoding for address: %s", addr)
            return False

        _logger.debug(
            "Decoded address %s: hrp=%s, data length=%s",
            addr,
            hrpgot,
            len(data) if data else 0,
        )

        if hrpgot not in ["bc", "tb"]:
            _logger.debug(
                "Invalid hrp for address %s: %s (expected 'bc' or 'tb')", addr, hrpgot
            )
            return False

        decoded = convertbits(data[1:], 5, 8, False)

        if decoded is None:
            _logger.debug("Failed to convert bits for address: %s", addr)
            return False

        _logger.debug("Converted data length for address %s: %s", addr, len(decoded))

        if len(decoded) < 2 or len(decoded) > 40:
            _logger.debug(
                "Invalid decoded data length for address %s: %s (expected 2-40)",
                addr,
                len(decoded),
            )
            return False

        if data[0] > 16:
            _logger.debug(
                "Invalid witness version for address %s: %s (expected 0-16)",
                addr,
                data[0],
            )
            return False

        if data[0] == 0 and len(decoded) != 20 and len(decoded) != 32:
            _logger.debug(
                "Invalid decoded data length for v0 segwit address %s: %s (expected 20 or 32)",
                addr,
                len(decoded),
            )
            return False

        _logger.debug("Address %s is a valid segwit Bitcoin address", addr)
        return True
    except Exception as e:
        _logger.error("Error validating segwit Bitcoin address %s: %s", addr, str(e))
        return False


def decode_base58(bc, length):
    """
    Decode a base58 encoded string to bytes.

    Args:
        bc (str): The base58 encoded string
        length (int): The expected length of the decoded bytes

    Returns:
        bytes: The decoded bytes
    """
    try:
        n = 0
        for char in bc:
            if char not in DIGITS58:
                _logger.error("Invalid character in base58 string: %s", char)
                raise ValueError(f"Invalid character in base58 string: {char}")
            n = n * 58 + DIGITS58.index(char)
        return codecs.decode(("%%0%dx" % (length << 1) % n), "hex_codec")[-length:]
    except Exception as e:
        _logger.error("Error decoding base58 string: %s", str(e))
        raise


def validate_bitcoin_address_old_format(address):
    """
    Validate a legacy (non-segwit) Bitcoin address.

    This function checks if the given address is a valid legacy Bitcoin address.

    Args:
        address (str): The Bitcoin address to validate

    Returns:
        bool: True if the address is valid, False otherwise
    """
    _logger.debug("Validating legacy Bitcoin address: %s", address)

    try:
        bcbytes = decode_base58(address, 25)
        checksum = bcbytes[-4:]
        calculated_checksum = sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]

        is_valid = checksum == calculated_checksum

        if is_valid:
            _logger.debug("Address %s is a valid legacy Bitcoin address", address)
        else:
            _logger.debug(
                "Invalid checksum for address %s: %s != %s",
                address,
                checksum.hex(),
                calculated_checksum.hex(),
            )

        return is_valid
    except Exception as e:
        _logger.error("Error validating legacy Bitcoin address %s: %s", address, str(e))
        return False


def check_received(addr):
    """
    Check if a Bitcoin payment has been received at the given address.

    This function makes API calls to blockchain.info to get information about
    transactions for a specific address and checks if they have enough confirmations.

    Args:
        addr (str): The Bitcoin address to check

    Returns:
        dict: Information about received payments, or None if an error occurred
    """
    addr_info_url = "https://blockchain.info/rawaddr/{addr}"
    tx_info_url = "https://blockchain.info/rawtx/{tx}"
    latest_block_url = "https://blockchain.info/latestblock"

    needed_confirms = 3

    _logger.info("Checking Bitcoin payments for address: %s", addr)

    try:
        # Get the current block height
        _logger.debug("Fetching latest block from %s", latest_block_url)
        latest_block_response = requests.get(latest_block_url, timeout=10)
        if latest_block_response.status_code != 200:
            _logger.error(
                "Failed to get latest block. Status code: %s, Response: %s",
                latest_block_response.status_code,
                latest_block_response.text,
            )
            return None

        latest_block_data = latest_block_response.json()
        _logger.debug("Latest block data: %s", latest_block_data)

        if "height" not in latest_block_data:
            _logger.error(
                "Latest block data does not contain 'height' field: %s",
                latest_block_data,
            )
            return None

        current_height = latest_block_data["height"]
        _logger.info("Current block height: %s", current_height)

        # Get address information
        _logger.debug("Fetching address info from %s", addr_info_url.format(addr=addr))
        addr_info_response = requests.get(addr_info_url.format(addr=addr), timeout=10)
        if addr_info_response.status_code != 200:
            _logger.error(
                "Failed to get address info. Status code: %s, Response: %s",
                addr_info_response.status_code,
                addr_info_response.text,
            )
            return None

        addr_info_data = addr_info_response.json()
        _logger.debug("Address info data: %s", addr_info_data)

        if "txs" not in addr_info_data:
            _logger.error(
                "Address info data does not contain 'txs' field: %s", addr_info_data
            )
            return None

        txs = addr_info_data["txs"]
        _logger.info("Found %s transactions for address %s", len(txs), addr)

        # No transactions -> nothing received
        if not txs:
            _logger.info("No transactions found for address %s", addr)
            return {"received": 0, "min_conf": 0, "when": None, "transaction": None}

        min_conf = None
        for tx in txs:
            if "hash" not in tx:
                _logger.error("Transaction does not contain 'hash' field: %s", tx)
                continue

            tx_hash = tx["hash"]
            _logger.debug("Checking transaction %s", tx_hash)

            # Get transaction information
            _logger.debug(
                "Fetching transaction info from %s", tx_info_url.format(tx=tx_hash)
            )
            tx_info_response = requests.get(tx_info_url.format(tx=tx_hash), timeout=10)
            if tx_info_response.status_code != 200:
                _logger.error(
                    "Failed to get transaction info. Status code: %s, Response: %s",
                    tx_info_response.status_code,
                    tx_info_response.text,
                )
                continue

            tx_info_data = tx_info_response.json()
            _logger.debug("Transaction info data: %s", tx_info_data)

            if "block_height" not in tx_info_data:
                _logger.error(
                    "Transaction info data does not contain 'block_height' field: %s",
                    tx_info_data,
                )
                continue

            b_height = tx_info_data["block_height"]
            # confirmations = current_block_height - transaction_block_height - 1
            conf = current_height - b_height - 1 if b_height else 0
            _logger.info(
                "Transaction %s has %s confirmations (needed: %s)",
                tx_hash,
                conf,
                needed_confirms,
            )

            if conf < needed_confirms:
                _logger.info(
                    "Transaction %s has insufficient confirmations (%s < %s)",
                    tx_hash,
                    conf,
                    needed_confirms,
                )
                return {"received": 0, "min_conf": 0, "when": None, "transaction": None}

            min_conf = min(conf, min_conf) if min_conf is not None else conf
            last_trans = tx

        # Check if total_received is in the response
        if "total_received" not in addr_info_data:
            _logger.error(
                "Address info data does not contain 'total_received' field: %s",
                addr_info_data,
            )
            return None

        # Here all transactions are >= needed_confirms times confirmed,
        # we consider total_received as "received" btc
        total_received = addr_info_data["total_received"] / 1e8
        _logger.info(
            "Total received for address %s: %s BTC with %s confirmations",
            addr,
            total_received,
            min_conf,
        )

        out = {
            "received": total_received,
            "min_conf": min_conf,
            "transaction": last_trans.get("hash"),
        }

        # Let's define the "transaction-finalized" when the last transaction
        # reached needed_confirms confirmations
        # so the time when this happened is ~ 10minutes * (confirmations - needed_confirms)
        out["when"] = datetime.now() - td(minutes=10) * (min_conf - needed_confirms)
        return out

    except requests.RequestException as e:
        _logger.error("Network error while checking Bitcoin payments: %s", str(e))
        return None
    except ValueError as e:
        _logger.error("JSON parsing error while checking Bitcoin payments: %s", str(e))
        return None
    except KeyError as e:
        _logger.error(
            "Missing key in API response while checking Bitcoin payments: %s", str(e)
        )
        return None
    except Exception as e:
        _logger.error("Unexpected error while checking Bitcoin payments: %s", str(e))
        return None


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
        """
        Cron job to check for Bitcoin payments and reconcile them with orders/invoices.

        This method is called by the scheduled action to check for Bitcoin payments
        and reconcile them with the corresponding orders/invoices.
        """
        _logger.info("Starting Bitcoin payment reconciliation cron job")

        try:
            # Get the Bitcoin payment acquirer
            acquirer_obj = self.env["payment.acquirer"].search(
                [("provider", "=", "bitcoin")]
            )

            if not acquirer_obj:
                _logger.error("No Bitcoin payment acquirer found")
                return

            _logger.info("Found Bitcoin payment acquirer: %s", acquirer_obj.name)

            # Get the payment journal
            payment_journal_obj = acquirer_obj.journal_id
            if not payment_journal_obj:
                _logger.error(
                    "No payment journal configured for Bitcoin payment acquirer"
                )
                return

            _logger.info("Using payment journal: %s", payment_journal_obj.name)

            # Get the check_hours parameter
            check_hours = acquirer_obj.bitcoin_order_older_than
            check_date = datetime.now() - td(hours=int(check_hours))
            _logger.info("Checking orders created after: %s", check_date)

            # Search for Bitcoin addresses that are assigned to orders or invoices
            # but not yet used
            bitcoin_addresses = self.search(
                [
                    "|",
                    ("order_id", "!=", False),
                    ("invoice_id", "!=", False),
                    ("is_btc_used", "=", False),
                ]
            )

            _logger.info("Found %s Bitcoin addresses to check", len(bitcoin_addresses))

            for bit_add_obj in bitcoin_addresses:
                # Skip if the order is too old
                if (
                    bit_add_obj.order_id
                    and bit_add_obj.order_id.create_date < check_date
                ):
                    continue

                # Check if a payment has been received
                _logger.info(
                    "Checking for received payments at address: %s", bit_add_obj.name
                )
                address_info = check_received(bit_add_obj.name)

                if not address_info:
                    _logger.warning(
                        "Failed to get payment information for address: %s",
                        bit_add_obj.name,
                    )
                    continue

                _logger.info(
                    "Payment information for address %s: %s",
                    bit_add_obj.name,
                    address_info,
                )

                # Set up the domain for searching rate lines
                if bit_add_obj.order_id:
                    domain = [
                        ("order_id", "=", bit_add_obj.order_id.id),
                        ("name", "=", bit_add_obj.order_id.name),
                    ]
                    _logger.info(
                        "Processing order: %s (ID: %s)",
                        bit_add_obj.order_id.name,
                        bit_add_obj.order_id.id,
                    )
                elif bit_add_obj.invoice_id:
                    domain = [
                        ("invoice_id", "=", bit_add_obj.invoice_id.id),
                        ("name", "=", bit_add_obj.invoice_id.name),
                    ]
                    _logger.info(
                        "Processing invoice: %s (ID: %s)",
                        bit_add_obj.invoice_id.name,
                        bit_add_obj.invoice_id.id,
                    )
                else:
                    _logger.warning(
                        "Bitcoin address %s has no order or invoice assigned",
                        bit_add_obj.name,
                    )
                    continue

                recs_to_post = list(
                    filter(None, (bit_add_obj.order_id, bit_add_obj.invoice_id))
                )

                # Get the expected rate
                valid_rate_exists = (
                    self.env["bitcoin.rate.line"].sudo().search(domain, limit=1)
                )

                valid_rate = 0.0
                if valid_rate_exists:
                    valid_rate = valid_rate_exists.rate
                    _logger.info(
                        "Found valid rate for %s: %s BTC",
                        bit_add_obj.order_id.name
                        if bit_add_obj.order_id
                        else bit_add_obj.invoice_id.name,
                        valid_rate,
                    )
                else:
                    _logger.warning(
                        "No valid rate found for %s",
                        bit_add_obj.order_id.name
                        if bit_add_obj.order_id
                        else bit_add_obj.invoice_id.name,
                    )

                # Convert the received amount to standard format
                amount_received = self.convert_num_to_standard(address_info["received"])
                _logger.info(
                    "Received amount: %s BTC, Expected amount: %s BTC",
                    amount_received,
                    valid_rate,
                )

                # If the received amount is sufficient
                if valid_rate and address_info["received"] >= valid_rate:
                    _logger.info(
                        "Sufficient payment received: %s BTC >= %s BTC",
                        amount_received,
                        valid_rate,
                    )

                    try:
                        open_invoice_objs = None

                        # Handle order case
                        if (
                            bit_add_obj.order_id
                            and bit_add_obj.order_id.state == "cancel"
                        ):
                            _logger.info(
                                "Order %s is in 'cancel' state, confirming it",
                                bit_add_obj.order_id.name,
                            )

                            if bit_add_obj.order_id.state not in ("done", "sale"):
                                try:
                                    bit_add_obj.order_id.action_confirm()
                                    _logger.info(
                                        "Order %s confirmed successfully",
                                        bit_add_obj.order_id.name,
                                    )
                                except Exception as e:
                                    _logger.error(
                                        "Failed to confirm order %s: %s",
                                        bit_add_obj.order_id.name,
                                        str(e),
                                    )
                                    continue

                            if not bit_add_obj.order_id.invoice_ids:
                                try:
                                    _logger.info(
                                        "Creating invoices for order %s",
                                        bit_add_obj.order_id.name,
                                    )
                                    bit_add_obj.order_id._create_invoices()
                                except Exception as e:
                                    _logger.error(
                                        "Failed to create invoices for order %s: %s",
                                        bit_add_obj.order_id.name,
                                        str(e),
                                    )
                                    continue

                            invoice_objs = bit_add_obj.order_id.mapped(
                                "invoice_ids"
                            ).filtered(lambda r: r.state == "draft")

                            _logger.info(
                                "Found %s draft invoices for order %s",
                                len(invoice_objs),
                                bit_add_obj.order_id.name,
                            )

                            if invoice_objs:
                                try:
                                    invoice_objs.action_post()
                                    _logger.info(
                                        "Posted %s invoices for order %s",
                                        len(invoice_objs),
                                        bit_add_obj.order_id.name,
                                    )
                                except Exception as e:
                                    _logger.error(
                                        "Failed to post invoices for order %s: %s",
                                        bit_add_obj.order_id.name,
                                        str(e),
                                    )
                                    continue

                            open_invoice_objs = bit_add_obj.order_id.mapped(
                                "invoice_ids"
                            ).filtered(lambda r: r.state == "posted")

                            _logger.info(
                                "Found %s posted invoices for order %s",
                                len(open_invoice_objs),
                                bit_add_obj.order_id.name,
                            )

                        # Handle invoice case
                        if bit_add_obj.invoice_id:
                            _logger.info(
                                "Processing invoice %s", bit_add_obj.invoice_id.name
                            )

                            invoice_objs = bit_add_obj.invoice_id.filtered(
                                lambda r: r.state == "draft"
                            )

                            _logger.info("Found %s draft invoices", len(invoice_objs))

                            open_invoice_objs = bit_add_obj.invoice_id.filtered(
                                lambda r: r.state == "posted"
                            )

                            _logger.info(
                                "Found %s posted invoices", len(open_invoice_objs)
                            )

                        # Create payment and reconcile
                        if open_invoice_objs:
                            _logger.info(
                                "Creating payment for %s posted invoices",
                                len(open_invoice_objs),
                            )

                            try:
                                line_to_reconcile = self.env["account.move.line"]
                                payment_line = self.env["account.move.line"]

                                payment_methods = (
                                    payment_journal_obj.available_payment_method_ids.ids
                                )

                                if not payment_methods:
                                    _logger.error(
                                        "No payment methods available for journal %s",
                                        payment_journal_obj.name,
                                    )
                                    continue

                                _logger.info(
                                    "Using payment method: %s",
                                    payment_methods[0] if payment_methods else "None",
                                )

                                # Prepare payment values
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

                                _logger.info(
                                    "Creating payment with values: %s", payment_vals
                                )

                                # Create payment
                                payment_obj = (
                                    self.env["account.payment"]
                                    .sudo()
                                    .create(payment_vals)
                                )

                                _logger.info("Payment created: %s", payment_obj.id)

                                # Post payment
                                try:
                                    payment_obj.action_post()
                                    _logger.info("Payment posted successfully")
                                except Exception as e:
                                    _logger.error("Failed to post payment: %s", str(e))
                                    continue

                                payment_move = payment_obj

                                # Get payment lines to reconcile
                                payment_line = payment_move.line_ids.filtered(
                                    lambda r: not r.reconciled
                                    and r.account_id.internal_type
                                    in ("payable", "receivable")
                                )

                                _logger.info(
                                    "Found %s payment lines to reconcile",
                                    len(payment_line),
                                )

                                # Get invoice lines to reconcile
                                for inv in open_invoice_objs:
                                    inv_lines = inv.line_ids.filtered(
                                        lambda r: not r.reconciled
                                        and r.account_id.internal_type
                                        in ("payable", "receivable")
                                    )

                                    _logger.info(
                                        "Found %s lines to reconcile for invoice %s",
                                        len(inv_lines),
                                        inv.name,
                                    )

                                    line_to_reconcile += inv_lines

                                # Reconcile payment with invoices
                                try:
                                    (line_to_reconcile + payment_line).reconcile()
                                    _logger.info(
                                        "Successfully reconciled payment with %s invoice lines",
                                        len(line_to_reconcile),
                                    )
                                except Exception as e:
                                    _logger.error(
                                        "Failed to reconcile payment with invoices: %s",
                                        str(e),
                                    )
                                    continue

                                # Mark Bitcoin address as used
                                bit_add_obj.write({"is_btc_used": True})
                                _logger.info(
                                    "Marked Bitcoin address %s as used",
                                    bit_add_obj.name,
                                )

                                # Post message based on received amount
                                if float(address_info["received"]) == float(valid_rate):
                                    _logger.info(
                                        "Exact payment received: %s BTC",
                                        amount_received,
                                    )

                                    for rec in recs_to_post:
                                        message = (
                                            _(
                                                "Bitcoin transaction %(transaction)s for \
                                            %(address)s with %(amount)s BTC has been\
                                             confirmed. The corresponding payment is \
                                             posted: %(invoices)s"
                                            )
                                            % {
                                                "transaction": address_info.get(
                                                    "transaction"
                                                ),
                                                "address": bit_add_obj.name,
                                                "amount": amount_received,
                                                "invoices": self.cnvrt_list_to_string(
                                                    invoice_objs.mapped("name")
                                                ),
                                            }
                                        )

                                        rec.message_post(body=message)
                                        _logger.info(
                                            "Posted message for %s: %s",
                                            rec._name,
                                            message,
                                        )

                                elif float(address_info["received"]) > float(
                                    valid_rate
                                ):
                                    max_amount_received = float(
                                        address_info["received"]
                                    ) - float(valid_rate)

                                    _logger.info(
                                        "Excess payment received: %s BTC (excess: %s BTC)",
                                        amount_received,
                                        self.convert_num_to_standard(
                                            max_amount_received
                                        ),
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
                                            "transaction": address_info.get(
                                                "transaction"
                                            ),
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
                                        _logger.info(
                                            "Posted message for %s: %s",
                                            rec._name,
                                            log_max_amt,
                                        )

                            except Exception as e:
                                _logger.error(
                                    "Error during payment creation and reconciliation: %s",
                                    str(e),
                                )
                                continue
                        else:
                            _logger.warning(
                                "No open invoices found for %s",
                                bit_add_obj.order_id.name
                                if bit_add_obj.order_id
                                else bit_add_obj.invoice_id.name,
                            )

                    except Exception as e:
                        _logger.error(
                            "Error processing payment for address %s: %s",
                            bit_add_obj.name,
                            str(e),
                        )
                        continue

                # If the received amount is insufficient
                else:
                    _logger.info(
                        "Insufficient payment received: %s BTC < %s BTC",
                        amount_received,
                        valid_rate,
                    )

                    insufficiant_amount = float(valid_rate) - float(
                        address_info["received"]
                    )

                    if address_info.get("transaction") and float(amount_received) > 0.0:
                        _logger.info(
                            "Partial payment received: %s BTC (missing: %s BTC)",
                            amount_received,
                            self.convert_num_to_standard(insufficiant_amount),
                        )

                        for rec in recs_to_post:
                            message = (
                                _(
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

                            rec.message_post(body=message)
                            _logger.info(
                                "Posted message for %s: %s", rec._name, message
                            )

                    # Send email notification if configured
                    if acquirer_obj.bitcoin_send_email and bit_add_obj.order_id:
                        try:
                            _logger.info(
                                "Sending email notification for order %s",
                                bit_add_obj.order_id.name,
                            )

                            template_obj = self.env.ref(
                                "payment_bitcoin.mail_template_data_bit_coin_order_notification"
                            )

                            template_obj.send_mail(
                                bit_add_obj.order_id.id,
                                force_send=True,
                                raise_exception=True,
                            )

                            _logger.info(
                                "Email notification sent successfully for order %s",
                                bit_add_obj.order_id.name,
                            )

                        except Exception as e:
                            _logger.error(
                                "Failed to send email notification for order %s: %s",
                                bit_add_obj.order_id.name,
                                str(e),
                            )

            _logger.info("Bitcoin payment reconciliation cron job completed")

        except Exception as e:
            _logger.error(
                "Error in Bitcoin payment reconciliation cron job: %s", str(e)
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
        """
        Validate Bitcoin address when creating or updating a record.

        This method is called when a Bitcoin address is created or updated.
        It checks if the address is valid using both segwit and legacy validation.
        """
        _logger.info("Validating Bitcoin address: %s", self.name)

        # Try segwit validation first
        is_segwit_valid = validate_bitcoin_address(self.name)

        if is_segwit_valid:
            _logger.info("Bitcoin address %s is valid (segwit format)", self.name)
            return

        # If not segwit, try legacy validation
        _logger.info(
            "Bitcoin address %s is not a valid segwit address, trying legacy format",
            self.name,
        )

        try:
            is_legacy_valid = validate_bitcoin_address_old_format(self.name)

            if is_legacy_valid:
                _logger.info("Bitcoin address %s is valid (legacy format)", self.name)
                return

            # If neither segwit nor legacy validation passed, raise an error
            _logger.error(
                "Bitcoin address %s is not valid (neither segwit nor legacy format)",
                self.name,
            )
            raise ValidationError(
                _(
                    "Bitcoin Address '%(address)s' doesn't seem to be a valid Bitcoin Address"
                )
                % {
                    "address": self.name,
                }
            )
        except Exception as e:
            _logger.error("Error validating Bitcoin address %s: %s", self.name, str(e))
            raise ValidationError(
                _("Error validating Bitcoin Address '%(address)s': %(error)s")
                % {
                    "address": self.name,
                    "error": str(e),
                }
            ) from e


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
        """
        Get Bitcoin rate and address for an order or invoice.

        This method returns the Bitcoin rate and address for the order currency
        and total amount. It first checks if a valid rate exists within the
        configured time limit, and if not, it fetches a new rate from the
        blockchain.info API.

        Args:
            order_id: ID of the sale order
            order_ref: Reference of the sale order
            invoice_id: ID of the invoice
            invoice_ref: Reference of the invoice

        Returns:
            tuple: (bitcoin_address, bitcoin_amount, unit) or False if an error occurred
        """
        _logger.info(
            "Getting Bitcoin rate for order_id=%s, order_ref=%s, invoice_id=%s, invoice_ref=%s",
            order_id,
            order_ref,
            invoice_id,
            invoice_ref,
        )

        try:
            # Get the Bitcoin rate configuration
            sobj = self.search([])
            if len(sobj) != 1:
                _logger.error(
                    "No Bitcoin rate configuration found or multiple configurations exist"
                )
                return False

            _logger.info("Found Bitcoin rate configuration: %s", sobj.id)

            # Get the order or invoice
            order = invoice = None
            if order_id:
                try:
                    order = self.env["sale.order"].sudo().browse(int(order_id))
                    _logger.info("Found order with ID %s: %s", order_id, order.name)
                except Exception as e:
                    _logger.error(
                        "Error finding order with ID %s: %s", order_id, str(e)
                    )
                    return False
            elif order_ref:
                try:
                    order = self.env["sale.order"].search(
                        [("name", "=", order_ref)], limit=1
                    )
                    if not order:
                        _logger.warning("Sale Order with ref %s is missing", order_ref)
                        return False
                    _logger.info("Found order with ref %s: %s", order_ref, order.id)
                except Exception as e:
                    _logger.error(
                        "Error finding order with ref %s: %s", order_ref, str(e)
                    )
                    return False

            if invoice_id:
                try:
                    invoice = self.env["account.move"].sudo().browse(int(invoice_id))
                    _logger.info(
                        "Found invoice with ID %s: %s", invoice_id, invoice.name
                    )
                except Exception as e:
                    _logger.error(
                        "Error finding invoice with ID %s: %s", invoice_id, str(e)
                    )
                    return False
            elif invoice_ref:
                try:
                    invoice = self.env["account.move"].search(
                        [("name", "=", invoice_ref)], limit=1
                    )
                    if not invoice:
                        _logger.warning("Invoice with ref %s is missing", invoice_ref)
                        return False
                    _logger.info(
                        "Found invoice with ref %s: %s", invoice_ref, invoice.id
                    )
                except Exception as e:
                    _logger.error(
                        "Error finding invoice with ref %s: %s", invoice_ref, str(e)
                    )
                    return False

            # Set up the domain for searching rate lines
            if order:
                domain = [("order_id", "=", order.id)]
                currency = order.pricelist_id.currency_id
                amount_total = order.amount_total
                name = order.name
                _logger.info(
                    "Using order %s with currency %s and amount %s",
                    order.name,
                    currency.name,
                    amount_total,
                )
            elif invoice:
                domain = [("invoice_id", "=", invoice.id)]
                currency = invoice.currency_id
                amount_total = invoice.amount_total
                name = invoice.name
                _logger.info(
                    "Using invoice %s with currency %s and amount %s",
                    invoice.name,
                    currency.name,
                    amount_total,
                )
            else:
                _logger.error("No order or invoice provided")
                raise UserError(_("Payment reference required"))

            # Find a Bitcoin address
            try:
                addr_ids = self.env["bitcoin.address"].search(domain, limit=1)
                if not addr_ids:
                    _logger.info(
                        "No Bitcoin address found for the order/invoice, "
                        "searching for unused addresses"
                    )
                    addr_ids = self.env["bitcoin.address"].search(
                        [("order_id", "=", False), ("invoice_id", "=", False)], limit=1
                    )
                    if not addr_ids:
                        _logger.error("No Bitcoin Address configured")
                        return False
                _logger.info("Using Bitcoin address: %s", addr_ids.name)
            except Exception as e:
                _logger.error("Error finding Bitcoin address: %s", str(e))
                return False

            # Extend the domain to search for valid rates
            valid_minutes = sobj.valid_minutes
            valid_from = (
                datetime.now() - relativedelta(minutes=valid_minutes)
            ).strftime("%Y-%m-%d %H:%M:00")

            domain.extend(
                [
                    ("currency_id", "=", currency.id),
                    ("amount", "=", amount_total),
                    ("create_date", ">=", valid_from),
                ]
            )

            _logger.info(
                "Searching for valid rate with domain: %s (valid from: %s)",
                domain,
                valid_from,
            )

            # Check if a valid rate exists
            try:
                valid_rate_exists = (
                    self.env["bitcoin.rate.line"].sudo().search(domain, limit=1)
                )
                if valid_rate_exists:
                    # Rate was looked up within valid time limit, so we are using the valid one
                    rate = valid_rate_exists[0].rate
                    _logger.info(
                        "Found valid rate: %s BTC (created at: %s)",
                        rate,
                        valid_rate_exists[0].create_date,
                    )
                else:
                    _logger.info("No valid rate found, fetching new rate from API")

                    # Check for New Rate
                    url = sobj.url.replace("{CURRENCY}", currency.name)
                    url = url.replace("{AMOUNT}", str(amount_total))

                    _logger.info("Fetching Bitcoin rate from URL: %s", url)

                    try:
                        response = requests.get(url, timeout=10)

                        if response.status_code != 200:
                            _logger.error(
                                "Failed to get Bitcoin exchange rate. "
                                "Status code: %s, Response: %s",
                                response.status_code,
                                response.text,
                            )
                            return False

                        _logger.debug("API response: %s", response.text)

                        try:
                            rate = float(response.content)
                            _logger.info("Received Bitcoin rate: %s BTC", rate)
                        except ValueError as e:
                            _logger.error(
                                "Failed to parse Bitcoin rate from response: %s. Error: %s",
                                response.content,
                                str(e),
                            )
                            return False

                        # Create rate lookup entry
                        try:
                            rate_line = (
                                self.env["bitcoin.rate.line"]
                                .sudo()
                                .create(
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
                            )
                            _logger.info("Created Bitcoin rate line: %s", rate_line.id)
                        except Exception as e:
                            _logger.error(
                                "Failed to create Bitcoin rate line: %s", str(e)
                            )
                            return False

                        # Post message to order/invoice
                        try:
                            message = (
                                _(
                                    """Bitcoin Address: <span><a target="_blank" \
                                href="https://www.blockchain.com/btc/address/%(address_id)s?\
                                filter=5">%(address_id1)s</a></span>, \
                                <span>%(rate)s </span> BTC"""
                                )
                                % {
                                    "address_id": addr_ids[0].name,
                                    "address_id1": addr_ids[0].name,
                                    "rate": rate,
                                }
                            )

                            if order:
                                order.message_post(body=message)
                                _logger.info("Posted message to order %s", order.name)
                            elif invoice:
                                invoice.message_post(body=message)
                                _logger.info(
                                    "Posted message to invoice %s", invoice.name
                                )
                        except Exception as e:
                            _logger.error("Failed to post message: %s", str(e))
                            # Continue anyway, this is not critical

                    except requests.RequestException as e:
                        _logger.error(
                            "Network error while fetching Bitcoin rate: %s", str(e)
                        )
                        return False
                    except Exception as e:
                        _logger.error(
                            "Unexpected error while fetching Bitcoin rate: %s", str(e)
                        )
                        return False
            except Exception as e:
                _logger.error("Error checking for valid rate: %s", str(e))
                return False

            # Assign the Bitcoin address to the order/invoice
            if addr_ids and rate:
                try:
                    addr_ids.sudo().write(
                        {
                            "order_id": order.id if order else None,
                            "invoice_id": invoice.id if invoice else None,
                        }
                    )
                    _logger.info(
                        "Assigned Bitcoin address %s to %s",
                        addr_ids.name,
                        order.name if order else invoice.name,
                    )

                    b_addr = addr_ids.name

                    # Apply markup if configured
                    if sobj.markup:
                        b_amount = (rate * (sobj.markup / 100)) + rate
                        _logger.info(
                            "Applied markup of %s%%: %s BTC -> %s BTC",
                            sobj.markup,
                            rate,
                            b_amount,
                        )
                    else:
                        b_amount = rate

                    # Convert to mBTC if configured
                    if sobj.unit == "mBTC":
                        b_amount = b_amount * 1000.0
                        _logger.info("Converted to mBTC: %s mBTC", b_amount)

                    final_amount = round(b_amount, sobj.digits)
                    _logger.info(
                        "Final Bitcoin amount: %s %s (rounded to %s digits)",
                        final_amount,
                        sobj.unit,
                        sobj.digits,
                    )

                    return (b_addr, final_amount, sobj.unit)
                except Exception as e:
                    _logger.error("Error assigning Bitcoin address: %s", str(e))
                    return False
            else:
                _logger.error(
                    "Missing Bitcoin address or rate: address=%s, rate=%s",
                    addr_ids.name if addr_ids else "None",
                    rate if "rate" in locals() else "None",
                )
                return False

        except Exception as e:
            _logger.error("Unexpected error in get_rate: %s", str(e))
            return False

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
