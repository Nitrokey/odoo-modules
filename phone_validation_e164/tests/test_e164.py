from odoo.tests.common import TransactionCase


class TestPhoneValidationE164(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env["res.country"].search([("code", "=", "DE")], limit=1)

    def test_format_number_to_e164_with_int(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "phone": 987654,  # Pass as int
                "country_id": self.country.id,
            }
        )
        # Should be formatted as string, not raise TypeError
        assert isinstance(partner.phone, str)
        # Should start with '+' if formatted to E164 (if valid)
        assert partner.phone.startswith("+") or partner.phone == "987654"

    def test_format_number_to_e164_with_str(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "phone": "+49 987654",
                "country_id": self.country.id,
            }
        )
        assert partner.phone.startswith("+49")

    def test_format_number_to_e164_with_invalid(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "phone": "notaphone",
                "country_id": self.country.id,
            }
        )
        # Should return the original string if formatting fails
        assert partner.phone == "notaphone"

    def test_onchange_phone(self):
        partner = self.env["res.partner"].new(
            {
                "phone": "+49 987654",
                "country_id": self.country.id,
            }
        )
        partner._onchange_phone_validation()
        assert partner.phone.startswith("+49")

    def test_onchange_mobile(self):
        partner = self.env["res.partner"].new(
            {
                "mobile": "+49 123456",
                "country_id": self.country.id,
            }
        )
        partner._onchange_mobile_validation()
        assert partner.mobile.startswith("+49")

    def test_write_phone(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "phone": "987654",
                "country_id": self.country.id,
            }
        )
        partner.write({"phone": "+49 987654"})
        assert partner.phone.startswith("+49")

    def test_write_mobile(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "mobile": "123456",
                "country_id": self.country.id,
            }
        )
        partner.write({"mobile": "+49 123456"})
        assert partner.mobile.startswith("+49")

    def test_create_without_country(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "phone": "+49 987654",
            }
        )
        assert partner.phone.startswith("+49")

    def test_format_number_to_e164_with_german_country(self):
        # Pass a local German number without +, should result in +49
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "phone": "987654321",
                "country_id": self.country.id,
            }
        )
        assert partner.phone.startswith("+49")
