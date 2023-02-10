from odoo import _, fields, models
from odoo.exceptions import UserError


class ProductLabelLayout(models.TransientModel):
    _inherit = "product.label.layout"

    print_format = fields.Selection(
        selection_add=[("4x6", "4x6")],
        default="4x6",
        ondelete={"4x6": "set default"},
    )

    def _prepare_report_data(self):
        if self.custom_quantity <= 0:
            raise UserError(_("You need to set a positive quantity."))

        # Get layout grid
        if self.print_format != "4x6":
            return super()._prepare_report_data()

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
