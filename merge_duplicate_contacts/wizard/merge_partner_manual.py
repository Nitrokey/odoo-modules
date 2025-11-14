import itertools
import logging
from ast import literal_eval

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MergePartnerManualCheck(models.TransientModel):
    _name = "merge.partner.manual.check"
    _description = "Merge Partner Manual Check"

    contact_type = fields.Selection(
        [
            ("contact", "Contact"),
            ("invoice", "Invoice address"),
            ("delivery", "Shipping address"),
            ("other", "Other address"),
            ("private", "Private Address"),
        ],
        string="Address Type",
        help="Used by Sales and Purchase Apps to select "
        "the relevant address depending on the context.",
    )

    contact_type2 = fields.Selection(
        [
            ("contact", "Contact"),
            ("invoice", "Invoice address"),
            ("delivery", "Shipping address"),
            ("other", "Other address"),
            ("private", "Private Address"),
        ],
        string="Address Type 2",
        help="Used by Sales and Purchase Apps to select"
        " the relevant address depending on the context.",
    )

    last_changes_date1 = fields.Datetime("Last Changes")
    last_changes_date2 = fields.Datetime("Last Changes 2")

    last_changes_uid1 = fields.Many2one("res.users", "Last Update By")
    last_changes_uid2 = fields.Many2one("res.users", "Last Update By 2")

    last_order1 = fields.Datetime("Last Order")
    last_order2 = fields.Datetime("Last Order 2")

    last_order_num1 = fields.Char("Last Order Number")
    last_order_num2 = fields.Char("Last Order Number 2")

    id1 = fields.Char("ID 1")
    id2 = fields.Char("ID 2")

    partner_id_1 = fields.Many2one("res.partner", "Partner")
    partner_id_2 = fields.Many2one("res.partner", "Partner 2")

    company_id = fields.Many2one("res.partner", "Company")
    company_id2 = fields.Many2one("res.partner", "Company 2")

    company_name = fields.Char()
    company_name2 = fields.Char(string="Company Name 2")

    name = fields.Char()
    name2 = fields.Char("Name 2")

    email = fields.Char()
    email2 = fields.Char("Email 2")

    phone = fields.Char()
    phone2 = fields.Char("Phone 2")

    mobile = fields.Char()
    mobile2 = fields.Char("Mobile 2")

    street = fields.Char("Address1")
    street2 = fields.Char("Address1 2")

    street11 = fields.Char("Address2")
    street22 = fields.Char("Address2 2")

    zip = fields.Char()
    zip2 = fields.Char("ZIP 2")

    city = fields.Char()
    city2 = fields.Char("City 2")

    state_id = fields.Many2one("res.country.state", string="State")
    state_id2 = fields.Many2one("res.country.state", string="State 2")

    country_id = fields.Many2one("res.country", string="Country")
    country_id2 = fields.Many2one("res.country", string="Country 2")

    is_company = fields.Boolean("Is Company ?")
    is_company2 = fields.Boolean("Is Company 2 ?")

    vat_1 = fields.Char("VAT")
    vat_2 = fields.Char()

    keep1 = fields.Boolean("Keep", default=True)
    keep2 = fields.Boolean("Keep 2")
    keep_type = fields.Selection(
        [
            ("keep1", "Keep Left"),
            ("keep2", "Keep Right"),
        ],
        default="keep1",
    )

    partner_wizard_id = fields.Many2one("base.partner.merge.automatic.wizard", "Wizard")
    partner_ids = fields.Many2many(
        "res.partner",
        "partner_merge_manual_check_rel",
        "marge_id",
        "partner_id",
        string="Contacts",
    )

    current_line_id = fields.Many2one("base.partner.merge.line", string="Current Line")
    dst_partner_id = fields.Many2one("res.partner", string="Destination Contact")

    state = fields.Selection(
        [("option", "Option"), ("selection", "Selection"), ("finished", "Finished")],
        readonly=True,
        required=True,
        string="Status",
        default="option",
    )

    line_ids = fields.One2many("base.partner.merge.line", "wizard_id", string="Lines")
    number_group = fields.Integer("Group of Contacts", readonly=True)
    total_duplicates = fields.Integer()
    duplicate_position = fields.Integer("Duplicate Contact Position")

    name_show_icon = fields.Boolean(
        "Name Icon", compute="_compute_name_show_icon", store=True
    )
    company_show_icon = fields.Boolean(
        "Company Icon", compute="_compute_company_show_icon", store=True
    )
    company_name_show_icon = fields.Boolean(
        "Company Name Icon", compute="_compute_company_name_show_icon", store=True
    )
    email_show_icon = fields.Boolean(
        "Email Icon", compute="_compute_email_show_icon", store=True
    )
    phone_show_icon = fields.Boolean(
        "Phone Icon", compute="_compute_phone_show_icon", store=True
    )
    mobile_show_icon = fields.Boolean(
        "Mobile Icon", compute="_compute_mobile_show_icon", store=True
    )
    addr1_show_icon = fields.Boolean(
        "Address1 Icon", compute="_compute_addr1_show_icon", store=True
    )
    addr2_show_icon = fields.Boolean(
        "Address2 Icon", compute="_compute_addr2_show_icon", store=True
    )
    zip_show_icon = fields.Boolean(
        "Zip Icon", compute="_compute_zip_show_icon", store=True
    )
    city_show_icon = fields.Boolean(
        "City Icon", compute="_compute_city_show_icon", store=True
    )
    state_show_icon = fields.Boolean(
        "State Icon", compute="_compute_state_show_icon", store=True
    )
    country_show_icon = fields.Boolean(
        "Country Icon", compute="_compute_country_show_icon", store=True
    )
    vat_show_icon = fields.Boolean(
        "Vat Icon", compute="_compute_vat_show_icon", store=True
    )
    is_company_show_icon = fields.Boolean(
        "Is Company Icon", compute="_compute_is_company_show_icon", store=True
    )

    @api.depends("name", "name2")
    def _compute_name_show_icon(self):
        for record in self:
            record.name_show_icon = not record.name or record.name == record.name2

    @api.depends("company_id", "company_id2")
    def _compute_company_show_icon(self):
        for record in self:
            if (not record.company_id and not record.company_id2) or (
                record.company_id == record.company_id2
            ):
                record.company_show_icon = True
            else:
                record.company_show_icon = False

    @api.depends("company_name", "company_name2")
    def _compute_company_name_show_icon(self):
        for record in self:
            if (not record.company_name and not record.company_name2) or (
                record.company_name == record.company_name2
            ):
                record.company_name_show_icon = True
            else:
                record.company_name_show_icon = False

    @api.depends("email", "email2")
    def _compute_email_show_icon(self):
        for record in self:
            if (not record.email and not record.email2) or (
                record.email2
                and record.email
                and record.email.lower() == record.email2.lower()
            ):
                record.email_show_icon = True
            else:
                record.email_show_icon = False

    @api.depends("phone", "phone2")
    def _compute_phone_show_icon(self):
        for record in self:
            if (not record.phone and not record.phone2) or (
                record.phone == record.phone2
            ):
                record.phone_show_icon = True
            else:
                record.phone_show_icon = False

    @api.depends("mobile", "mobile2")
    def _compute_mobile_show_icon(self):
        for record in self:
            if (not record.mobile and not record.mobile2) or (
                record.mobile == record.mobile2
            ):
                record.mobile_show_icon = True
            else:
                record.mobile_show_icon = False

    @api.depends("street", "street2")
    def _compute_addr1_show_icon(self):
        for record in self:
            if (not record.street and not record.street2) or (
                record.street == record.street2
            ):
                record.addr1_show_icon = True
            else:
                record.addr1_show_icon = False

    @api.depends("street11", "street22")
    def _compute_addr2_show_icon(self):
        for record in self:
            if (not record.street11 and not record.street22) or (
                record.street11 == record.street22
            ):
                record.addr2_show_icon = True
            else:
                record.addr2_show_icon = False

    @api.depends("zip", "zip2")
    def _compute_zip_show_icon(self):
        for record in self:
            if (not record.zip and not record.zip2) or (record.zip == record.zip2):
                record.zip_show_icon = True
            else:
                record.zip_show_icon = False

    @api.depends("city", "city2")
    def _compute_city_show_icon(self):
        for record in self:
            if (not record.city and not record.city2) or (record.city == record.city2):
                record.city_show_icon = True
            else:
                record.city_show_icon = False

    @api.depends("state_id", "state_id2")
    def _compute_state_show_icon(self):
        for record in self:
            if (not record.state_id and not record.state_id2) or (
                record.state_id == record.state_id2
            ):
                record.state_show_icon = True
            else:
                record.state_show_icon = False

    @api.depends("country_id", "country_id2")
    def _compute_country_show_icon(self):
        for record in self:
            if (not record.country_id and not record.country_id2) or (
                record.country_id == record.country_id2
            ):
                record.country_show_icon = True
            else:
                record.country_show_icon = False

    @api.depends("vat_1", "vat_2")
    def _compute_vat_show_icon(self):
        for record in self:
            if (not record.vat_1 and not record.vat_2) or (
                record.vat_1 == record.vat_2
            ):
                record.vat_show_icon = True
            else:
                record.vat_show_icon = False

    @api.depends("is_company", "is_company2")
    def _compute_is_company_show_icon(self):
        for record in self:
            if (not record.is_company and not record.is_company2) or (
                record.is_company == record.is_company2
            ):
                record.is_company_show_icon = True
            else:
                record.is_company_show_icon = False

    @api.onchange("keep_type")
    def _onchange_keep_type(self):
        self.ensure_one()
        if self.keep_type == "keep1":
            self.keep1 = True
        elif self.keep_type == "keep2":
            self.keep2 = True

    @api.onchange("keep1")
    def _onchange_keep1(self):
        self.ensure_one()
        if self.keep1:
            self.keep2 = False
            self.dst_partner_id = self.partner_ids and self.partner_ids[0].id or False

    @api.onchange("keep2")
    def _onchange_keep2(self):
        self.ensure_one()
        if self.keep2:
            self.keep1 = False
            self.dst_partner_id = self.partner_ids and self.partner_ids[1].id or False

    def action_skip(self):
        """Skip the current duplicate partner pair and move to the next."""
        wizard_line = self.partner_wizard_id.current_line_id
        if wizard_line:
            skipped_ids = set(self.partner_ids.ids)
            current_aggr_ids = set(literal_eval(wizard_line.aggr_ids or "[]"))
            remaining_ids = list(current_aggr_ids - skipped_ids)

            if not remaining_ids or len(remaining_ids) == 1:
                wizard_line.unlink()
            else:
                wizard_line.write({"aggr_ids": remaining_ids})
        else:
            raise UserError(_("No duplicates found."))

        # Move to the next duplicate
        self.partner_wizard_id.write(
            {
                "duplicate_position": self.partner_wizard_id.duplicate_position + 1,
            }
        )
        return self.partner_wizard_id._action_new_next_screen()

    def _get_ordered_partner(self, partner_ids):
        partners = self.env["res.partner"].browse(list(partner_ids))
        ordered_partners = partners.sorted(
            lambda p: (not p.active, p.create_date), reverse=True
        )
        return ordered_partners

    # delete source partner, since they are merged
    def _log_merge_operation(self, src_partners, dst_partner):
        _logger.info(
            "(uid = %s) merged the partners %r with %s",
            self.env.uid,
            src_partners.ids,
            dst_partner.id,
        )

    def _update_foreign_keys(self, src_partners, dst_partner):
        res = self.env["base.partner.merge.automatic.wizard"]._update_foreign_keys(
            src_partners, dst_partner
        )
        return res

    def _update_reference_fields(self, src_partners, dst_partner, context=None):
        res = self.env["base.partner.merge.automatic.wizard"]._update_reference_fields(
            src_partners, dst_partner
        )
        return res

    @api.model
    def _update_values(self, src_partners, dst_partner):
        """Update destination partner with values from source partners,
        excluding certain form fields and computed fields."""
        _logger.debug(
            "_update_values for dst_partner: %s for src_partners: %r",
            dst_partner.id,
            src_partners.ids,
        )

        def write_serializer(item):
            """Convert recordsets to IDs for safe write operations."""
            return item.id if isinstance(item, models.BaseModel) else item

        # Fields to exclude from merging
        excluded_fields = {
            "name",
            "email",
            "phone",
            "street",
            "street2",
            "zip",
            "city",
            "state_id",
            "country_id",
            "is_company",
            "vat",
        }

        values = {}
        for field_name, field in dst_partner._fields.items():
            if (
                field.type not in ("many2many", "one2many")
                and not field.compute
                and field_name not in excluded_fields
            ):
                for record in itertools.chain(src_partners, [dst_partner]):
                    if record[field_name]:
                        values[field_name] = write_serializer(record[field_name])

        # Remove non-writable fields
        values.pop("id", None)
        parent_id = values.pop("parent_id", None)

        # Ensure company flag consistency
        if dst_partner.child_ids and "is_company" not in values:
            values["is_company"] = dst_partner.is_company

        # Apply updates
        dst_partner.write(values)

        # Handle parent_id carefully to avoid recursion errors
        if parent_id and parent_id != dst_partner.id:
            try:
                dst_partner.write({"parent_id": parent_id})
            except ValidationError:
                _logger.info(
                    "Skipped recursive hierarchy for parent_id %s of partner %s",
                    parent_id,
                    dst_partner.id,
                )

    def action_merge(self, context=None):
        """Merge two partners based on selection (keep1/keep2) with VAT bypass."""
        context = dict(context or {}, active_test=False)
        if not (self.keep1 or self.keep2):
            raise Warning(_("Please select a contact to keep."))

        def update_partner_data(dst, data, vat_value):
            """Helper to write partner data and bypass VAT validation."""
            dst.write(data)
            if vat_value:
                self._cr.execute(
                    "UPDATE res_partner SET vat = %s WHERE id = %s",
                    (vat_value, dst.id),
                )

        if self.keep1:
            self.dst_partner_id = self.partner_ids[:1].id
            if self.dst_partner_id:
                update_partner_data(
                    self.dst_partner_id,
                    {
                        "parent_id": self.company_id.id if self.company_id else False,
                        "company_name": self.company_name or False,
                        "name": self.name or False,
                        "email": self.email or False,
                        "phone": self.phone or False,
                        "mobile": self.mobile or False,
                        "street": self.street or False,
                        "street2": self.street11 or False,
                        "zip": self.zip or False,
                        "city": self.city or False,
                        "state_id": self.state_id.id if self.state_id else False,
                        "country_id": self.country_id.id if self.country_id else False,
                        "is_company": self.is_company2 or False,
                        "vat": self.vat_1 or False,
                    },
                    self.vat_1,
                )
        else:
            self.dst_partner_id = self.partner_ids[1:2].id
            if self.dst_partner_id:
                update_partner_data(
                    self.dst_partner_id,
                    {
                        "parent_id": self.company_id2.id if self.company_id2 else False,
                        "company_name": self.company_name2 or False,
                        "name": self.name2 or False,
                        "email": self.email2 or False,
                        "phone": self.phone2 or False,
                        "mobile": self.mobile2 or False,
                        "street": self.street2 or False,
                        "street2": self.street22 or False,
                        "zip": self.zip2 or False,
                        "city": self.city2 or False,
                        "state_id": self.state_id2.id if self.state_id2 else False,
                        "country_id": self.country_id2.id
                        if self.country_id2
                        else False,
                        "is_company": self.is_company2 or False,
                        "vat": self.vat_2 or False,
                    },
                    self.vat_2,
                )

        partner_ids = set(map(int, self.partner_ids))
        if not partner_ids:
            self.write({"state": "finished"})
            return {
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
            }

        self.env["base.partner.merge.automatic.wizard"]._merge(
            partner_ids, self.dst_partner_id
        )

        if self.partner_wizard_id.current_line_id:
            deleted_ids = list(partner_ids - {self.dst_partner_id.id})
            aggr_ids = literal_eval(self.partner_wizard_id.current_line_id.aggr_ids)
            new_aggr_ids = list(set(aggr_ids) - set(deleted_ids))

            if not new_aggr_ids or len(new_aggr_ids) == 1:
                self.partner_wizard_id.current_line_id.unlink()
            else:
                self.partner_wizard_id.current_line_id.write({"aggr_ids": new_aggr_ids})

        self.partner_wizard_id.write(
            {
                "duplicate_position": self.partner_wizard_id.duplicate_position + 1,
            }
        )

        return self.partner_wizard_id.with_context(**context)._action_new_next_screen()

    def _swap_field_values(self, direction):
        mapping = [
            ("company_id", "company_id2"),
            ("company_name", "company_name2"),
            ("name", "name2"),
            ("email", "email2"),
            ("phone", "phone2"),
            ("mobile", "mobile2"),
            ("street", "street2"),
            ("street11", "street22"),
            ("zip", "zip2"),
            ("city", "city2"),
            ("state_id", "state_id2"),
            ("country_id", "country_id2"),
            ("is_company", "is_company2"),
            ("vat_1", "vat_2"),
        ]
        ctx_field = self._context.get("field_name")
        for left, right in mapping:
            if ctx_field in (left, right):
                if direction == "left":
                    setattr(self, left, getattr(self, right))
                else:
                    setattr(self, right, getattr(self, left))
                break
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def swap_to_left(self):
        return self._swap_field_values("left")

    def swap_to_right(self):
        return self._swap_field_values("right")

    def dummy_button(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
