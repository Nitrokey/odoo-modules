from odoo import _, fields, models
from odoo.exceptions import UserError


class ProductLabelLayout(models.TransientModel):
    _inherit = "product.label.layout"

    print_format = fields.Selection(
        [
            ("4x6", "4x6"),
            ("dymo", "Dymo"),
            ("2x7xprice", "2 x 7 with price"),
            ("4x7xprice", "4 x 7 with price"),
            ("4x12", "4 x 12"),
            ("4x12xprice", "4 x 12 with price"),
        ],
        string="Format",
        default="4x6",
        required=True,
    )

    def _prepare_report_data(self):
        if self.custom_quantity <= 0:
            raise UserError(_("You need to set a positive quantity."))

        # Get layout grid
        if self.print_format != "4x6":
            return super(ProductLabelLayout, self)._prepare_report_data()

        xml_id = "product_label_image.report_product_label_image_4x6"

        active_model = ""
        if self.product_tmpl_ids:
            products = self.product_tmpl_ids.ids
            active_model = "product.template"
        elif self.product_ids:
            products = self.product_ids.ids
            active_model = "product.product"

        # Build data to pass to the report
        data = {
            "active_model": active_model,
            "quantity_by_product": {p: self.custom_quantity for p in products},
            "layout_wizard": self.id,
            "price_included": "xprice" in self.print_format,
        }
        return xml_id, data
