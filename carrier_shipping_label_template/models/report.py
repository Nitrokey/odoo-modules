import base64
import io

from odoo import _, models
from odoo.exceptions import UserError


class IrActionsReportReportlab(models.Model):
    _inherit = "ir.actions.report"

    def is_shipping_label_report(self):
        return (
            self.xml_id
            == "carrier_shipping_label_template.action_report_shipping_label"
        )

    def _render_qweb_pdf(self, res_ids=None, data=None):
        if not self.is_shipping_label_report():
            return super()._render_qweb_pdf(res_ids, data)

        if self.model != "stock.picking":
            raise UserError(_("Shipping Label Report is not defined on pickings"))

        pickings = self.env["stock.picking"].browse(res_ids)
        labels = pickings.mapped("shipping_label_ids")
        if not labels and self.env.context.get("raise_on_missing_labels", True):
            raise UserError(_("No shipping labels to print for %s", pickings))

        streams = [io.BytesIO(base64.decodebytes(att.datas)) for att in labels]
        return self._merge_pdfs(streams), "pdf"

    def _retrieve_attachment(self, record):
        if self.is_shipping_label_report():
            return None

        return super()._retrieve_attachment(record)
