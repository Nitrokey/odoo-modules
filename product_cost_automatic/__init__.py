from odoo import SUPERUSER_ID, api

from . import models, wizard


def _set_is_automatically(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    products = env["product.product"].search([])
    inactive_automatic_products = products.filtered(lambda x: x.standard_price > 0.0)
    inactive_automatic_products.write({"is_automatically": False})
    active_automatic_products = products - inactive_automatic_products
    active_automatic_products.write({"is_automatically": True})
