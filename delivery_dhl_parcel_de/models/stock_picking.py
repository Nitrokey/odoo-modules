import binascii
import json

from odoo import fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_return_shipment = fields.Boolean(copy=False)
    picking_type_code = fields.Selection(
        related="picking_type_id.code",
        store=True,
        readonly=True,
    )

    def dhl_parcel_de_provider_return_shipment(self):
        """
        This method is used to return shipment of DHL Parcel.
        @return: Return Label & Tracking Number
        """
        try:
            carrier_id = self.carrier_id
            company_id = carrier_id.company_id
            shipper_address_error = carrier_id.check_address_details(
                self.partner_id, ["zip", "city", "street"]
            )
            if shipper_address_error or not self.shipping_weight:
                raise ValidationError(
                    ", ".join(
                        [
                            "Shipper Address : %s \n" % shipper_address_error  # noqa: UP031
                            if shipper_address_error
                            else "",
                            "Shipping weight is missing!"
                            if not self.shipping_weight
                            else "",
                        ]
                    )
                )
            products_data = carrier_id.prepare_product_data_request(self)
            request_data = json.dumps(
                {
                    "receiverId": carrier_id.dhl_return_receiver_id,
                    "shipmentReference": self.origin or "",
                    "shipper": {
                        "name1": self.partner_id.name or "",
                        "name2": self.partner_id.parent_id
                        and self.partner_id.parent_id.name
                        or "",
                        "addressStreet": self.partner_id.street or "",
                        "addressHouse": self.partner_id.street2
                        or self.partner_id.street
                        or "",
                        "city": self.partner_id.city or "",
                        "email": self.partner_id.email or "",
                        "phone": self.partner_id.phone or "",
                        "postalCode": self.partner_id.zip or "",
                        "state": self.partner_id.state_id
                        and self.partner_id.state_id.code
                        or "",
                    },
                    "itemWeight": {
                        "uom": carrier_id.dhl_weight_uom or "",
                        "value": self.shipping_weight,
                    },
                    "customsDetails": {"items": products_data},
                }
            )
            headers = {
                "content-type": "application/json",
                "Authorization": f"Bearer {company_id.dhl_access_token}",
            }
            api_url = f"{company_id.dhl_parcel_de_api_url}/parcel/de/shipping/returns/v1/orders?labelType=SHIPMENT_LABEL"  # noqa: E501
            request_type = "POST"
            response_status, response_data = (
                carrier_id.dhl_parcel_de_provider_create_shipment(
                    request_type, api_url, request_data, headers
                )
            )
            if response_status and response_data.get("shipmentNo"):
                return_track_number = response_data.get("shipmentNo")
                self.is_return_shipment = True
                self.carrier_tracking_ref = return_track_number
                label_data = response_data.get("label").get("b64")
                label_data = binascii.a2b_base64(label_data)
                message = "Return Shipping Number : %s" % return_track_number  # noqa:UP031
                self.message_post(
                    body=message,
                    attachments=[
                        ("DHL_Return_Label_%s.pdf" % return_track_number, label_data)  # noqa:UP031
                    ],
                )
            else:
                raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e)  # noqa: B904
