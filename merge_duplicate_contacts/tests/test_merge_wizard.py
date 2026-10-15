from ast import literal_eval

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

WIZARD = "base.partner.merge.automatic.wizard"
MANUAL = "merge.partner.manual.check"


class MergeCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"].with_context(
            mail_create_nolog=True, mail_notrack=True
        )
        cls.partner_a = cls.Partner.create(
            {"name": "Alpha Merge Test", "email": "dup-merge@example.org"}
        )
        cls.partner_b = cls.Partner.create(
            {"name": "Beta Merge Test", "email": "dup-merge@example.org"}
        )

    def _open_manual_wizard(self, partners, **vals):
        """Open the merge screen like the "Merge" action on the partner list."""
        action = partners.open_wizard_action()
        self.assertEqual(action["res_model"], MANUAL)
        return self.env[MANUAL].with_context(**action["context"]).create(vals), action

    def _make_order(self, partner):
        return self.env["sale.order"].create({"partner_id": partner.id})


@tagged("post_install", "-at_install")
class TestResPartnerExtension(MergeCommon):
    def test_open_wizard_requires_two_records(self):
        with self.assertRaises(UserError):
            self.partner_a.open_wizard_action()
        with self.assertRaises(UserError):
            self.Partner.browse().open_wizard_action()

    def test_prepare_wizard_data(self):
        data = self.partner_a.prepare_wizard_data()
        self.assertEqual(data["state"], "option")
        self.assertTrue(data["group_by_name"])
        self.assertTrue(data["associate_contact"])
        self.assertTrue(data["contact_not_being_customer"])
        self.assertTrue(data["without_sales_orders"])
        self.assertFalse(data["exclude_contact"])
        self.assertEqual(data["line_ids"], [])
        # the data must be usable to create a wizard
        self.env[WIZARD].create(data)

    def test_open_wizard_action_context(self):
        pair = self.partner_a | self.partner_b
        action = pair.open_wizard_action()
        ctx = action["context"]
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["target"], "new")
        self.assertEqual(ctx["default_partner_id_1"], self.partner_a.id)
        self.assertEqual(ctx["default_partner_id_2"], self.partner_b.id)
        self.assertEqual(ctx["default_dst_partner_id"], self.partner_a.id)
        self.assertEqual(ctx["default_name"], "Alpha Merge Test")
        self.assertEqual(ctx["default_name2"], "Beta Merge Test")
        self.assertEqual(ctx["default_email"], "dup-merge@example.org")
        self.assertEqual(ctx["default_total_duplicates"], 1)
        self.assertEqual(ctx["default_duplicate_position"], 1)
        self.assertEqual(ctx["default_number_group"], 1)
        self.assertEqual(ctx["default_state"], "selection")
        self.assertFalse(ctx["default_last_order1"])
        self.assertFalse(ctx["default_last_order_num2"])

    def test_open_wizard_action_prefers_partner_with_latest_order(self):
        order = self._make_order(self.partner_b)
        action = (self.partner_a | self.partner_b).open_wizard_action()
        ctx = action["context"]
        self.assertEqual(ctx["default_partner_id_1"], self.partner_b.id)
        self.assertEqual(ctx["default_partner_id_2"], self.partner_a.id)
        self.assertEqual(ctx["default_dst_partner_id"], self.partner_b.id)
        self.assertEqual(ctx["default_last_order_num1"], order.name)
        self.assertEqual(ctx["default_last_order1"], order.date_order)
        self.assertFalse(ctx["default_last_order_num2"])

    def test_display_name_only_customer_id(self):
        partner = self.partner_a.with_context(only_show_customer_id=True)
        partner._compute_display_name()
        self.assertEqual(partner.display_name, str(self.partner_a.id))

    def test_display_name_default_behaviour(self):
        """Without the context key, or with address/e-mail hints, names are kept."""
        for ctx in (
            {},
            {"only_show_customer_id": True, "show_email": True},
            {"only_show_customer_id": True, "show_address": True},
        ):
            partner = self.partner_a.with_context(**ctx)
            partner._compute_display_name()
            self.assertIn("Alpha Merge Test", partner.display_name, ctx)


@tagged("post_install", "-at_install")
class TestGenerateQuery(MergeCommon):
    def _wizard(self, **vals):
        values = {
            "associate_contact": False,
            "contact_not_being_customer": False,
            "without_sales_orders": False,
        }
        values.update(vals)
        return self.env[WIZARD].create(values)

    def _groups(self, query):
        """Return the sets of partner ids found by the query."""
        # the query is plain SQL: write pending ORM changes first
        self.env.flush_all()
        self.env.cr.execute(query)
        return [set(ids) for _min, ids in self.env.cr.fetchall()]

    def test_query_without_fields_and_filters(self):
        self.assertEqual(
            self._wizard()._generate_query([]),
            "SELECT min(id), array_agg(id) FROM res_partner",
        )

    def test_query_field_expressions(self):
        query = self._wizard()._generate_query(["email", "vat", "phone"])
        self.assertIn(
            "GROUP BY lower(email), replace(vat, ' ', ''), phone HAVING COUNT(*) > 1",
            query,
        )
        self.assertIn("email IS NOT NULL AND TRIM(email) != ''", query)
        self.assertIn("TRIM(replace(vat, ' ', '')) != ''", query)
        self.assertIn("phone IS NOT NULL AND TRIM(phone) != ''", query)
        self.assertNotIn("customer_rank", query)
        self.assertNotIn("sale_order", query)
        self.assertNotIn("parent_id", query)

    def test_query_flags(self):
        wizard = self._wizard(
            associate_contact=True,
            contact_not_being_customer=True,
            without_sales_orders=True,
        )
        query = wizard._generate_query(["name"])
        self.assertIn("parent_id IS NULL", query)
        self.assertIn("customer_rank > 0", query)
        self.assertIn("SELECT partner_id FROM sale_order", query)
        self.assertIn("SELECT partner_invoice_id FROM sale_order", query)
        self.assertIn("SELECT partner_shipping_id FROM sale_order", query)
        # the query is valid SQL
        self.env.cr.execute(query)

    def test_query_email_domain_filter(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "merge_duplicate_contacts.email_domains", " example.com, test.org ,,"
        )
        query = self._wizard(filter_domain_email=True)._generate_query(["email"])
        self.assertIn(
            "substring(email from '@(.*)$') not in ('example.com', 'test.org')", query
        )
        self.env.cr.execute(query)

    def test_query_email_domain_filter_without_domains(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "merge_duplicate_contacts.email_domains", " , "
        )
        query = self._wizard(filter_domain_email=True)._generate_query(["email"])
        self.assertNotIn("substring", query)

    def test_query_finds_duplicates(self):
        groups = self._groups(self._wizard()._generate_query(["email"]))
        self.assertIn({self.partner_a.id, self.partner_b.id}, groups)

    def test_query_email_is_case_insensitive(self):
        self.partner_b.email = "DUP-Merge@Example.org"
        groups = self._groups(self._wizard()._generate_query(["email"]))
        self.assertIn({self.partner_a.id, self.partner_b.id}, groups)

    def test_query_vat_ignores_spaces(self):
        self.env.cr.execute(
            "UPDATE res_partner SET vat = %s WHERE id = %s",
            ("XX 1234 5678", self.partner_a.id),
        )
        self.env.cr.execute(
            "UPDATE res_partner SET vat = %s WHERE id = %s",
            ("XX12345678", self.partner_b.id),
        )
        groups = self._groups(self._wizard()._generate_query(["vat"]))
        self.assertIn({self.partner_a.id, self.partner_b.id}, groups)

    def test_query_customer_and_order_filters(self):
        third = self.Partner.create(
            {"name": "Gamma Merge Test", "email": "dup-merge@example.org"}
        )
        self.partner_a.customer_rank = 1
        self.partner_b.customer_rank = 1
        self._make_order(self.partner_a)
        self._make_order(self.partner_b)
        wizard = self._wizard(
            contact_not_being_customer=True, without_sales_orders=True
        )
        groups = self._groups(wizard._generate_query(["email"]))
        self.assertIn({self.partner_a.id, self.partner_b.id}, groups)
        self.assertFalse(any(third.id in group for group in groups))

    def test_query_associate_contact_excludes_parents_and_children(self):
        child = self.Partner.create(
            {
                "name": "Child Merge Test",
                "email": "dup-merge@example.org",
                "parent_id": self.partner_a.id,
            }
        )
        wizard = self._wizard(associate_contact=True)
        groups = self._groups(wizard._generate_query(["email"]))
        # child has a parent, partner_a is a parent: both are excluded
        for group in groups:
            self.assertNotIn(child.id, group)
            self.assertNotIn(self.partner_a.id, group)

    def test_query_email_domain_excludes_partners(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "merge_duplicate_contacts.email_domains", "example.org"
        )
        wizard = self._wizard(filter_domain_email=True)
        groups = self._groups(wizard._generate_query(["email"]))
        self.assertFalse(any(self.partner_a.id in group for group in groups))


@tagged("post_install", "-at_install")
class TestProcessQuery(MergeCommon):
    def _query_for(self, partners):
        return (
            "SELECT MIN(id), ARRAY_AGG(id) FROM res_partner "
            f"WHERE id IN {tuple(partners.ids + [0])}"
        )

    def test_process_query_creates_lines(self):
        wizard = self.env[WIZARD].create({})
        wizard._process_query(self._query_for(self.partner_a | self.partner_b))
        self.assertEqual(len(wizard.line_ids), 1)
        line = wizard.line_ids
        self.assertEqual(line.min_id, self.partner_a.id)
        self.assertCountEqual(
            literal_eval(line.aggr_ids), [self.partner_a.id, self.partner_b.id]
        )
        self.assertEqual(wizard.state, "selection")
        self.assertEqual(wizard.number_group, 1)
        self.assertEqual(wizard.total_duplicates, 1)
        self.assertEqual(wizard.duplicate_position, 1)

    def test_process_query_counts_all_duplicates_of_a_group(self):
        third = self.Partner.create({"name": "Gamma Merge Test"})
        wizard = self.env[WIZARD].create({})
        wizard._process_query(self._query_for(self.partner_a | self.partner_b | third))
        self.assertEqual(wizard.number_group, 1)
        self.assertEqual(wizard.total_duplicates, 2)

    def test_process_query_skips_single_partner_groups(self):
        wizard = self.env[WIZARD].create({})
        query = (
            "SELECT MIN(id), ARRAY_AGG(id) FROM res_partner "
            f"WHERE id = {self.partner_a.id}"
        )
        wizard._process_query(query)
        self.assertFalse(wizard.line_ids)
        self.assertEqual(wizard.number_group, 0)
        self.assertEqual(wizard.total_duplicates, 0)

    def test_process_query_excludes_user_partners(self):
        """With "exclude_contact", groups containing a user's partner are skipped."""
        user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create({"name": "Merge User", "login": "merge-user-test"})
        )
        query = self._query_for(self.partner_a | user.partner_id)
        excluded = self.env[WIZARD].create({"exclude_contact": True})
        excluded._process_query(query)
        self.assertFalse(excluded.line_ids)
        # ... unless occurrences are not to be ignored
        included = self.env[WIZARD].create({"exclude_contact": True})
        included._process_query(query, ignore_occurence=False)
        self.assertEqual(len(included.line_ids), 1)

    def test_line_count_grows_with_group_size(self):
        Line = self.env["base.partner.merge.line"]
        wizard = self.env[WIZARD].create({})
        small = Line.create({"wizard_id": wizard.id, "min_id": 1, "aggr_ids": "[1, 2]"})
        large = Line.create(
            {"wizard_id": wizard.id, "min_id": 1, "aggr_ids": "[1, 2, 3, 4]"}
        )
        self.assertEqual(small.aggr_ids_count, 2)
        self.assertEqual(large.aggr_ids_count, 4)
        # smaller groups are processed first
        self.assertEqual(wizard.line_ids.ids, [small.id, large.id])


@tagged("post_install", "-at_install")
class TestManualProcess(MergeCommon):
    def _automatic_wizard(self, **vals):
        values = {
            "group_by_email": True,
            "group_by_name": True,
            "associate_contact": False,
            "contact_not_being_customer": False,
            "without_sales_orders": False,
        }
        values.update(vals)
        return self.env[WIZARD].create(values)

    def test_start_manual_process_requires_filter(self):
        wizard = self.env[WIZARD].create({})
        with self.assertRaises(UserError):
            wizard.action_start_manual_process()

    def test_start_manual_process(self):
        self.partner_b.name = self.partner_a.name
        wizard = self._automatic_wizard()
        action = wizard.action_start_manual_process()
        self.assertEqual(action["res_model"], MANUAL)
        ids = {self.partner_a.id, self.partner_b.id}
        self.assertIn(
            ids, [set(literal_eval(line.aggr_ids)) for line in wizard.line_ids]
        )
        self.assertEqual(wizard.state, "selection")
        self.assertTrue(wizard.current_line_id)
        self.assertEqual(action["context"]["default_partner_wizard_id"], wizard.id)
        self.assertEqual(action["context"]["default_state"], "selection")

    def test_next_screen_without_lines(self):
        wizard = self.env[WIZARD].create({})
        # automatic wizard: warn the user
        with self.assertRaises(UserError):
            wizard.with_context(pass_warning=True)._action_new_next_screen()
        # no active record: warn as well
        with self.assertRaises(UserError):
            wizard._action_new_next_screen()
        # manual wizard (active record): finish silently
        result = wizard.with_context(active_id=wizard.id)._action_new_next_screen()
        self.assertIsNone(result)
        self.assertEqual(wizard.state, "finished")
        self.assertFalse(wizard.current_line_id)
        self.assertFalse(wizard.partner_ids)

    def test_next_screen_selects_first_line(self):
        wizard = self.env[WIZARD].create({})
        wizard._process_query(
            "SELECT MIN(id), ARRAY_AGG(id) FROM res_partner "
            f"WHERE id IN ({self.partner_a.id}, {self.partner_b.id})"
        )
        action = wizard._action_new_next_screen()
        self.assertEqual(wizard.current_line_id, wizard.line_ids)
        self.assertEqual(wizard.partner_ids, self.partner_a | self.partner_b)
        self.assertEqual(wizard.dst_partner_id, self.partner_a)
        ctx = action["context"]
        self.assertEqual(ctx["default_current_line_id"], wizard.line_ids.id)
        self.assertEqual(ctx["default_email2"], "dup-merge@example.org")


@tagged("post_install", "-at_install")
class TestManualCheckIcons(MergeCommon):
    def _icons(self, **vals):
        return self.env[MANUAL].create(vals)

    def test_text_icons(self):
        record = self._icons(
            name="A",
            name2="A",
            phone="1",
            phone2="2",
            mobile=False,
            mobile2=False,
            street="S",
            street2=False,
            street11="X",
            street22="X",
            zip="1",
            zip2="1",
            city="C",
            city2="D",
            vat_1="V",
            vat_2="V",
        )
        self.assertTrue(record.name_show_icon)
        self.assertFalse(record.phone_show_icon)
        self.assertTrue(record.mobile_show_icon)
        self.assertFalse(record.addr1_show_icon)
        self.assertTrue(record.addr2_show_icon)
        self.assertTrue(record.zip_show_icon)
        self.assertFalse(record.city_show_icon)
        self.assertTrue(record.vat_show_icon)

    def test_name_icon_when_left_name_empty(self):
        record = self._icons(name=False, name2="B")
        self.assertTrue(record.name_show_icon)
        record.name = "A"
        self.assertFalse(record.name_show_icon)

    def test_email_icon_is_case_insensitive(self):
        record = self._icons(email="Test@Example.com", email2="test@example.com")
        self.assertTrue(record.email_show_icon)
        record.email2 = "other@example.com"
        self.assertFalse(record.email_show_icon)
        record.email2 = False
        self.assertFalse(record.email_show_icon)
        record.email = False
        self.assertTrue(record.email_show_icon)

    def test_relational_and_boolean_icons(self):
        de, us = self.env.ref("base.de"), self.env.ref("base.us")
        record = self._icons(
            country_id=de.id,
            country_id2=us.id,
            company_id=self.partner_a.id,
            company_id2=self.partner_a.id,
            company_name="X",
            company_name2="Y",
            is_company=True,
            is_company2=False,
        )
        self.assertFalse(record.country_show_icon)
        self.assertTrue(record.company_show_icon)
        self.assertFalse(record.company_name_show_icon)
        self.assertFalse(record.is_company_show_icon)
        record.write({"country_id2": de.id, "is_company2": True})
        self.assertTrue(record.country_show_icon)
        self.assertTrue(record.is_company_show_icon)
        record.company_id2 = self.partner_b
        self.assertFalse(record.company_show_icon)

    def test_state_icon(self):
        state = self.env["res.country.state"].search([], limit=1)
        record = self._icons(state_id=state.id)
        self.assertFalse(record.state_show_icon)
        record.state_id2 = state
        self.assertTrue(record.state_show_icon)

    def test_onchange_keep_type(self):
        record = self._icons(keep1=False, keep2=False, keep_type="keep2")
        record._onchange_keep_type()
        self.assertTrue(record.keep2)
        record.keep_type = "keep1"
        record._onchange_keep_type()
        self.assertTrue(record.keep1)


@tagged("post_install", "-at_install")
class TestManualActions(MergeCommon):
    def test_action_skip_without_line(self):
        wizard = self.env[WIZARD].create({})
        manual = self.env[MANUAL].create({"partner_wizard_id": wizard.id})
        with self.assertRaises(UserError):
            manual.action_skip()

    def test_action_skip_last_pair_finishes(self):
        manual, _action = self._open_manual_wizard(self.partner_a | self.partner_b)
        wizard = manual.partner_wizard_id
        self.assertEqual(wizard.duplicate_position, 1)
        result = manual.with_context(active_id=wizard.id).action_skip()
        self.assertIsNone(result)
        self.assertFalse(wizard.line_ids)
        self.assertEqual(wizard.state, "finished")
        self.assertEqual(wizard.duplicate_position, 2)
        self.assertTrue(self.partner_a.exists() and self.partner_b.exists())

    def test_action_skip_keeps_remaining_partners(self):
        """Skipping a pair of a larger group keeps the others for the next screen."""
        third = self.Partner.create({"name": "Gamma Merge Test"})
        fourth = self.Partner.create({"name": "Delta Merge Test"})
        partners = self.partner_a | self.partner_b | third | fourth
        manual, _action = self._open_manual_wizard(partners)
        wizard = manual.partner_wizard_id
        shown = manual.partner_ids
        self.assertEqual(len(shown), 2)
        action = manual.with_context(active_id=wizard.id).action_skip()
        remaining = partners - shown
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertCountEqual(literal_eval(wizard.line_ids.aggr_ids), remaining.ids)
        self.assertEqual(action["res_model"], MANUAL)
        self.assertEqual(wizard.partner_ids, remaining)
        self.assertEqual(wizard.duplicate_position, 2)

    def test_action_merge_requires_selection(self):
        manual, _action = self._open_manual_wizard(
            self.partner_a | self.partner_b, keep1=False, keep2=False
        )
        with self.assertRaises(UserError):
            manual.action_merge()

    def test_action_merge_keep_first(self):
        child = self.Partner.create(
            {"name": "Child of Beta", "parent_id": self.partner_b.id}
        )
        manual, _action = self._open_manual_wizard(self.partner_a | self.partner_b)
        wizard = manual.partner_wizard_id
        manual.city = "Merge City"
        manual.with_context(active_id=wizard.id).action_merge()

        self.assertEqual(manual.dst_partner_id, self.partner_a)
        self.assertTrue(self.partner_a.exists())
        self.assertFalse(self.partner_b.exists())
        self.assertEqual(self.partner_a.city, "Merge City")
        self.assertEqual(self.partner_a.name, "Alpha Merge Test")
        # records of the merged partner now point to the destination
        self.env.invalidate_all()
        self.assertEqual(child.parent_id, self.partner_a)
        # the wizard moved on
        self.assertFalse(wizard.line_ids)
        self.assertEqual(wizard.state, "finished")
        self.assertEqual(wizard.duplicate_position, 2)

    def test_action_merge_keep_first_uses_first_is_company(self):
        manual, _action = self._open_manual_wizard(self.partner_a | self.partner_b)
        manual.write({"is_company": True, "is_company2": False})
        manual.with_context(active_id=manual.partner_wizard_id.id).action_merge()
        self.assertTrue(self.partner_a.is_company)

    def test_action_merge_keep_second(self):
        manual, _action = self._open_manual_wizard(
            self.partner_a | self.partner_b, keep1=False, keep2=True
        )
        manual._onchange_keep2()
        manual.name2 = "Beta Renamed"
        manual.with_context(active_id=manual.partner_wizard_id.id).action_merge()
        self.assertEqual(manual.dst_partner_id, self.partner_b)
        self.assertFalse(self.partner_a.exists())
        self.assertEqual(self.partner_b.name, "Beta Renamed")

    def test_swap_values(self):
        manual, _action = self._open_manual_wizard(self.partner_a | self.partner_b)
        manual.name2 = "Other"
        result = manual.with_context(field_name="name").swap_to_right()
        self.assertEqual(manual.name2, "Alpha Merge Test")
        manual.name2 = "Other"
        manual.with_context(field_name="name2").swap_to_left()
        self.assertEqual(manual.name, "Other")
        self.assertEqual(result["res_model"], MANUAL)
        self.assertEqual(result["res_id"], manual.id)
        # unknown fields are ignored
        before = manual.read(["name", "name2", "email"])
        manual.with_context(field_name="bogus").swap_to_left()
        self.assertEqual(manual.read(["name", "name2", "email"]), before)

    def test_dummy_button(self):
        manual, _action = self._open_manual_wizard(self.partner_a | self.partner_b)
        result = manual.dummy_button()
        self.assertEqual(result["res_id"], manual.id)
        self.assertEqual(result["target"], "new")
