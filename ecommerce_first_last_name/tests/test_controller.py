from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.website.tools import MockRequest

from ..controllers.main import WebsiteSaleFirstLastname


@tagged("post_install", "-at_install")
class TestFirstLastName(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WebsiteSaleFirstLastname()
        cls.website = cls.env["website"].search([], limit=1)
        cls.partner = cls.env["res.partner"].create(
            {"name": "John Doe", "last_name": "Doe"}
        )

    def _parse(self, form_data):
        with MockRequest(self.env, website=self.website):
            return self.controller._parse_form_data(form_data)

    def _validate(self, address_values, partner, can_edit_name=True):
        with (
            MockRequest(self.env, website=self.website),
            patch.object(
                type(self.env["res.partner"]),
                "_can_edit_name",
                lambda self: can_edit_name,
            ),
        ):
            return self.controller._validate_address_values(
                address_values,
                partner,
                "billing",
                False,
                "",
                True,
            )

    # _parse_form_data

    def test_parse_first_and_last_name(self):
        """First and last name are joined into the full partner name"""
        address_values, extra_form_data = self._parse(
            {"name": "Jane", "last_name": "Doe", "city": "Berlin"}
        )
        self.assertEqual(address_values["name"], "Jane Doe")
        self.assertEqual(address_values["last_name"], "Doe")
        self.assertEqual(address_values["company_type"], "person")
        self.assertEqual(address_values["city"], "Berlin")
        self.assertEqual(extra_form_data.get("first_name"), "Jane")

    def test_parse_strips_whitespace(self):
        """Surrounding whitespace is not part of the joined name"""
        address_values, extra_form_data = self._parse(
            {"name": "  Jane ", "last_name": " Doe  "}
        )
        self.assertEqual(address_values["name"], "Jane Doe")
        self.assertEqual(address_values["last_name"], "Doe")

    def test_parse_last_name_only(self):
        """Without a first name the last name becomes the full name"""
        address_values, extra_form_data = self._parse({"last_name": "Doe"})
        self.assertEqual(address_values["name"], "Doe")
        self.assertEqual(address_values["last_name"], "Doe")
        self.assertEqual(address_values["company_type"], "person")
        self.assertNotIn("first_name", extra_form_data)

    def test_parse_empty_first_name_with_last_name(self):
        """An empty first name behaves like a missing one"""
        address_values, extra_form_data = self._parse({"name": "", "last_name": "Doe"})
        self.assertEqual(address_values["name"], "Doe")
        self.assertNotIn("first_name", extra_form_data)

    def test_parse_without_last_name(self):
        """Without a last name the name is kept and no last_name is set"""
        address_values, extra_form_data = self._parse({"name": "Jane"})
        self.assertEqual(address_values["name"], "Jane")
        self.assertNotIn("last_name", address_values)
        self.assertNotIn("first_name", extra_form_data)
        self.assertEqual(address_values["company_type"], "person")

    def test_parse_forces_person_company_type(self):
        """The company type is always overwritten with person"""
        address_values, extra_form_data = self._parse(
            {"name": "Jane", "last_name": "Doe", "company_type": "company"}
        )
        self.assertEqual(address_values["company_type"], "person")

    # _validate_address_values

    def test_validate_no_partner(self):
        """New addresses are not restricted"""
        invalid, missing, messages = self._validate(
            {"name": "Jane Doe", "last_name": "Doe"},
            self.env["res.partner"],
            can_edit_name=False,
        )
        self.assertNotIn("name", invalid)
        self.assertNotIn("last_name", invalid)

    def test_validate_name_editable(self):
        """Changes are allowed if the partner name can be edited"""
        invalid, missing, messages = self._validate(
            {"name": "Jane Smith", "last_name": "Smith"}, self.partner
        )
        self.assertNotIn("name", invalid)
        self.assertNotIn("last_name", invalid)

    def test_validate_unchanged(self):
        """Unchanged names are valid even if they are locked"""
        invalid, missing, messages = self._validate(
            {"name": "John Doe", "last_name": "Doe"},
            self.partner,
            can_edit_name=False,
        )
        self.assertEqual(invalid, set())

    def test_validate_single_name_unchanged(self):
        """Partners without last name can be resubmitted unchanged"""
        partner = self.env["res.partner"].create({"name": "Madonna"})
        invalid, missing, messages = self._validate(
            {"name": "Madonna", "last_name": ""}, partner, can_edit_name=False
        )
        self.assertEqual(invalid, set())

    def test_validate_first_name_changed(self):
        """Only the first name is flagged if just the first name changed"""
        invalid, missing, messages = self._validate(
            {"name": "Jane Doe", "last_name": "Doe"},
            self.partner,
            can_edit_name=False,
        )
        self.assertEqual(invalid, {"name"})

    def test_validate_last_name_changed(self):
        """Only the last name is flagged if just the last name changed"""
        invalid, missing, messages = self._validate(
            {"name": "John Smith", "last_name": "Smith"},
            self.partner,
            can_edit_name=False,
        )
        self.assertEqual(invalid, {"last_name"})

    def test_validate_both_names_changed(self):
        """Both fields are flagged if first and last name changed"""
        invalid, missing, messages = self._validate(
            {"name": "Jane Smith", "last_name": "Smith"},
            self.partner,
            can_edit_name=False,
        )
        self.assertEqual(invalid, {"name", "last_name"})

    # res.partner

    def test_partner_last_name_field(self):
        """The partner has a last_name field"""
        self.assertEqual(self.partner.last_name, "Doe")
