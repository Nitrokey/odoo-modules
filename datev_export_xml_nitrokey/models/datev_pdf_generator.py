# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class DatevPdfGenerator(models.AbstractModel):
    _inherit = "datev.pdf.generator"

    @api.model
    def generate_pdf(self, invoice):
        return super(DatevPdfGenerator, self.with_context(must_skip_send_to_printer=True)).generate_pdf(invoice)
