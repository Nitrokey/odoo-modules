from odoo.addons.payment.tests.common import PaymentAcquirerCommon


class BitcoinCommon(PaymentAcquirerCommon):

    def setUp(self):
        super(BitcoinCommon, self).setUp()

        self.bitcoin = self.env.ref('payment_bitcoin.payment_acquirer_bitcoin')

        self.acquirer = self.bitcoin

