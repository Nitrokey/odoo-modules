from odoo import fields, models


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    outside_customs_territory = fields.Boolean(
        default=False,
        help="When set, this state/region is treated as outside the customs "
        "territory of its parent country, even if that country belongs to a "
        "customs union (e.g. the EU). Carrier integrations use this flag to "
        "require customs export documentation for shipments to this region.",
    )
