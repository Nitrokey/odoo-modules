from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"
    _mailing_enabled = True


class ResPartner(models.Model):
    _inherit = "res.partner"

    delivery_count = fields.Integer(
        string="Number of Deliveries", compute="_compute_picking_ids", store=True
    )
    sale_order_count = fields.Integer(
        compute="_compute_sale_order_count",
        string="Number of Sales Orders",
        search="_search_sale_order_count",
    )

    @api.depends("sale_order_ids")
    def _compute_picking_ids(self):
        for partner in self:
            count_picking = 0
            for delivery in partner.sale_order_ids:
                count_picking += len(delivery.picking_ids)
            partner.delivery_count += count_picking

    def _search_sale_order_count(self, operator, value):
        _query = """select partner_id as order from sale_order
group by partner_id having count(id) {} %s;""".format(
            operator
        )
        if not value:
            value = 0
            _query = """select partner_id as order from sale_order
group by partner_id having count(id) > %s;"""
        params = (value,)
        self.env.cr.execute(_query, params)
        partners = self.env.cr.fetchall()
        if partners:
            partners = [item[0] for item in partners]
            if not value and operator == "=":
                return [("id", "not in", partners)]
        return [("id", "in", partners)]
