import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def reports_to_print(self):
        reports = self.env["ir.actions.report"]
        for ref in [
            "carrier_shipping_label_template.action_report_shipping_label",
            "stock.action_report_picking",
            "stock.action_report_delivery",
        ]:
            report = self.env.ref(ref, False)
            if report and report.printing_printer_id:
                reports |= report
        return reports

    def button_validate(self):
        res = super().button_validate()
        if self.env.context.get("must_skip_send_to_printer"):
            return res

        ctx = {"raise_on_missing_labels": False}
        for report in self.reports_to_print().with_context(**ctx):
            if report.auto_picking_type_ids:
                pickings = self.filtered_domain(
                    [("picking_type_id", "in", report.auto_picking_type_ids.ids)]
                )
            else:
                pickings = self

            if pickings:
                report.sudo()._render_qweb_pdf(pickings.ids)

        return res
