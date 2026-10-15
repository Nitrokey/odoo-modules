from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestVariantsTemplate(TransactionCase):
    def test_view_is_valid_and_inherits_variants(self):
        view = self.env.ref(
            "website_product_attribute_description.product_variants_extended"
        )
        self.assertEqual(view.inherit_id, self.env.ref("website_sale.variants"))
        self.assertTrue(view.active)

    def test_combined_arch_contains_tooltips(self):
        """The inheriting xpaths are applied to the standard template"""
        view = self.env.ref("website_sale.variants")
        arch = self.env["ir.ui.view"]._read_template(view.id)
        # One tooltip per attribute display type (select, radio/multi, pills, color)
        self.assertGreaterEqual(arch.count('id="description_tooltip"'), 4)
        self.assertIn("ptal.attribute_id.description", arch)


@tagged("post_install", "-at_install")
class TestProductPage(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.descriptions = {}
        lines = []
        for display_type in ("select", "radio", "pills", "color", "multi"):
            description = f"Description of the {display_type} attribute"
            cls.descriptions[display_type] = description
            attribute = cls.env["product.attribute"].create(
                {
                    "name": f"Attr {display_type}",
                    "display_type": display_type,
                    "create_variant": "no_variant",
                    "description": description,
                    "value_ids": [
                        (0, 0, {"name": f"{display_type} A", "html_color": "#ff0000"}),
                        (0, 0, {"name": f"{display_type} B", "html_color": "#00ff00"}),
                    ],
                }
            )
            lines.append(
                (
                    0,
                    0,
                    {
                        "attribute_id": attribute.id,
                        "value_ids": [(6, 0, attribute.value_ids.ids)],
                    },
                )
            )
        no_description = cls.env["product.attribute"].create(
            {
                "name": "Attr without description",
                "display_type": "select",
                "create_variant": "no_variant",
                "value_ids": [
                    (0, 0, {"name": "plain A"}),
                    (0, 0, {"name": "plain B"}),
                ],
            }
        )
        cls.product = cls.env["product.template"].create(
            {
                "name": "Tooltip Test Product",
                "type": "consu",
                "list_price": 10.0,
                "is_published": True,
                "attribute_line_ids": lines,
            }
        )
        cls.product_plain = cls.env["product.template"].create(
            {
                "name": "Plain Test Product",
                "type": "consu",
                "list_price": 10.0,
                "is_published": True,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": no_description.id,
                            "value_ids": [(6, 0, no_description.value_ids.ids)],
                        },
                    )
                ],
            }
        )

    def test_product_page_shows_tooltips(self):
        response = self.url_open(self.product.website_url)
        self.assertEqual(response.status_code, 200)
        for description in self.descriptions.values():
            self.assertIn(description, response.text)
        self.assertGreaterEqual(response.text.count('id="description_tooltip"'), 5)

    def test_product_page_without_description(self):
        response = self.url_open(self.product_plain.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("plain A", response.text)
        self.assertNotIn("description_tooltip", response.text)
