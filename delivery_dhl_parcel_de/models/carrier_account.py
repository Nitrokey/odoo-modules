import requests

from odoo import fields, models
from odoo.exceptions import ValidationError


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    use_dhl_parcel_de_shipping_provider = fields.Boolean(
        copy=False,
        string="Use DHL Parcel DE Shipping Provider",
        help="If use DHL Parcel DE shipping provider than value set TRUE.",
        default=False,
    )  # Tempororily field
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
    dhl_api_secret = fields.Char(
        "DHL API Secret",
        copy=False,
        help="Obtained via Get Access! (app creation) and manually approved by DHL.",
    )
    dhl_tracking_url = fields.Char(
        "DHL Tracking URL",
        copy=False,
        default="https://www.dhl.de/en/privatkunden/pakete-empfangen/verfolgen.html?piececode=",
        help="Obtained via Get Access! (app creation) and manually approved by DHL.",
    )
    dhl_access_token = fields.Char(
        "DHL Access Token",
        copy=False,
    )

    def dhl_parcel_de_get_access_token(self):
        """
        This method is used to get access token from DHL Parcel DE Shipping Provider.
        #OAuth2
        """
        url = f"{self.dhl_parcel_de_api_url}/parcel/de/account/auth/ropc/v1/token"

        payload = {
            "grant_type": "password",
            "username": self.dhl_userid,
            "password": self.dhl_password,
            "client_id": self.dhl_api_key,
            "client_secret": self.dhl_api_secret,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            response = requests.request(
                "POST", url, headers=headers, data=payload, timeout=30
            )
            if response.status_code in [200, 201]:
                response_data = response.json()
                if response_data["access_token"]:
                    self.dhl_access_token = response_data["access_token"]
                    return {
                        "effect": {
                            "fadeout": "slow",
                            "message": "Yeah! DHL Token Retrieved successfully!!",
                            "img_url": "/web/static/img/smile.svg",
                            "type": "rainbow_man",
                        }
                    }
                else:
                    raise ValidationError(response_data)  # noqa: B904
            else:
                raise ValidationError(response.text)
        except Exception as e:
            raise ValidationError(e)  # noqa: B904

    def dhl_parcel_de_get_access_token_cron(self):
        for carrier_account_id in self.search(
            [("delivery_type", "=", "dhl_parcel_de_provider")]
        ):
            carrier_account_id.dhl_parcel_de_get_access_token()
