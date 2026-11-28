from odoo.tools.sql import column_exists


def migrate(cr, version):
    """Take over the declared percentage from stock_picking_declared_value"""
    if not column_exists(cr, "delivery_carrier", "declared_amount_percentage"):
        return
    cr.execute(
        """
        UPDATE delivery_carrier
        SET declared_value_percentage = declared_amount_percentage
        WHERE delivery_type = 'dhl_parcel_de_provider'
        """
    )
