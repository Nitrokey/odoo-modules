# © 2024 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    auto_picking_type_ids = fields.Many2many("stock.picking.type")

    def _render_qweb_pdf(self, res_ids=None, data=None):
        document, fmt = super()._render_qweb_pdf(res_ids, data)

        if self.is_shipping_label_report():
            # Implement the auto printing because super isn't called.
            # See base_report_to_printer/models/ir_actions_report.py
            behaviour = self.behaviour()
            printer = behaviour.pop("printer", None)
            can_print_report = self._can_print_report(behaviour, printer, document)

            if can_print_report:
                printer.print_document(
                    self, document, doc_format=self.report_type, **behaviour
                )

        return document, fmt
