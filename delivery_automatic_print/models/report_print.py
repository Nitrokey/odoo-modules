from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()
        for pickings in self:
            if pickings.picking_type_id.code == "outgoing":
                if pickings.ups_image or pickings.label_de_attach_id:
                    self.env.ref(
                        "carrier_shipping_label_template.action_report_shipping_label"
                    ).sudo()._render_qweb_pdf([self.id])[0]

                self.env.ref("stock.action_report_picking").sudo()._render_qweb_pdf(
                    [self.id]
                )[0]
                self.env.ref("stock.action_report_delivery").sudo()._render_qweb_pdf(
                    [self.id]
                )[0]

        return res
