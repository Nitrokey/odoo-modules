import base64
import io
import zipfile

from lxml import etree

from odoo.addons.datev_export_xml.tests import test_datev_export


class TestDatevExportXmlNitrokey(test_datev_export.TestDatevExport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create demo data that tests rely on if not present
        cls._ensure_demo_data()

    @classmethod
    def _ensure_demo_data(cls):
        """Create all necessary demo data for tests to work with empty DB."""
        # Check if demo data already exists, if not create it
        
        # Create countries if they don't exist
        if not cls.env.ref("base.de", raise_if_not_found=False):
            cls.env["res.country"].create({
                "name": "Germany",
                "code": "DE",
            })
        
        # Create customers if they don't exist
        if not hasattr(cls, 'customer_de') or not cls.customer_de:
            cls.customer_de = cls.PartnerObj.create({
                "name": "Customer DE Test",
                "street": "Test Street 123",
                "city": "Berlin",
                "zip": "10115",
                "country_id": cls.env.ref("base.de").id,
                "is_company": True,
            })
        
        if not hasattr(cls, 'customer_eu') or not cls.customer_eu:
            # Get or create France
            country_fr = cls.env.ref("base.fr", raise_if_not_found=False)
            if not country_fr:
                country_fr = cls.env["res.country"].create({
                    "name": "France",
                    "code": "FR",
                })
            cls.customer_eu = cls.PartnerObj.create({
                "name": "Customer EU Test",
                "street": "Rue de Test 456",
                "city": "Paris",
                "zip": "75001",
                "country_id": country_fr.id,
                "is_company": True,
            })
        
        if not hasattr(cls, 'customer_noneu') or not cls.customer_noneu:
            # Get or create USA
            country_us = cls.env.ref("base.us", raise_if_not_found=False)
            if not country_us:
                country_us = cls.env["res.country"].create({
                    "name": "United States",
                    "code": "US",
                })
            cls.customer_noneu = cls.PartnerObj.create({
                "name": "Customer NonEU Test",
                "street": "Test Avenue 789",
                "city": "New York",
                "zip": "10001",
                "country_id": country_us.id,
                "is_company": True,
            })
        
        # Create vendors if they don't exist
        if not hasattr(cls, 'vendor_de') or not cls.vendor_de:
            cls.vendor_de = cls.PartnerObj.create({
                "name": "Vendor DE Test",
                "street": "Vendor Street 321",
                "city": "Munich",
                "zip": "80331",
                "country_id": cls.env.ref("base.de").id,
                "is_company": True,
                "supplier_rank": 1,
            })
        
        if not hasattr(cls, 'vendor_eu') or not cls.vendor_eu:
            country_fr = cls.env.ref("base.fr", raise_if_not_found=False)
            if not country_fr:
                country_fr = cls.env["res.country"].create({
                    "name": "France",
                    "code": "FR",
                })
            cls.vendor_eu = cls.PartnerObj.create({
                "name": "Vendor EU Test",
                "street": "Rue Vendor 654",
                "city": "Lyon",
                "zip": "69001",
                "country_id": country_fr.id,
                "is_company": True,
                "supplier_rank": 1,
            })
        
        if not hasattr(cls, 'vendor_noneu') or not cls.vendor_noneu:
            country_us = cls.env.ref("base.us", raise_if_not_found=False)
            if not country_us:
                country_us = cls.env["res.country"].create({
                    "name": "United States",
                    "code": "US",
                })
            cls.vendor_noneu = cls.PartnerObj.create({
                "name": "Vendor NonEU Test",
                "street": "Vendor Street 987",
                "city": "Los Angeles",
                "zip": "90001",
                "country_id": country_us.id,
                "is_company": True,
                "supplier_rank": 1,
            })
        
        # Create accounts if they don't exist
        if not hasattr(cls, 'account_income') or not cls.account_income:
            cls.account_income = cls.AccountObj.create({
                "name": "Test Income Account",
                "code": "10000",
                "account_type": "income",
            })
        
        if not hasattr(cls, 'account_expense') or not cls.account_expense:
            cls.account_expense = cls.AccountObj.create({
                "name": "Test Expense Account",
                "code": "50000",
                "account_type": "expense",
            })
        
        # Create products if they don't exist
        if not hasattr(cls, 'consulting') or not cls.consulting:
            cls.consulting = cls.ProductObj.create({
                "name": "Consulting Service",
                "default_code": "CONSULT-01",
                "type": "service",
                "list_price": 120.00,
            })
        
        if not hasattr(cls, 'lease') or not cls.lease:
            cls.lease = cls.ProductObj.create({
                "name": "Lease Service",
                "default_code": "LEASE-01",
                "type": "service",
                "list_price": 900.00,
            })
        
        # Create analytic accounts if they don't exist
        if not hasattr(cls, 'analytic_account_it') or not cls.analytic_account_it:
            # Get or create analytic plan
            analytic_plan = cls.env["account.analytic.plan"].search([], limit=1)
            if not analytic_plan:
                analytic_plan = cls.env["account.analytic.plan"].create({
                    "name": "Test Plan",
                })
            
            cls.analytic_account_it = cls.AnalyticAccountObj.create({
                "name": "IT Department",
                "plan_id": analytic_plan.id,
            })
        
        if not hasattr(cls, 'analytic_account_office') or not cls.analytic_account_office:
            analytic_plan = cls.env["account.analytic.plan"].search([], limit=1)
            if not analytic_plan:
                analytic_plan = cls.env["account.analytic.plan"].create({
                    "name": "Test Plan",
                })
            
            cls.analytic_account_office = cls.AnalyticAccountObj.create({
                "name": "Office Department",
                "plan_id": analytic_plan.id,
            })
        
        # Create parent/child customers if needed
        if not hasattr(cls, 'parent_customer') or not cls.parent_customer:
            cls.parent_customer = cls.PartnerObj.create({
                "name": "Parent Customer Test",
                "street": "Parent Street 111",
                "city": "Hamburg",
                "zip": "20095",
                "country_id": cls.env.ref("base.de").id,
                "is_company": True,
            })
        
        if not hasattr(cls, 'child_customer') or not cls.child_customer:
            cls.child_customer = cls.PartnerObj.create({
                "name": "Child Customer Test",
                "parent_id": cls.parent_customer.id,
                "street": "Child Street 222",
                "city": "Hamburg",
                "zip": "20095",
                "country_id": cls.env.ref("base.de").id,
                "is_company": False,
            })
        
        # Create dummy attachments for vendor invoices if they don't exist
        if not hasattr(cls, 'inv_attach_de') or not cls.inv_attach_de:
            cls.inv_attach_de = cls.AttachmentObj.create({
                "name": "invoice_de.pdf",
                "datas": base64.b64encode(b"Test PDF content"),
                "mimetype": "application/pdf",
            })
        
        if not hasattr(cls, 'inv_attach_eu') or not cls.inv_attach_eu:
            cls.inv_attach_eu = cls.AttachmentObj.create({
                "name": "invoice_eu.pdf",
                "datas": base64.b64encode(b"Test PDF content"),
                "mimetype": "application/pdf",
            })
        
        if not hasattr(cls, 'inv_attach_noneu') or not cls.inv_attach_noneu:
            cls.inv_attach_noneu = cls.AttachmentObj.create({
                "name": "invoice_noneu.pdf",
                "datas": base64.b64encode(b"Test PDF content"),
                "mimetype": "application/pdf",
            })
        
        if not hasattr(cls, 'refund_attach_de') or not cls.refund_attach_de:
            cls.refund_attach_de = cls.AttachmentObj.create({
                "name": "refund_de.pdf",
                "datas": base64.b64encode(b"Test PDF content"),
                "mimetype": "application/pdf",
            })
        
        if not hasattr(cls, 'refund_attach_eu') or not cls.refund_attach_eu:
            cls.refund_attach_eu = cls.AttachmentObj.create({
                "name": "refund_eu.pdf",
                "datas": base64.b64encode(b"Test PDF content"),
                "mimetype": "application/pdf",
            })
        
        if not hasattr(cls, 'refund_attach_noneu') or not cls.refund_attach_noneu:
            cls.refund_attach_noneu = cls.AttachmentObj.create({
                "name": "refund_noneu.pdf",
                "datas": base64.b64encode(b"Test PDF content"),
                "mimetype": "application/pdf",
            })

    def test_01_out_invoice_de_datev_export(self):
        return super().test_01_out_invoice_de_datev_export()

    def test_02_out_invoice_eu_datev_export(self):
        return super().test_02_out_invoice_eu_datev_export()

    def test_04_out_refund_de_datev_export(self):
        return super().test_04_out_refund_de_datev_export()

    def test_partner_special_characters_validation(self):
        """
        Test that partners with special characters are properly validated and rejected.
        """
        # Create a partner with invalid control characters
        invalid_partner = self.PartnerObj.create(
            {
                "name": "Test Customer\x01",  # Contains U+0001 (control character)
                "street": "Main Street\x02",  # Contains U+0002 (control character)
                "city": "Test City",
                "zip": "12345",
                "is_company": True,
            }
        )

        # Create an invoice with this partner
        tax = self.env["account.tax"].create(
            {
                "name": "Tax 19%",
                "amount": 19.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )

        invoice = self.InvoiceObj.create(
            {
                "partner_id": invalid_partner.id,
                "user_id": self.env.user.id,
                "invoice_date": self.start_date,
                "invoice_date_due": self.end_date,
                "company_id": self.env.company.id,
                "currency_id": self.env.company.currency_id.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.consulting.id,
                            "quantity": 1.0,
                            "price_unit": 100.00,
                            "tax_ids": [(6, 0, tax.ids)],
                            "account_id": self.account_income.id,
                            "analytic_distribution": {self.analytic_account_it.id: 100},
                        },
                    ),
                ],
            }
        )
        # Don't post the invoice as it will fail due to special characters in XML
        # generation
        # Instead, test the validation directly on the draft invoice

        # Create export and validate
        datev_export = self.DatevExportObj.create(
            {
                "export_type": "out",
                "export_invoice": True,
                "export_refund": True,
                "check_xsd": True,
                "date_start": self.start_date,
                "date_stop": self.end_date,
                "manually_document_selection": True,
                "invoice_ids": [(6, 0, [invoice.id])],
            }
        )

        # Validation should detect the invalid characters
        datev_export.action_validate()

        # Check that the invoice is marked as problematic
        self.assertTrue(
            invoice.datev_validation,
            "Invoice should have validation error due to special characters",
        )
        self.assertIn(
            "U+0001",
            invoice.datev_validation,
            "Validation error should mention the specific invalid character U+0001",
        )

        invalid_partner.name = "Test Customer"
        datev_export.action_validate()
        self.assertIn(
            "U+0002",
            invoice.datev_validation,
            "Validation error should mention the specific invalid character U+0002",
        )
        self.assertIn(
            "invalid characters",
            invoice.datev_validation.lower(),
            "Validation error should mention invalid characters",
        )

        # Check that problematic invoices count is updated
        self.assertEqual(
            datev_export.problematic_invoices_count,
            1,
            "Should have 1 problematic invoice",
        )

    def test_partner_valid_characters_pass_validation(self):
        """Test that partners with only valid characters pass validation."""
        # Create a partner with only valid characters
        valid_partner = self.PartnerObj.create(
            {
                "name": "Test Customer Valid",
                "street": "Main Street 123",
                "city": "Test City",
                "zip": "12345",
                "country_id": self.env.ref(
                    "base.de"
                ).id,  # Add country for DATEV XSD validation
                "is_company": True,
            }
        )

        # Create an invoice with this partner
        tax = self.env["account.tax"].create(
            {
                "name": "Tax 19%",
                "amount": 19.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )

        # Create an account with code >= 10000 to satisfy DATEV XSD validation
        valid_account = self.env["account.account"].create(
            {
                "name": "Test Income Account",
                "code": "10000",
                "account_type": "income",
            }
        )

        invoice = self.InvoiceObj.create(
            {
                "partner_id": valid_partner.id,
                "user_id": self.env.user.id,
                "invoice_date": self.start_date,
                "invoice_date_due": self.end_date,
                "company_id": self.env.company.id,
                "currency_id": self.env.company.currency_id.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.consulting.id,
                            "quantity": 1.0,
                            "price_unit": 100.00,
                            "tax_ids": [(6, 0, tax.ids)],
                            "account_id": valid_account.id,
                            "analytic_distribution": {self.analytic_account_it.id: 100},
                        },
                    ),
                ],
            }
        )
        invoice.action_post()

        # Create export and validate
        datev_export = self.create_customer_datev_export_manually(invoice)

        # Validation should pass without errors
        datev_export.action_validate()

        # Check that the invoice has no validation errors
        self.assertFalse(
            invoice.datev_validation,
            "Invoice should not have validation errors with valid characters",
        )

        # Check that problematic invoices count is 0
        self.assertEqual(
            datev_export.problematic_invoices_count,
            0,
            "Should have 0 problematic invoices",
        )

    def test_skip_zero_amount_lines(self):
        """Test that invoice lines with zero amount (e.g., 100% discount)
        are skipped in export."""
        # Create tax for testing
        tax = self.env["account.tax"].create(
            {
                "name": "Tax 19%",
                "amount": 19.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )
        # Create invoice with mixed lines: normal line and zero amount line
        # (100% discount)
        invoice = self.InvoiceObj.create(
            {
                "partner_id": self.customer_de.id,
                "user_id": self.env.user.id,
                "invoice_date": self.start_date,
                "invoice_date_due": self.end_date,
                "company_id": self.env.company.id,
                "currency_id": self.env.company.currency_id.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    # Normal line with amount
                    (
                        0,
                        0,
                        {
                            "product_id": self.consulting.id,
                            "quantity": 1.0,
                            "price_unit": 100.00,
                            "discount": 0.0,  # No discount
                            "tax_ids": [(6, 0, tax.ids)],
                            "account_id": self.account_income.id,
                            "analytic_distribution": {self.analytic_account_it.id: 100},
                        },
                    ),
                    # Zero amount line with 100% discount
                    (
                        0,
                        0,
                        {
                            "product_id": self.lease.id,
                            "quantity": 1.0,
                            "price_unit": 50.00,
                            "discount": 100.0,  # 100% discount = zero amount
                            "tax_ids": [(6, 0, tax.ids)],
                            "account_id": self.account_income.id,
                            "analytic_distribution": {self.analytic_account_it.id: 100},
                        },
                    ),
                ],
            }
        )
        invoice.action_post()
        # Verify the invoice has 2 lines but only 1 should have non-zero amount
        self.assertEqual(len(invoice.invoice_line_ids.filtered("product_id")), 2)
        # Check that one line has zero amount due to 100% discount
        zero_line = invoice.invoice_line_ids.filtered(lambda x: x.discount == 100.0)
        self.assertEqual(len(zero_line), 1)
        price_info = zero_line.datev_price_information()
        self.assertEqual(price_info["total_excluded"], 0.0)
        # Create export
        datev_export = self.create_customer_datev_export_manually(invoice)
        datev_export.action_pending()
        datev_export.with_user(datev_export.create_uid.id).get_zip()
        # Parse the invoice XML directly from the ZIP file to count invoice_item_list
        # elements
        if not datev_export.line_ids.attachment_id:
            self.fail("No attachment found in export")
        zip_data = base64.b64decode(datev_export.line_ids.attachment_id.datas)
        fp = io.BytesIO()
        fp.write(zip_data)
        with zipfile.ZipFile(fp, "r") as z:
            inv_file = invoice.name.replace("/", "-") + ".xml"
            inv_xml_content = z.read(inv_file)
            inv_root = etree.fromstring(inv_xml_content)
            # Count invoice_item_list elements (should be 1, not 2)
            # Handle namespace properly for XPath
            nsmap = inv_root.nsmap
            if None in nsmap:
                # Remove the default namespace to avoid XPath issues
                nsmap = {k: v for k, v in nsmap.items() if k is not None}
                nsmap["ns"] = inv_root.nsmap[None]
                invoice_items = inv_root.xpath(
                    "//ns:invoice_item_list", namespaces=nsmap
                )
            else:
                invoice_items = inv_root.xpath("//invoice_item_list")
            self.assertEqual(
                len(invoice_items), 1, "Only non-zero amount lines should be exported"
            )
            # Verify the exported line is the one without discount
            exported_item = invoice_items[0]
            self.assertEqual(
                exported_item.get("product_id"),
                self.consulting.default_code,
                "The exported line should be the consulting product (no discount)",
            )
