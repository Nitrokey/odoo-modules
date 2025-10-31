import logging
from ast import literal_eval

from odoo import Command, fields, models

_logger = logging.getLogger(__name__)


class MergePartnerAutomatic(models.TransientModel):
    _inherit = "base.partner.merge.automatic.wizard"

    total_duplicates = fields.Integer()
    duplicate_position = fields.Integer("Duplicate Contact Position")
    associate_contact = fields.Boolean(
        string="Partner contacts associated to the contact", default=True
    )
    contact_not_being_customer = fields.Boolean(
        string="A contact not being customer", default=True
    )
    without_sales_orders = fields.Boolean(default=True)
    filter_domain_email = fields.Boolean(string="Domain Email")
    group_by_phone = fields.Boolean(string="Phone")
    group_by_mobile = fields.Boolean(string="Mobile")

    def _action_new_next_screen(self):
        """Open the next screen in the merge wizard."""
        self.env.registry.clear_cache()
        values, context = {}, {}

        if not self.line_ids:
            self.write(
                {"current_line_id": False, "partner_ids": [], "state": "finished"}
            )
            return

        current_line = self.line_ids[0]
        current_partner_ids = sorted(literal_eval(current_line.aggr_ids)[-2:])

        # Prefer the most recent partner based on latest sale order
        recent_order = self.env["sale.order"].search(
            [("partner_id", "in", current_partner_ids)],
            order="date_order desc, id desc",
            limit=1,
        )
        if recent_order:
            first_partner_id = [recent_order.partner_id.id]
            current_partner_ids = first_partner_id + list(
                set(current_partner_ids) - set(first_partner_id)
            )

        values.update(
            {
                "current_line_id": current_line.id,
                "partner_ids": [Command.set(current_partner_ids)],
                "dst_partner_id": current_partner_ids[0],
                "state": "selection",
            }
        )
        self.write(values)

        partner1, partner2 = self.env["res.partner"].browse(current_partner_ids)

        def _get_last_order(partner):
            order = self.env["sale.order"].search(
                [("partner_id", "=", partner.id)],
                order="date_order desc, id desc",
                limit=1,
            )
            return order.date_order if order else False, order.name if order else False

        sale_order_date1, sale_order_num1 = _get_last_order(partner1)
        sale_order_date2, sale_order_num2 = _get_last_order(partner2)

        context = {
            **{
                f"default_{k}": v
                for k, v in {
                    "last_changes_date1": partner1.write_date,
                    "last_changes_uid1": partner1.write_uid.id,
                    "last_changes_date2": partner2.write_date,
                    "last_changes_uid2": partner2.write_uid.id,
                    "last_order1": sale_order_date1,
                    "last_order2": sale_order_date2,
                    "last_order_num1": sale_order_num1,
                    "last_order_num2": sale_order_num2,
                    "partner_ids": values["partner_ids"],
                    "current_line_id": values["current_line_id"],
                    "dst_partner_id": values["dst_partner_id"],
                    "id1": partner1.id,
                    "id2": partner2.id,
                    "partner_id_1": partner1.id,
                    "partner_id_2": partner2.id,
                    "company_id": partner1.parent_id.id,
                    "company_id2": partner2.parent_id.id,
                    "company_name": partner1.company_name,
                    "company_name2": partner2.company_name,
                    "name": partner1.name,
                    "name2": partner2.name,
                    "email": partner1.email,
                    "email2": partner2.email,
                    "phone": partner1.phone,
                    "phone2": partner2.phone,
                    "mobile": partner1.mobile,
                    "mobile2": partner2.mobile,
                    "street": partner1.street,
                    "street2": partner2.street,
                    "street11": partner1.street2,
                    "street22": partner2.street2,
                    "zip": partner1.zip,
                    "zip2": partner2.zip,
                    "city": partner1.city,
                    "city2": partner2.city,
                    "state_id": partner1.state_id.id,
                    "state_id2": partner2.state_id.id,
                    "country_id": partner1.country_id.id,
                    "country_id2": partner2.country_id.id,
                    "vat_1": partner1.vat,
                    "vat_2": partner2.vat,
                    "is_company": partner1.is_company,
                    "is_company2": partner2.is_company,
                    "number_group": self.number_group,
                    "partner_wizard_id": self.id,
                    "state": "selection",
                    "total_duplicates": self.total_duplicates,
                    "duplicate_position": self.duplicate_position,
                    "contact_type": partner1.type,
                    "contact_type2": partner2.type,
                }.items()
            }
        }

        return {
            "type": "ir.actions.act_window",
            "name": "Merge Contacts",
            "res_model": "merge.partner.manual.check",
            "view_mode": "form",
            "target": "new",
            "context": context,
        }

    def _generate_query(self, fields, maximum_group=100):
        """Generate dynamic SQL query for duplicate detection."""
        final_query = "SELECT min(id), array_agg(id) FROM res_partner"
        sql_fields, where_queries = [], []

        for field in fields:
            if field in ["email", "name"]:
                sql_fields.append(f"lower({field})")
                where_queries.append(f"{field} IS NOT NULL AND TRIM({field}) != ''")
            elif field == "vat":
                sql_fields.append(f"replace({field}, ' ', '')")
                where_queries.append(
                    f"{field} IS NOT NULL AND TRIM(replace({field}, ' ', '')) != ''"
                )
            else:
                sql_fields.append(field)
                where_queries.append(f"{field} IS NOT NULL AND TRIM({field}) != ''")

        if self.associate_contact:
            where_queries.append("""
                parent_id IS NULL
                AND id NOT IN (
                    SELECT parent_id FROM res_partner WHERE parent_id IS NOT NULL
                )
            """)

        if self.contact_not_being_customer:
            where_queries.append("customer_rank > 0")

        if self.without_sales_orders:
            where_queries.append("""
                id IN (
                    SELECT partner_id FROM sale_order
                    UNION
                    SELECT partner_invoice_id FROM sale_order
                    UNION
                    SELECT partner_shipping_id FROM sale_order
                )
            """)

        if self.filter_domain_email:
            email_domains = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("merge_duplicate_contacts.email_domains", "")
                .split(",")
            )
            email_domains = list(filter(None, map(str.strip, email_domains)))
            if email_domains:
                clause = self.env.cr.mogrify(
                    "substring(email from '@(.*)$') not in %s", (tuple(email_domains),)
                ).decode()
                where_queries.append(clause)

        if where_queries:
            final_query += " WHERE " + " AND ".join(where_queries)
        if sql_fields:
            final_query += " GROUP BY " + ", ".join(sql_fields)
            final_query += " HAVING COUNT(*) > 1"

        return final_query

    def _process_query(self, query, ignore_occurence=True):
        """Execute the select query and write results in the wizard."""
        proxy = self.env["base.partner.merge.line"]
        models = self._compute_models()
        self._cr.execute(query)
        data = sorted(self._cr.fetchall(), key=lambda x: len(x[1]))

        counter, total_duplicates = 0, 0
        for min_id, aggr_ids in data:
            if models and self._partner_use_in(aggr_ids, models) and ignore_occurence:
                continue

            partners = self.env["res.partner"].search([("id", "in", aggr_ids)])
            if len(partners) < 2:
                continue

            ordered = self._get_ordered_partner(partners.ids)
            proxy.create(
                {
                    "wizard_id": self.id,
                    "min_id": min_id,
                    "aggr_ids": [p.id for p in ordered],
                }
            )
            counter += 1
            total_duplicates += len(ordered) - 1

        self.write(
            {
                "state": "selection",
                "number_group": counter,
                "total_duplicates": total_duplicates,
                "duplicate_position": 1,
            }
        )
        _logger.info("Processed %s groups of duplicates", counter)

    def action_start_manual_process(self):
        """Start the manual merge process."""
        self.ensure_one()
        context = dict(self._context.copy() or {}, active_test=False)
        query = self._generate_query(
            self._compute_selected_groupby(), self.maximum_group
        )
        self.with_context(context=context)._process_query(query)
        return self._action_new_next_screen()
