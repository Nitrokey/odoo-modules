from ..models.bitcoin import validate_bitcoin_address, check_received
from .common import BitcoinCommon

no_payment_addr = "3FNJPXykZ38UkFBTGLncMQaHxaS7xjm83X"
payment_addr = "3NYbDtMSN84qz71WLaZu1unXrkjew2KrEq"

class TestBitcoinNoPayment(BitcoinCommon):
    def setUp(self):
        super(TestBitcoinNoPayment, self).setUp()
        self.website = self.env.ref("website.default_website")
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
        so = self._create_sale_order(590, partner_id.id) # 590 = 0.0443296 ~=(0.044366 BTC)
        self.btc_adr = self.create_bitcoin_address_data(no_payment_addr, so)
        tx = self.env["payment.transaction"].create({
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "acquirer_id": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "sale_order_ids": [(6, 0, [so.id])],
            "bitcoin_address_link": f"https://www.blockchain.com/btc/address{no_payment_addr}",
            "callback_res_id": so.id,
            "tx_url": "/payment/bitcoin/feedback",
            "amount": so.amount_total
        })
        address_id = self.env["bitcoin.address"].search([("name", "=", no_payment_addr)])

        # Executing cron for bitcoin payment
        if address_id:
            address_id.cron_bitcoin_payment_reconciliation()

        # Checks that no invoice is created for no payment
        invoice_objs = so.mapped("invoice_ids")
        self.assertFalse(invoice_objs)

    def test_bitcoin_payment(self):
        '''This method tests payment is received from bitcoin'''
        partner_id = self.env.user.partner_id
        so = self._create_sale_order(590, partner_id.id) # 590 = 0.0443296 ~=(0.044366 BTC)
        self.btc_adr = self.create_bitcoin_address_data(payment_addr, so)
        tx = self.env["payment.transaction"].create({
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "acquirer_id": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "sale_order_ids": [(6, 0, [so.id])],
            "bitcoin_address_link": f"https://www.blockchain.com/btc/address{payment_addr}",
            "callback_res_id": so.id,
            "return_url": "/shop/payment/validate",
            "amount": so.amount_total,
        })
        address_id = self.env["bitcoin.address"].search([("name","=",payment_addr)])

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
        self.btc_adr = self.create_bitcoin_address_data(payment_addr, so)
        tx = self.env["payment.transaction"].create({
            "reference": so.name,
            "currency_id": self.currency_euro.id,
            "acquirer_id": self.bitcoin.id,
            "partner_id": partner_id.id,
            "type": "form",
            "sale_order_ids": [(6, 0, [so.id])],
            "bitcoin_address_link": f"https://www.blockchain.com/btc/address{payment_addr}",
            "callback_res_id": so.id,
            "return_url": "/shop/payment/validate",
            "amount": so.amount_total,
        })
        address_id = self.env["bitcoin.address"].search([("name", "=", payment_addr)])

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

        # Unlink the bitcoin address record
        self.btc_adr.unlink()

        self.env.ref("payment_bitcoin.mail_template_data_bit_coin_order_notification").write({"auto_delete": True})
