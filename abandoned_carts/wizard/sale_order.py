import logging
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import Warning as odoo_warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF
from odoo.tools.safe_eval import safe_eval

_LOGGER = logging.getLogger(__name__)


class SaleOrderWizard(models.TransientModel):
    _name = "sale.order.wizard"
    _description = "Abandoned Order Popup"

    sale_order_ids = fields.Many2many("sale.order", string="Sale Order")
    max_delete_limit = fields.Integer("Max Record delete limit")

    @api.model
    def default_get(self, fields):
        order_retention_period = safe_eval(
            self.env["ir.config_parameter"].get_param(
                "abandoned_carts.order_retention_period", "48"
            )
        )
        date = datetime.now() - timedelta(hours=order_retention_period)

        res = super().default_get(fields)
        system_user = self.sudo().env.ref("base.user_root", False)
        domain = [
            ("state", "in", ["draft", "sent"]),
            ("create_date", "<", date.strftime(DF)),
            ("website_id", "!=", False),
        ]
        if system_user:
            domain.append(("create_uid", "=", system_user.id))

        # sales_team = self.env.ref('sales_team.salesteam_website_sales', False)
        # if sales_team:
        #    domain.append(('team_id', '=', sales_team.id))

        max_delete_batch_limit = safe_eval(
            self.env["ir.config_parameter"].get_param(
                "abandoned_carts.max_delete_batch_limit", "2000"
            )
        )
        current_quotation = self.env["sale.order"].search(
            domain, limit=max_delete_batch_limit
        )
        res.update(
            {
                "sale_order_ids": [(6, 0, current_quotation.ids)],
                "max_delete_limit": max_delete_batch_limit,
            }
        )
        return res

    @api.model
    def _cron_remove_abandoned_cart_order(self):
        """This function removes sale order and customers"""
        # Remove sale order
        vals = self.default_get(["max_delete_limit", "sale_order_ids"])
        record = self.create(vals)
        record.action_remove_sale_order()

        # Remove Customers
        vals = self.env["customer.wizard"].default_get(
            ["max_delete_limit", "customer_ids"]
        )
        record = self.env["customer.wizard"].create(vals)
        record.action_remove_customer()
        return True

    def action_remove_sale_order(self):
        max_delete_batch_limit = safe_eval(
            self.env["ir.config_parameter"].get_param(
                "abandoned_carts.max_delete_batch_limit", "2000"
            )
        )

        ctx = self._context or {}
        selected_ids = ctx.get("deleting_ids", [])
        if selected_ids and ctx.get("manual_remove"):
            order_ids = selected_ids  # self.env['res.partner'].browse(selected_ids)
        else:
            order_ids = self.sale_order_ids.ids

        if len(order_ids) > max_delete_batch_limit:
            raise odoo_warning(
                _(
                    "For safety reasons, you cannot delete more than %d sale orders \
                together. You can re-open the wizard several times if needed."
                )
                % (max_delete_batch_limit)
            )

        # orders = self.sale_order_ids.mapped('order_id')
        user = self.env.user
        for order_id in order_ids:
            self.with_delay().create_order_remove_queue(order_id, user.id, user.name)

    def create_order_remove_queue(self, order_id, user_id, user_name):
        current_date = datetime.now()
        log_obj = self.env["removed.record.log"]

        order = self.env["sale.order"].browse(order_id)
        record_name = order.name
        record_id = order.id
        error = ""

        try:
            if order.state == "sent":
                order.action_cancel()
            order.unlink()
        except Exception as e:
            error = str(e)

        log_obj.create(
            {
                "name": record_name,
                "date": current_date,
                "res_model": "sale.order",
                "res_id": record_id,
                "user_id": user_id,
                "error": error,
            }
        )
        _LOGGER.info(
            "name %s, date %s, model %s, res_id %s, user %s"
            % (record_name, current_date, "sale.order", record_id, user_name)
        )

    def action_remove_sale_order_manual(self):
        ctx = self._context or {}
        deleting_ids = ctx.get("deleting_ids", [])
        if deleting_ids:
            self.with_context(manual_remove=True).action_remove_sale_order()
        return True
