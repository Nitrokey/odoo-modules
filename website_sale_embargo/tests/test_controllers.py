from contextlib import contextmanager
from unittest.mock import Mock, patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.website.tools import MockRequest
from odoo.addons.website_sale.controllers.main import WebsiteSale as CoreWebsiteSale
from odoo.addons.website_sale_embargo.controllers.main import (
    WebsiteSale as EmbargoWebsiteSale,
)


@tagged("post_install", "-at_install")
class TestWebsiteSaleEmbargoControllers(TransactionCase):
    """Test the checkout controllers of website_sale_embargo"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("website.default_website")
        cls.country_us = cls.env.ref("base.us")
        cls.country_cn = cls.env.ref("base.cn")

        hs_code = cls.env["hs.code"].create(
            {
                "local_code": "9999999998",
                "description": "Embargoed product code",
                "country_id": [(6, 0, [cls.country_cn.id])],
            }
        )
        cls.product_embargoed = cls.env["product.product"].create(
            {
                "name": "Embargoed Controller Product",
                "type": "consu",
                "list_price": 100.0,
                "hs_code_id": hs_code.id,
            }
        )
        cls.product_free = cls.env["product.product"].create(
            {"name": "Free Controller Product", "type": "consu", "list_price": 10.0}
        )

    def _create_order(self, country, product=None):
        partner = self.env["res.partner"].create(
            {
                "name": f"Customer {country.code}",
                "email": f"customer.{country.code.lower()}@example.com",
                "country_id": country.id,
            }
        )
        return self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "partner_invoice_id": partner.id,
                "partner_shipping_id": partner.id,
                "website_id": self.website.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": (product or self.product_embargoed).id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

    @contextmanager
    def _mock_request(self, order):
        """Mock the HTTP request and the cart of the website to ``order``"""
        website_model = type(self.env["website"])
        with (
            patch.object(website_model, "sale_get_order", return_value=order),
            MockRequest(self.env, website=self.website) as request,
        ):
            request.render = Mock(return_value="<rendered>")
            yield request

    # /shop/confirm_order

    def test_confirm_order_embargoed_country(self):
        order = self._create_order(self.country_cn)
        with (
            self._mock_request(order),
            patch.object(CoreWebsiteSale, "shop_confirm_order") as parent,
            self.assertRaises(ValidationError) as cm,
        ):
            EmbargoWebsiteSale().shop_confirm_order()
        self.assertIn("Embargoed Controller Product", str(cm.exception))
        parent.assert_not_called()

    def test_confirm_order_allowed_country(self):
        order = self._create_order(self.country_us)
        with (
            self._mock_request(order),
            patch.object(
                CoreWebsiteSale, "shop_confirm_order", return_value="parent"
            ) as parent,
        ):
            result = EmbargoWebsiteSale().shop_confirm_order(foo="bar")
        # the route decorator wraps the plain return value in a response
        self.assertEqual(result.get_data(as_text=True), "parent")
        parent.assert_called_once_with(foo="bar")

    def test_confirm_order_allowed_product(self):
        order = self._create_order(self.country_cn, self.product_free)
        with (
            self._mock_request(order),
            patch.object(CoreWebsiteSale, "shop_confirm_order", return_value="parent"),
        ):
            result = EmbargoWebsiteSale().shop_confirm_order()
        # the route decorator wraps the plain return value in a response
        self.assertEqual(result.get_data(as_text=True), "parent")

    def test_confirm_order_without_order(self):
        with (
            self._mock_request(self.env["sale.order"]),
            patch.object(CoreWebsiteSale, "shop_confirm_order", return_value="parent"),
        ):
            result = EmbargoWebsiteSale().shop_confirm_order()
        # the route decorator wraps the plain return value in a response
        self.assertEqual(result.get_data(as_text=True), "parent")

    # /shop/address

    def test_address_empty_cart_redirects(self):
        order = self.env["sale.order"].create(
            {"partner_id": self.env.user.partner_id.id, "website_id": self.website.id}
        )
        with (
            self._mock_request(order),
            patch.object(CoreWebsiteSale, "shop_address") as parent,
        ):
            response = EmbargoWebsiteSale().shop_address(address_type="delivery")
        self.assertIn(response.status_code, (301, 302, 303))
        parent.assert_not_called()

    def test_address_delivery_embargoed_country_form_param(self):
        order = self._create_order(self.country_us)
        with (
            self._mock_request(order) as request,
            patch.object(CoreWebsiteSale, "shop_address") as parent,
        ):
            result = EmbargoWebsiteSale().shop_address(
                address_type="delivery", country_id=str(self.country_cn.id)
            )
        self.assertEqual(result.get_data(as_text=True), "<rendered>")
        parent.assert_not_called()
        template, values = request.render.call_args.args
        self.assertEqual(template, "website_sale.address")
        self.assertEqual(values["error"]["product_embargo"], "error")
        self.assertIn(
            "Embargoed Controller Product", values["error"]["error_message"][0]
        )
        self.assertEqual(values["address_type"], "delivery")

    def test_address_delivery_embargoed_country_from_order(self):
        order = self._create_order(self.country_cn)
        with (
            self._mock_request(order) as request,
            patch.object(CoreWebsiteSale, "shop_address") as parent,
        ):
            result = EmbargoWebsiteSale().shop_address(
                address_type="delivery", use_delivery_as_billing="true"
            )
        self.assertEqual(result.get_data(as_text=True), "<rendered>")
        parent.assert_not_called()
        values = request.render.call_args.args[1]
        self.assertTrue(values["use_delivery_as_billing"])
        self.assertIn("error_message", values["error"])

    def test_address_delivery_allowed_country(self):
        order = self._create_order(self.country_cn)
        with (
            self._mock_request(order),
            patch.object(
                CoreWebsiteSale, "shop_address", return_value="parent"
            ) as parent,
        ):
            result = EmbargoWebsiteSale().shop_address(
                address_type="delivery", country_id=str(self.country_us.id)
            )
        # the route decorator wraps the plain return value in a response
        self.assertEqual(result.get_data(as_text=True), "parent")
        parent.assert_called_once()
        self.assertEqual(parent.call_args.kwargs["address_type"], "delivery")
        self.assertEqual(parent.call_args.kwargs["country_id"], str(self.country_us.id))

    def test_address_billing_is_not_checked(self):
        order = self._create_order(self.country_cn)
        with (
            self._mock_request(order),
            patch.object(
                CoreWebsiteSale, "shop_address", return_value="parent"
            ) as parent,
        ):
            result = EmbargoWebsiteSale().shop_address(address_type="billing")
        # the route decorator wraps the plain return value in a response
        self.assertEqual(result.get_data(as_text=True), "parent")
        parent.assert_called_once()

    # Views

    def test_hs_code_views(self):
        for xmlid in (
            "website_sale_embargo.website_sale_embargo_hs_code_tree",
            "website_sale_embargo.website_sale_embargo_hs_code_form",
        ):
            view = self.env.ref(xmlid)
            arch = self.env["hs.code"].get_view(view.id, view.type)["arch"]
            self.assertIn("country_id", arch)
