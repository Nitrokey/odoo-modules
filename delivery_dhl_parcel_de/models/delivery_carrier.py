import binascii
import json
import logging
import re

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("dhl_parcel_de_provider", "DHL Parcel DE")],
        ondelete={"dhl_parcel_de_provider": "set default"},
    )
    dhl_parcel_de_provider_package_id = fields.Many2one(
        "stock.package.type", string="DHL Package Info", help="Default Package"
    )
    dhl_weight_uom = fields.Selection(
        [("kg", "KG"), ("g", "G")],
        string="DHL Weight UOM",
        help="Weight UOM of the Shipment",
    )
    dhl_services_name = fields.Selection(
        [
            ("V01PAK", "V01PAK-DHL Paket"),
            ("V53WPAK", "V53WPAK-DHL Paket International"),
            ("V54EPAK", "V54EPAK-DHL Europaket"),
            ("V62KP", "V62KP-DHL Kleinpaket"),
            ("V66WPI", "V66WPI-Warenpost International"),
        ],
        string="Product Name",
        help="Shipping Services those are accepted by DHL.",
    )
    dhl_procedure_no = fields.Char(
        string="DHL Procedure Number",
        help="The Procedure refers to DHL products that are used for "
        "shipping and max length is 2 digit.",
    )
    dhl_participation_no = fields.Char(
        string="DHL Participation Number",
        help="Participation number referred to as Partner ID in the web service."
        "The participation is 2 numerical digits from 00 to 99 or "
        "alphanumerical digits from AA to ZZ.",
    )
    dhl_bulky_goods = fields.Boolean(string="Bulky Goods", copy=False)
    dhl_premium = fields.Boolean(string="Premium", copy=False)
    dhl_document_format = fields.Selection(
        [("PDF", "PDF"), ("ZPL2", "ZPL2")],
        string="Label Format",
        help="Label Format",
        default="PDF",
    )
    # international
    dhl_export_type = fields.Selection(
        [
            ("OTHER", "OTHER"),
            ("PRESENT", "PRESENT"),
            ("COMMERCIAL_SAMPLE", "COMMERCIAL SAMPLE"),
            ("DOCUMENT", "DOCUMENT"),
            ("COMMERCIAL_GOODS", "COMMERCIAL GOODS"),
            ("RETURN_OF_GOODS", "RETURN OF GOODS"),
        ],
        string="Export Type",
        help="This contains the category of goods contained in parcel.",
    )
    dhl_export_type_description = fields.Char(
        string="Description", help="Detailed description for OTHER goods."
    )
    dhl_endorsement = fields.Selection(
        [("RETURN", "Return"), ("ABANDON", "Abandon")],
        string="Endorsement",
        help="Endorsement",
        default="RETURN",
    )
    is_return_shipment = fields.Boolean(string="Is Return Order", copy=False)
    dhl_return_receiver_id = fields.Char(
        string="Receiver ID", help="The receiver id of the return shipment."
    )
    dhl_tracking_url = fields.Char(
        "DHL Tracking URL",
        copy=False,
        default="https://www.dhl.de/en/privatkunden/pakete-empfangen/verfolgen.html?piececode=",
        help="Obtained via Get Access! (app creation) and manually approved by DHL.",
    )

    @staticmethod
    def _is_packstation(street2):
        """Return True if street2 indicates a DHL Packstation (locker) delivery."""
        return bool(street2 and "packstation" in street2.lower())

    @staticmethod
    def _get_packstation_locker_id(street2):
        """Extract the locker ID from a street2 field.

        Removes the keyword 'Packstation' (case-insensitive), any adjacent
        colons and surrounding whitespace, returning only the numeric locker ID.

        Examples::

            "Packstation 123"    -> "123"
            "Packstation: 456"   -> "456"
            "PACKSTATION  :  789" -> "789"
        """
        locker_id = re.sub(r"(?i)\s*packstation\s*:?\s*", "", street2).strip()
        return locker_id

    def _calculate_package_insurance(self, picking, package_weight, total_weight):
        """
        Calculate insurance value for a package based on weight distribution.

        :param picking: stock.picking record with declared_value
        :param package_weight: float, weight of the specific package
        :param total_weight: float, total weight of all packages in the shipment
        :return: float, proportional insurance amount for the package
        """
        if not picking.declared_value or total_weight <= 0:
            return 0.0
        return (package_weight / total_weight) * picking.declared_value

    def convert_weight(self, shipping_weight):
        grams_for_kg = 1000  # 1 Kg to Grams
        uom_id = self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()
        if uom_id.name == self.dhl_weight_uom:
            return shipping_weight
        elif uom_id.name == "g" and self.dhl_weight_uom == "kg":
            return round(shipping_weight / grams_for_kg, 3)
        elif uom_id.name == "kg" and self.dhl_weight_uom == "g":
            return int(round(shipping_weight * grams_for_kg, 3))

    def prepare_product_data_request(self, picking):
        products_data = []
        for rec in picking.move_line_ids.filtered("product_id"):
            if picking.sale_id:
                order_lines = rec.move_id.sale_line_id | picking.sale_id.order_line
                product_id = rec.product_id
                bom_line = rec.move_id.bom_line_id
                if bom_line and bom_line.bom_id.product_id:
                    domain = [
                        ("product_id", "=", bom_line.bom_id.product_id.id),
                        ("product_uom_qty", ">", 0),
                    ]
                    find_sale_line_id = order_lines.filtered_domain(domain)[:1]
                elif bom_line and bom_line.bom_id.product_tmpl_id:
                    domain = [
                        (
                            "product_id.product_tmpl_id",
                            "=",
                            bom_line.bom_id.product_tmpl_id.id,
                        ),
                        ("product_uom_qty", ">", 0),
                    ]
                    find_sale_line_id = order_lines.filtered_domain(domain)[:1]
                else:
                    domain = [
                        ("product_id", "=", product_id.id),
                        ("product_uom_qty", ">", 0),
                    ]
                    find_sale_line_id = order_lines.filtered_domain(domain)[:1]

                if not find_sale_line_id:
                    raise ValidationError(
                        _("Proper data of sale order lines not found.")
                    )

                single_unit_price = (
                    find_sale_line_id.price_subtotal / find_sale_line_id.product_uom_qty
                )
                if bom_line and bom_line.bom_id:
                    item_value = single_unit_price / len(bom_line.bom_id.bom_line_ids)
                else:
                    item_value = single_unit_price
            else:
                item_value = rec.sale_price

            product_request = {
                "itemDescription": rec.product_id.name,
                "packagedQuantity": rec.quantity,
                "itemValue": {
                    "currency": self.company_id
                    and self.company_id.currency_id
                    and self.company_id.currency_id.name,
                    "value": round(item_value, 3),
                },
                "itemWeight": {
                    "uom": self.dhl_weight_uom,
                    "value": int(rec.product_id.weight)
                    if self.dhl_weight_uom == "g"
                    else rec.product_id.weight,
                },
            }

            if rec.product_id.hs_code_id:
                product_request["hsCode"] = rec.product_id.hs_code_id.hs_code

            if rec.product_id.origin_country_id:
                product_request["countryOfOrigin"] = (
                    rec.product_id.origin_country_id.code_alpha3
                )
            products_data.append(product_request)

        return products_data

    def check_address_details(self, address_id, required_fields):
        """
        check the address of Shipper and Recipient
        param : address_id: res.partner,
                required_fields: ['zip', 'city', 'country_id', 'street']
        return: missing address message
        """

        res = [field for field in required_fields if not address_id[field]]
        if res:
            return "Missing Values For Address :\n %s" % ", ".join(res).replace(  # noqa: UP031
                "_id", ""
            )

    def dhl_parcel_de_provider_rate_shipment(self, order):
        """
        This method is used for get rate of shipment
        param : order : sale.order
        return: 'success': False : 'error message' : True
        return: 'success': True : 'error_message': False
        """
        # Shipper and Recipient Address
        shipper_address_id = order.warehouse_id.partner_id
        recipient_address_id = order.partner_shipping_id

        shipper_address_error = self.check_address_details(
            shipper_address_id, ["city", "country_id", "street"]
        )
        recipient_address_error = self.check_address_details(
            recipient_address_id, ["city", "country_id", "street"]
        )

        product_weight = order.order_line.filtered(
            lambda x: not x.is_delivery
            and x.product_id.type == "consu"
            and x.product_id.weight <= 0
        )
        product_name = ", ".join(product_weight.mapped("product_id").mapped("name"))

        if shipper_address_error or recipient_address_error or product_name:
            return {
                "success": False,
                "price": 0.0,
                "error_message": "%s %s  %s "  # noqa: UP031
                % (
                    "Shipper Address : %s \n" % (shipper_address_error)  # noqa: UP031
                    if shipper_address_error
                    else "",
                    "Recipient Address : %s \n" % (recipient_address_error)  # noqa: UP031
                    if recipient_address_error
                    else "",
                    "product weight is not available : %s" % (product_name)  # noqa: UP031
                    if product_name
                    else "",
                ),
                "warning_message": False,
            }
        return {
            "success": True,
            "price": 0.0,
            "error_message": False,
            "warning_message": False,
        }

    def dhl_parcel_de_provider_get_package_info(self, picking, insurance_value):
        shipper_address_id = (
            picking.picking_type_id
            and picking.picking_type_id.warehouse_id
            and picking.picking_type_id.warehouse_id.partner_id
        )
        recipient_address_id = picking.partner_id
        if picking.picking_type_id.code == "incoming":
            recipient_address_id, shipper_address_id = (
                shipper_address_id,
                recipient_address_id,
            )

        sender_zip = shipper_address_id.zip or ""
        sender_city = shipper_address_id.city or ""
        sender_country_code = (
            shipper_address_id.country_id
            and shipper_address_id.country_id.code_alpha3
            or ""
        )
        sender_street = shipper_address_id.street or ""
        sender_street2 = shipper_address_id.street2 or ""
        sender_phone = shipper_address_id.phone or ""
        sender_email = shipper_address_id.email or ""

        receiver_company = recipient_address_id.commercial_company_name or ""
        receiver_zip = recipient_address_id.zip or ""
        receiver_city = recipient_address_id.city or ""
        receiver_country_code = (
            recipient_address_id.country_id
            and recipient_address_id.country_id.code_alpha3
            or ""
        )
        receiver_street = recipient_address_id.street or ""
        receiver_street2 = recipient_address_id.street2 or ""
        receiver_phone = recipient_address_id.phone or ""
        receiver_email = recipient_address_id.email or ""
        billingNumber = (
            self.carrier_account_id.account
            + self.dhl_procedure_no
            + self.dhl_participation_no
        )

        if self._is_packstation(receiver_street2):
            locker_id = self._get_packstation_locker_id(receiver_street2)
            consignee = {
                "name1": receiver_company or recipient_address_id.name,
                "name2": receiver_street,
                "addressStreet": "Packstation",
                "addressHouse": locker_id,
                "postalCode": receiver_zip,
                "city": receiver_city,
                "country": receiver_country_code,
                "email": receiver_email,
                "phone": receiver_phone,
            }
        else:
            consignee = {
                "name1": receiver_company or recipient_address_id.name,
                "name2": recipient_address_id.name
                if receiver_company
                else receiver_street2,
                "name3": receiver_street2 if receiver_company else "",
                "addressStreet": receiver_street,
                "postalCode": receiver_zip,
                "city": receiver_city,
                "country": receiver_country_code,
                "email": receiver_email,
                "phone": receiver_phone,
            }

        package_data = {
            "product": self.dhl_services_name,
            "billingNumber": billingNumber,
            "refNo": picking.name or "",
            "shipper": {
                "name1": shipper_address_id.name,
                "name2": sender_street2,
                "addressStreet": sender_street,
                "postalCode": sender_zip,
                "city": sender_city,
                "country": sender_country_code,
                "email": sender_email,
                "phone": sender_phone,
            },
            "consignee": consignee,
        }

        europe_group_id = self.env.ref("base.europe")
        if (
            recipient_address_id.country_id not in europe_group_id.country_ids
            or recipient_address_id.state_id.outside_customs_territory
        ):
            product_data = self.prepare_product_data_request(picking)
            company = self.company_id or self.env.company
            currency = company.currency_id and company.currency_id.name
            package_data["customs"] = {
                "exportType": self.dhl_export_type,
                "exportDescription": self.dhl_export_type_description or "",
                "postalCharges": {
                    "currency": currency,
                    "value": picking.sale_id.order_line.filtered(
                        lambda x: x.is_delivery
                    )[:1].price_subtotal
                    or 0.0,
                },
                "items": product_data,
            }

        consignee = package_data.get("consignee")
        shipper = package_data.get("shipper")
        # Remove empty entries
        for key in ("name1", "name2", "name3", "email", "phone"):
            if not consignee.get(key):
                consignee.pop(key, None)
            if not shipper.get(key):
                shipper.pop(key, None)

        services = {}
        if insurance_value > 0:
            services["additionalInsurance"] = {
                "currency": self.company_id
                and self.company_id.currency_id
                and self.company_id.currency_id.name,
                "value": round(max(1, insurance_value), 2),
            }

        if self.dhl_premium:
            services["premium"] = True
        if self.dhl_bulky_goods:
            services["bulkyGoods"] = True
        if self.dhl_endorsement:
            services["endorsement"] = True
        if services:
            package_data["services"] = services

        return package_data

    def create_dhl_de_package_dict(self, height, length, width, weight):
        return {
            "details": {
                "dim": {
                    "uom": "mm",
                    "height": height,
                    "length": length,
                    "width": width,
                },
                "weight": {
                    "uom": self.dhl_weight_uom,
                    "value": int(weight) if self.dhl_weight_uom == "g" else weight,
                },
            }
        }

    def _verify_dhl_parcel_packages(self, packages):
        package_types = self.env["stock.package.type"].search(
            [
                ("package_carrier_type", "=", self.delivery_type),
                ("max_weight", "!=", 0),
            ]
        )
        if not package_types:
            raise ValidationError(
                _(
                    f"No package types configured for delivery method "
                    f"{self.delivery_type}. Please create at least one "
                    f"package before sending shipment."
                )
            )

        for package in packages:
            package_type = package_types.filtered(
                lambda x: x.shipper_package_code == package.packaging_type  # noqa: B023
            )
            if package_type and package.weight > package_type[:1].max_weight:
                raise ValidationError(
                    _(
                        "The weight of your package is higher than the maximum "
                        "weight authorized for this package type. Please choose "
                        "another package type."
                    )
                )

    def dhl_parcel_de_provider_packages(self, picking):
        package_list = []
        weight_bulk = picking.weight_bulk
        default_package_type = self.dhl_parcel_de_provider_package_id
        packages = self._get_packages_from_picking(picking, default_package_type)
        self._verify_dhl_parcel_packages(packages)

        # Calculate total weight for insurance distribution
        total_weight = sum(package.weight for package in packages)
        if weight_bulk:
            total_weight += weight_bulk

        # Process existing packages with dynamic insurance calculation
        for package in packages:
            dimensions = package.dimension
            height = dimensions.get("dimensions", 0)
            width = dimensions.get("width", 0)
            length = dimensions.get("length", 0)
            weight = self.convert_weight(package.weight)

            # Calculate insurance dynamically based on weight distribution
            insurance_value = self._calculate_package_insurance(
                picking, weight, total_weight
            )

            package_data = self.create_dhl_de_package_dict(
                height, length, width, weight
            )
            request_data = self.dhl_parcel_de_provider_get_package_info(
                picking, insurance_value
            )
            package_data.update(request_data)
            package_list.append(package_data)

        return package_list

    def dhl_parcel_de_provider_create_shipment(
        self, request_type, api_url, request_data, header
    ):
        _logger.debug("Shipment Request API URL:::: %s" % api_url)  # noqa:UP031
        _logger.debug("Shipment Request Data:::: %s" % request_data)  # noqa:UP031
        response_data = requests.request(
            method=request_type,
            url=api_url,
            headers=header,
            data=request_data,
            timeout=30,
        )
        if response_data.status_code in [200, 201, 207]:
            response_data = response_data.json()
            _logger.debug(f">>> Response Data {response_data}")
            return True, response_data
        else:
            return False, response_data.text

    def dhl_parcel_de_provider_send_shipping(self, picking):
        shipper_address_id = (
            picking.picking_type_id
            and picking.picking_type_id.warehouse_id
            and picking.picking_type_id.warehouse_id.partner_id
        )
        recipient_address_id = picking.partner_id
        shipper_address_error = self.check_address_details(
            shipper_address_id, ["zip", "city", "country_id", "street"]
        )
        recipient_address_error = self.check_address_details(
            recipient_address_id, ["zip", "city", "country_id", "street"]
        )
        if (
            shipper_address_error
            or recipient_address_error
            or not picking.shipping_weight
        ):
            # pylint: disable=C8107
            raise ValidationError(
                "%s %s  %s "  # noqa:UP031
                % (
                    "Shipper Address : %s \n" % (shipper_address_error)  # noqa:UP031
                    if shipper_address_error
                    else "",
                    "Recipient Address : %s \n" % (recipient_address_error)  # noqa:UP031
                    if recipient_address_error
                    else "",
                    "Shipping weight is missing!"
                    if not picking.shipping_weight
                    else "",
                )
            )
        if not self.carrier_account_id:
            raise ValidationError(
                _("Carrier account is not set for DHL delivery method.")
            )

        packages = self.dhl_parcel_de_provider_packages(picking)
        request_data = json.dumps({"shipments": packages})
        try:
            header = {
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.carrier_account_id.dhl_access_token}",
            }
            api_url = f"{self.carrier_account_id.dhl_parcel_de_api_url}/parcel/de/shipping/v2/orders?docFormat={self.dhl_document_format}"  # noqa: E501
            request_type = "POST"
            (
                response_status,
                response_data,
            ) = self.dhl_parcel_de_provider_create_shipment(
                request_type, api_url, request_data, header
            )
            final_tracking_number = []
            if (
                response_status
                and response_data.get("status")
                and response_data.get("status").get("statusCode") in [200, 207]
            ):
                for package_id in response_data.get("items"):
                    if package_id.get("sstatus").get("status") != 400:
                        tracking_number = package_id.get("shipmentNo")
                        label_data = (
                            package_id.get("label").get("b64")
                            if self.dhl_document_format == "PDF"
                            else package_id.get("label").get("zpl2")
                        )
                        if self.dhl_document_format == "PDF":
                            label_data = binascii.a2b_base64(label_data)
                        message = _(
                            "Label created!<br/> <b>Shipping  Number : </b>%s<br/>",
                            tracking_number,
                        )
                        picking.message_post(
                            body=message,
                            attachments=[
                                (
                                    "Shipping-Label-%s.%s"  # noqa:UP031
                                    % (
                                        tracking_number,
                                        self.dhl_document_format[:3].lower(),
                                    ),
                                    label_data,
                                )  # noqa:UP031
                            ],
                            body_is_html=True,
                        )
                        final_tracking_number.append(tracking_number)

                        if package_id.get("customsDoc") and package_id.get(
                            "customsDoc"
                        ).get("b64"):
                            doc_data = package_id.get("customsDoc").get("b64")
                            binary_data = binascii.a2b_base64(str(doc_data))
                            message = _("Document created!")
                            picking.message_post(
                                body=message,
                                attachments=[
                                    ("CustomsDoc-%s.pdf" % tracking_number, binary_data)  # noqa:UP031
                                ],
                            )
                    else:
                        # pylint: disable=C8107
                        raise ValidationError(response_data)
                shipping_data = {
                    "exact_price": 0.0,
                    "tracking_number": ",".join(final_tracking_number),
                }
                shipping_data = [shipping_data]
                return shipping_data
            else:
                raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e) from e

    def dhl_parcel_de_provider_cancel_shipment(self, picking):
        carrier_account_id = self.carrier_account_id
        try:
            api_url = f"{carrier_account_id.dhl_parcel_de_api_url}/parcel/de/shipping/v2/orders?profile=STANDARD_GRUPPENPROFIL"  # noqa: E501
            awb_numbers = picking.carrier_tracking_ref.split(",")
            for shipment in awb_numbers:
                api_url += f"&shipment={shipment}"
            request_data = {}
            header = {
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {carrier_account_id.dhl_access_token}",
            }
            request_type = "DELETE"
            (
                response_status,
                response_data,
            ) = self.dhl_parcel_de_provider_create_shipment(
                request_type, api_url, request_data, header
            )
            if response_status and response_data:
                _logger.debug(
                    "Cancel API : Parcel DE Response Data : %s", response_data
                )
            else:
                raise ValidationError(response_data.reason or response_data)
        except Exception as e:
            raise ValidationError(e) from e

    def dhl_parcel_de_provider_get_tracking_link(self, picking):
        if self.dhl_tracking_url:
            # Return link only for the latest tracking number
            tracking_no = picking.carrier_tracking_ref.split(",")[-1]
            return f"{self.dhl_tracking_url}{tracking_no}"
        else:
            raise ValidationError(
                _("Please set tracking URL in DHL delivery method settings.")
            )
