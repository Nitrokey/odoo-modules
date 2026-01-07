from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _update_reserved_quantity_vals(
        self,
        need,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=True,
    ):
        """Override to prevent automatic serial number assignment.

        For products tracked by serial number, we still reserve the quantity
        but do NOT assign a specific lot_id. This forces staff to manually
        enter the serial number when processing the operation.
        """
        # Get the move line vals from parent
        move_line_vals, taken_quantity = super()._update_reserved_quantity_vals(
            need,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )

        # For serial-tracked products, clear the lot_id from the move line vals
        if self.product_id.tracking == "serial":
            for vals in move_line_vals:
                vals["lot_id"] = False
                vals["lot_name"] = False

        return move_line_vals, taken_quantity
