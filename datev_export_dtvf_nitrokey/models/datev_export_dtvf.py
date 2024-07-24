# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class DatevExportDtvfExport(models.Model):
    _inherit = "datev_export_dtvf.export"

    def _get_data_transaction(self, move):
        """Try to export whatever looks like an SO number as "Belegfeld 1" """
        for data in super()._get_data_transaction(move):
            for line in move.line_ids:
                for field_name in ("ref", "name", "move_name"):
                    if (line[field_name] or "").startswith("SO") or (
                        line[field_name] or ""
                    ).startswith("EK"):
                        data["Belegfeld 1"] = line[field_name]
            yield data
