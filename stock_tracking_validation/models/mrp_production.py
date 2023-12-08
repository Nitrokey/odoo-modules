from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def open_stock_tracking_wizard(self):
        production_line_has_lot = self.move_raw_ids.filtered(
            lambda m: m.move_line_ids.filtered(lambda lot: lot.lot_id)
        )
        if not production_line_has_lot:
            return self.button_mark_done()
        action = (
            self.env.ref("stock_tracking_validation.action_product_stock_validation")
            .sudo()
            .read()[0]
        )
        product_data = """<table class="table table-sm w-50 table-bordered
                            table-striped table-hover m-2">
                            <thead class="thead-light"">
                                <tr>
                                    <th>Product Name</th>
                                    <th>Lot/Serial</th>
                                </tr>
                            </thead>
                            <tbody>"""
        for production_line in self.move_raw_ids.filtered(lambda m: m.move_line_ids):
            if not production_line.move_line_ids.mapped("lot_id"):
                continue
            name = production_line.product_id.name
            lot_name = ""
            for lot_line in production_line.move_line_ids:
                if len(production_line.move_line_ids) == 1:
                    lot_name = lot_line.lot_id.name
                else:
                    if lot_line == production_line.move_line_ids[-1]:
                        lot_name += lot_line.lot_id.name
                    else:
                        lot_name += lot_line.lot_id.name + ", "
            product_data += """
                <tr>
                    <td class="border">%s</td>
                    <td>%s</td>
                </tr>
            """ % (
                name,
                lot_name,
            )
        product_data += """
                        </tbody>
                        </table>
                        """
        action["context"] = {"default_product_data": product_data}
        return action
