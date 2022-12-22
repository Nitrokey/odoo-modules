from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super(StockPicking, self).action_done()
        for pickings in self:
            if pickings.picking_type_id.code == 'outgoing':
                if pickings.ups_image or pickings.label_de_attach_id:
                    pdf = self.env.ref('carrier_shipping_label_template.action_report_shipping_label').sudo().render_qweb_pdf(
                        [self.id])[0]
                pdf = self.env.ref('stock.action_report_picking').sudo().render_qweb_pdf(
                    [self.id])[0]
                pdf = self.env.ref('stock.action_report_delivery').sudo().render_qweb_pdf(
                    [self.id])[0]
        return res
