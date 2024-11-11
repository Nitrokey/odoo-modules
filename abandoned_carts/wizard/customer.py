import logging
from datetime import datetime

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

_LOGGER = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Abandoned Customer Line Popup"""

    _inherit = "res.partner"

    def action_view_customer(self):
        try:
            form_id = (
                self.env["ir.model.data"]
                .sudo()
                .get_object_reference("base", "view_partner_form")[1]
            )
        except ValueError:
            form_id = False

        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "res.partner",
            "res_id": self.id,
            "views": [(form_id, "form")],
            "target": "new",
            "context": {
                "turn_view_readonly": True,
            },
        }


class CustomerWizard(models.TransientModel):
    """Abandoned Customer Popup"""

    _name = "customer.wizard"
    _description = "Abandoned Customer Popup"

    @api.model
    def set_fix_customer(self):
        user = self.env.ref("base.group_portal")
        user_internal = self.env.ref("base.group_user")

        system_users = self.env["res.users"].browse()
        for ref in ("base.user_root", "base.public_user"):
            rec = self.sudo().env.ref(ref, False)
            if rec:
                system_users |= rec

        if system_users:
            ids = ",".join(map(str, system_users.ids))
            system_user_filter = f"AND p.create_uid IN ({ids})"
        else:
            system_user_filter = ""

        qry = f"""
SELECT p.id
FROM res_partner p
LEFT JOIN res_users ru ON ru.partner_id=p.id
WHERE
    NOT EXISTS (
        SELECT 1 FROM crm_lead as lead WHERE lead.partner_id = p.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM calendar_event_res_partner_rel ce WHERE ce.res_partner_id = p.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM hr_employee emp WHERE emp.user_id = ru.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM helpdesk_ticket WHERE partner_id = p.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM mailing_contact where partner_id = p.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM crm_phonecall call WHERE call.partner_id=p.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM account_move inv WHERE inv.partner_id = p.id OR
        inv.partner_shipping_id = p.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM sale_order o
        WHERE o.partner_id = p.id OR o.partner_invoice_id=p.id OR o.partner_shipping_id=p.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM account_move_line line  WHERE line.partner_id = p.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM project_task task  WHERE task.partner_id = p.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM res_groups_users_rel
        WHERE gid = ( SELECT id FROM res_groups WHERE id=%s )
            AND uid=ru.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM res_groups_users_rel
        WHERE gid = (SELECT id FROM res_groups WHERE id=%s)
            AND uid=ru.id
    ) AND
    NOT EXISTS (
        SELECT 1 FROM payment_transaction pt WHERE pt.partner_id = p.id
    ) AND
    p.parent_id IS NULL AND
    p.is_company = False AND
    p.id NOT IN (
        SELECT partner_id FROM res_users
        UNION ALL
        SELECT partner_id FROM res_company ORDER BY partner_id
    )
    {system_user_filter}
ORDER BY p.id DESC"""  # noqa: E201,E202,E271,E272

        self._cr.execute(
            qry,
            (
                user.id,
                user_internal.id,
            ),
        )
        data = self._cr.fetchall()
        customer_ids = [p[0] for p in data]
        partner_obj = self.env["res.partner"].browse(customer_ids)
        return partner_obj

    customer_ids = fields.Many2many(
        "res.partner", string="Customers", default=set_fix_customer
    )
    max_delete_limit = fields.Integer("Max Record delete limit")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        max_delete_batch_limit = safe_eval(
            self.env["ir.config_parameter"].get_param(
                "abandoned_carts.max_delete_batch_limit", "50"
            )
        )

        res.update({"max_delete_limit": max_delete_batch_limit})
        return res

    def action_remove_customer(self):
        max_delete_batch_limit = safe_eval(
            self.env["ir.config_parameter"].get_param(
                "abandoned_carts.max_delete_batch_limit", "50"
            )
        )
        ctx = self._context or {}
        selected_ids = ctx.get("deleting_ids", [])
        if selected_ids and ctx.get("manual_remove"):
            customer_ids = selected_ids  # self.env['res.partner'].browse(selected_ids)
        else:
            customer_ids = self.customer_ids.ids

        user = self.env.user
        user_id = user.id

        batches = [
            customer_ids[i : i + max_delete_batch_limit]
            for i in range(0, len(customer_ids), max_delete_batch_limit)
        ]
        for batch in batches:
            self.with_delay().create_partner_remove_queue(batch, user_id, user.name)

    def create_partner_remove_queue(self, partner_ids, user_id, user_name):
        partner_obj = self.env["res.partner"]
        log_obj = self.env["removed.record.log"]
        current_date = datetime.now()

        for partner_id in partner_ids:
            partner = self.env["res.partner"].browse(partner_id)
            record_name = partner.name
            record_id = partner.id
            error = ""
            try:
                partner.unlink()
            except Exception as e:
                line = partner_obj.browse(partner_id)
                line.write({"active": False})
                error = str(e)

            log_obj.create(
                {
                    "name": record_name,
                    "date": datetime.now(),
                    "res_model": "res.partner",
                    "res_id": record_id,
                    "user_id": user_id,
                    "error": error,
                }
            )
            _LOGGER.info(
                "name %s, date %s, model %s, res_id %s, user %s"
                % (record_name, current_date, "res.partner", record_id, user_name)
            )

    def action_remove_customer_manual(self):
        ctx = self._context or {}
        deleting_ids = ctx.get("deleting_ids", [])
        if deleting_ids:
            self.with_context(manual_remove=True).action_remove_customer()
        return True
