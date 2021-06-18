import sys
import requests
from datetime import timedelta as td
from datetime import datetime as dt

from odoo import _, api, fields, models


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
        # confirmations = current_block_height - transaction_block_height - 1
        conf = current_height - b_height - 1 if b_height else 0
        if conf < needed_confirms:
            return {"received": 0, "min_conf": 0, "when": None}
        min_conf = min(conf, min_conf) if min_conf is not None else conf

    # here all transactions are >= 10 times confirmed,
    # we consider total_received" as "received" btc
    out = {"received": addr_info.json()["total_received"]/1e8, "min_conf": min_conf}
    
    # let's define the "transaction-finalized" when the last transaction reached needed_confirms confirmations
    # so the time when this happened is ~ 10minutes * )confirmations - needed_confirms)
    out["when"] = dt.now() - td(minutes=10) * (min_conf - needed_confirms)
    
    return out


class BitcoinAddress(models.Model):
    _inherit = 'bitcoin.address'

    @api.model
    def cron_bitcoin_payment_reconciliation(self):
        acquirer_obj = self.env['payment.acquirer'].search([('provider', '=', 'bitcoin')])
        payment_journal_obj = acquirer_obj.journal_id
        
        check_hours = self.env['ir.config_parameter'].sudo().get_param('payment_bitcoin.bit_coin_order_older_than', '6')
        check_date = (dt.now() - td(hours=int(check_hours))).strftime("%Y-%m-%d %H:%M:%S")
        
        for bit_add_obj in self.search([('create_date', '>=', check_date)]):
            address_info = check_received(bit_add_obj.name)
            bit_coin_rate = self.env['bitcoin.rate'].get_rate(order_id=bit_add_obj.order_id.id)
            if address_info and bit_coin_rate:
                if address_info['received'] >= bit_coin_rate[1]:
                    if bit_add_obj.order_id.state not in ('cancel'):
                        if bit_add_obj.order_id.state not in ('done', 'sale'):
                            bit_add_obj.order_id.action_confirm()
                        
                        if not bit_add_obj.order_id.invoice_ids:
                            bit_add_obj.order_id.action_invoice_create()
                            
                        invoice_objs = bit_add_obj.order_id.mapped('invoice_ids').filtered(lambda r: r.state in ['draft'])
                        if invoice_objs:
                            invoice_objs.action_invoice_open()
                            
                        open_invoice_objs = bit_add_obj.order_id.mapped('invoice_ids').filtered(lambda r: r.state in ['open'])
                        if open_invoice_objs:
                            line_to_reconcile = self.env['account.move.line']
                            payment_line = self.env['account.move.line']
                            
                            payment_methods = payment_journal_obj.inbound_payment_method_ids.ids
                            payment_vals = {
                                'partner_id': bit_add_obj.order_id.partner_id.id,
                                'payment_type': 'inbound',
                                'partner_type': 'customer',
                                'amount': bit_add_obj.order_id.amount_total,
                                'payment_date': fields.Date.today(),
                                'journal_id': payment_journal_obj.id,
                                'payment_method_id': payment_methods and payment_methods[0] or False
                                }
                            payment_obj = self.env['account.payment'].sudo().create(payment_vals)
                            payment_obj.post()
                            payment_move = payment_obj.move_line_ids.mapped('move_id')
                            payment_line = payment_move.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                            
                            for inv in open_invoice_objs:
                                line_to_reconcile += inv.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                            
                            (line_to_reconcile + payment_line).reconcile()
                else:
                    template_obj = self.env.ref('payment_bitcoin_customization.mail_template_data_bit_coin_order_notification')
                    template_obj.send_mail(bit_add_obj.order_id.id, force_send=True, raise_exception=True)   
                    
                        
    


