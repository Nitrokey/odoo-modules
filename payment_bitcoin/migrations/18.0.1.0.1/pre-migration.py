from odoo.tools.sql import column_exists


def migrate(cr, version):
    """Convert transaction amounts stored in mBTC to BTC"""
    if not column_exists(cr, "payment_transaction", "bitcoin_unit"):
        return
    cr.execute(
        """
        UPDATE payment_transaction
        SET bitcoin_amount = bitcoin_amount / 1000.0, bitcoin_unit = 'BTC'
        WHERE bitcoin_unit = 'mBTC'
        """
    )
