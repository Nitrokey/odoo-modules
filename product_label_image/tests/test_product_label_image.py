from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

REPORT_XML_ID = "product_label_image.report_product_label_image_4x6"
REPORT_NAME = "product_label_image.producttemplatelabel_image_4x6"


@tagged("post_install", "-at_install")
class TestProductLabelImage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env["product.template"].create(
            {"name": "Label Template", "barcode": "5901234123457"}
        )
        cls.product = cls.template.product_variant_id
        cls.Wizard = cls.env["product.label.layout"]

    def _wizard(self, **vals):
        vals.setdefault("print_format", "4x6")
        return self.Wizard.create(vals)

    # wizard

    def test_default_print_format(self):
        wizard = self.Wizard.create({"product_tmpl_ids": [(6, 0, self.template.ids)]})
        self.assertEqual(wizard.print_format, "4x6")

    def test_dimensions(self):
        wizard = self._wizard(product_tmpl_ids=[(6, 0, self.template.ids)])
        self.assertEqual(wizard.columns, 4)
        self.assertEqual(wizard.rows, 6)

    def test_prepare_report_data_template(self):
        wizard = self._wizard(
            product_tmpl_ids=[(6, 0, self.template.ids)], custom_quantity=3
        )
        xml_id, data = wizard._prepare_report_data()
        self.assertEqual(xml_id, REPORT_XML_ID)
        self.assertEqual(data["active_model"], "product.template")
        self.assertEqual(data["quantity_by_product"], {self.template.id: 3})
        self.assertEqual(data["layout_wizard"], wizard.id)
        self.assertFalse(data["price_included"])

    def test_prepare_report_data_product(self):
        wizard = self._wizard(product_ids=[(6, 0, self.product.ids)], custom_quantity=2)
        xml_id, data = wizard._prepare_report_data()
        self.assertEqual(xml_id, REPORT_XML_ID)
        self.assertEqual(data["active_model"], "product.product")
        self.assertEqual(data["quantity_by_product"], {self.product.id: 2})

    def test_prepare_report_data_invalid_quantity(self):
        wizard = self._wizard(
            product_tmpl_ids=[(6, 0, self.template.ids)], custom_quantity=0
        )
        with self.assertRaises(UserError):
            wizard._prepare_report_data()

    def test_prepare_report_data_no_products(self):
        wizard = self._wizard(custom_quantity=1)
        with self.assertRaises(UserError):
            wizard._prepare_report_data()

    def test_prepare_report_data_other_format_uses_super(self):
        wizard = self._wizard(
            print_format="dymo", product_tmpl_ids=[(6, 0, self.template.ids)]
        )
        xml_id, data = wizard._prepare_report_data()
        self.assertEqual(xml_id, "product.report_product_template_label_dymo")
        self.assertEqual(data["active_model"], "product.template")

    def test_process_returns_report_action(self):
        wizard = self._wizard(product_tmpl_ids=[(6, 0, self.template.ids)])
        action = wizard.process()
        self.assertEqual(action["type"], "ir.actions.report")
        self.assertEqual(action["report_name"], REPORT_NAME)
        self.assertEqual(action["data"]["layout_wizard"], wizard.id)

    # report model

    def _report_model(self):
        return self.env[f"report.{REPORT_NAME}"]

    def test_report_values_unknown_model(self):
        with self.assertRaises(UserError):
            self._report_model()._get_report_values([], {"active_model": "res.partner"})

    def test_report_values_no_wizard(self):
        data = {
            "active_model": "product.template",
            "quantity_by_product": {self.template.id: 1},
        }
        self.assertEqual(self._report_model()._get_report_values([], data), {})

    def test_report_values_template(self):
        wizard = self._wizard(product_tmpl_ids=[(6, 0, self.template.ids)])
        data = {
            "active_model": "product.template",
            "quantity_by_product": {self.template.id: 25},
            "layout_wizard": wizard.id,
            "price_included": False,
        }
        values = self._report_model()._get_report_values([], data)
        self.assertEqual(values["rows"], 6)
        self.assertEqual(values["columns"], 4)
        # 25 labels on a 4 x 6 = 24 grid need two pages
        self.assertEqual(values["page_numbers"], 2)
        self.assertEqual(
            list(values["quantity"].values()), [[(self.template.barcode, 25)]]
        )
        self.assertEqual(list(values["quantity"]), [self.template])

    def test_report_values_custom_barcodes(self):
        wizard = self._wizard(product_ids=[(6, 0, self.product.ids)])
        data = {
            "active_model": "product.product",
            "quantity_by_product": {self.product.id: 1},
            "custom_barcodes": {self.product.id: [("CUSTOM1", 2), ("CUSTOM2", 3)]},
            "layout_wizard": wizard.id,
        }
        values = self._report_model()._get_report_values([], data)
        self.assertEqual(values["page_numbers"], 1)
        barcodes = values["quantity"][self.product]
        self.assertEqual(
            barcodes,
            [(self.product.barcode, 1), ("CUSTOM1", 2), ("CUSTOM2", 3)],
        )

    def test_report_html_render(self):
        wizard = self._wizard(product_tmpl_ids=[(6, 0, self.template.ids)])
        _xml_id, data = wizard._prepare_report_data()
        html, report_type = self.env["ir.actions.report"]._render_qweb_html(
            REPORT_XML_ID, [], data=data
        )
        self.assertEqual(report_type, "html")
        self.assertIn(b"Label Template", html)
