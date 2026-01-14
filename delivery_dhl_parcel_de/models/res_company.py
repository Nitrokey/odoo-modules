from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    use_dhl_parcel_de_shipping_provider = fields.Boolean(
        copy=False,
        string="Use DHL Parcel DE Shipping Provider",
        help="If use DHL Parcel DE shipping provider than value set TRUE.",
        default=False,
    )
    dhl_parcel_de_api_url = fields.Char(
        string="DHL API URL", copy=False, default="https://api-sandbox.dhl.com"
    )
    dhl_userid = fields.Char(
        "DHL UserId",
        copy=False,
        help="When use the sandbox account developer id use as the userId."
        "When use the live account application id use as the userId.",
    )
    dhl_password = fields.Char(
        "DHL Password",
        copy=False,
        help="When use the sandbox account developer portal password use "
        "to as the password.When use the live account application "
        "token use to as the password.",
    )
    dhl_api_key = fields.Char(
        "DHL API Key",
        copy=False,
        help="Obtained via Get Access! (app creation) and manually approved by DHL.",
    )
    dhl_tracking_url = fields.Char(
        "DHL Tracking URL",
        copy=False,
        default="https://www.dhl.de/en/privatkunden/pakete-empfangen/verfolgen.html?piececode=",
        help="Obtained via Get Access! (app creation) and manually approved by DHL.",
    )
