import base64

from odoo.tests import HttpCase, TransactionCase, tagged

# 1x1 pixel PNG
PNG_1X1 = base64.b64encode(
    base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQ"
        "AAAABJRU5ErkJggg=="
    )
)


@tagged("post_install", "-at_install")
class TestProductIconTemplate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.template"].create(
            {"name": "Product with icons", "type": "consu"}
        )
        cls.icons = cls.env["product.icon"].create(
            [
                {
                    "name": f"Icon {number}",
                    "sequence": number,
                    "product_template_id": cls.product.id,
                    "image_1920": PNG_1X1,
                }
                for number in (1, 2)
            ]
        )

    def _render_icons(self, product):
        return str(
            self.env["ir.qweb"]._render(
                "website_sale_product_icon.product_icons", {"product": product}
            )
        )

    def test_view_inherits_product_page(self):
        view = self.env.ref("website_sale_product_icon.product")
        self.assertEqual(view.inherit_id, self.env.ref("website_sale.product"))
        self.assertTrue(view.active)

    def test_product_page_calls_icons_template(self):
        arch = self.env["ir.ui.view"]._read_template(
            self.env.ref("website_sale.product").id
        )
        self.assertIn("website_sale_product_icon.product_icons", arch)

    def test_render_icons(self):
        html = self._render_icons(self.product)
        self.assertIn("o_wspi_icons", html)
        self.assertEqual(html.count("o_wspi_icon_image"), 2)
        for icon in self.icons:
            self.assertIn(f"id={icon.id}", html)
            self.assertIn(icon.name, html)
        # Icons are sorted by sequence
        self.assertLess(html.index("Icon 1"), html.index("Icon 2"))

    def test_render_without_icons(self):
        product = self.env["product.template"].create(
            {"name": "Product without icons", "type": "consu"}
        )
        html = self._render_icons(product)
        self.assertNotIn("o_wspi_icons", html)


@tagged("post_install", "-at_install")
class TestProductIconPage(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.template"].create(
            {
                "name": "Icon Page Product",
                "type": "consu",
                "list_price": 10.0,
                "is_published": True,
            }
        )
        cls.icon = cls.env["product.icon"].create(
            {
                "name": "Certified Icon",
                "product_template_id": cls.product.id,
                "image_1920": PNG_1X1,
            }
        )
        cls.product_plain = cls.env["product.template"].create(
            {
                "name": "Icon Page Plain Product",
                "type": "consu",
                "list_price": 10.0,
                "is_published": True,
            }
        )

    def test_product_page_shows_icons(self):
        response = self.url_open(self.product.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("o_wspi_icon_image", response.text)
        self.assertIn("Certified Icon", response.text)

    def test_product_page_without_icons(self):
        response = self.url_open(self.product_plain.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("o_wspi_icons", response.text)

    def test_icon_image_is_served(self):
        response = self.url_open(f"/web/image/product.icon/{self.icon.id}/image_128")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content)
