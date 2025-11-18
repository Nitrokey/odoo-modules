from odoo import _, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _compute_display_name(self):
        """Custom display_name logic depending on context."""
        ctx = self._context or {}
        if ctx.get("only_show_customer_id") and not any(
            k in ctx
            for k in ["show_address", "show_address_only", "show_email", "html_format"]
        ):
            for record in self:
                record.display_name = f"{record.id}"  # : {record.name or ''}
        else:
            return super()._compute_display_name()

    def prepare_wizard_data(self):
        """Prepare default data for merge wizard."""
        return {
            "group_by_name": True,
            "state": "option",
            "number_group": 0,
            "current_line_id": False,
            "line_ids": [],
            "partner_ids": [],
            "exclude_contact": False,
            "maximum_group": 0,
            "total_duplicates": 0,
            "duplicate_position": 0,
            "associate_contact": True,
            "contact_not_being_customer": True,
            "without_sales_orders": True,
        }

    def open_wizard_action(self):
        """Open the partner merge wizard with selected partners."""
        if len(self.ids) < 2:
            raise UserError(
                _("At least two records are needed to perform this action.")
            )
        data = self.prepare_wizard_data()
        wizard = self.env["base.partner.merge.automatic.wizard"].create(data)
        wizard.with_context(**{})._process_query(
            f"SELECT MIN(id), ARRAY_AGG(id) FROM res_partner WHERE id IN\
            {tuple(self.ids)}",
            ignore_occurence=False,
        )
        return wizard._action_new_next_screen()
