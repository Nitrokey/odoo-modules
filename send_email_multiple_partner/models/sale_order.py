from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_sale_order_email_send(self):
        composer_form_view_id = self.env.ref(
            "mail.email_compose_message_wizard_form"
        ).id

        template_id = False
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "view_id": composer_form_view_id,
            "target": "new",
            "context": {
                "default_composition_mode": "mass_mail",
                "default_res_id": self.ids[0],
                "default_model": "sale.order",
                "default_use_template": bool(template_id),
                "default_template_id": template_id,
                "hide_no_auto_thread": True,
                "active_ids": self.ids,
            },
        }
