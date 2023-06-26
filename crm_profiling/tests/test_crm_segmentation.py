from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCRMSegmentation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_model = self.env["res.partner"]
        self.segmentation_model = self.env["crm.segmentation"]
        self.segmentation_line_model = self.env["crm.segmentation.line"]
        self.category_model = self.env["res.partner.category"]
        self.answer_model = self.env["crm_profiling.answer"]
        self.batch_model = self.env["queue.job.batch"]

    def test_process_start_exclusive(self):
        # Create test data
        category = self.category_model.create({"name": "Category A"})
        segmentation = self.segmentation_model.create(
            {
                "name": "Segmentation A",
                "categ_id": category.id,
                "exclusif": True,
                "sales_purchase_active": True,
                "segmentation_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Criterion A",
                            "expr_value": 100,
                        },
                    )
                ],
            }
        )
        partners = self.partner_model.create(
            [{"name": "Partner 1"}, {"name": "Partner 2"}, {"name": "Partner 3"}]
        )
        partners.write({"category_id": [(6, 0, category.ids)]})

        self.batch_model.create(
            {
                "name": "Test Q Batch",
                "user_id": self.env.ref("base.user_root").id,
                "segmentation_id": segmentation.id,
            }
        )
        # Stop before to get inside if condition in this method
        # because at this we did not start job.
        segmentation.process_continue()
        segmentation.last_batch_id = False
        segmentation.process_stop()

        # Start the process
        segmentation.process_start()
        self.assertEqual(segmentation.state, "running")

        # Stop the process
        segmentation.process_stop()
        self.assertEqual(segmentation.state, "stopped")

        # Continue the process
        segmentation.process_continue()

        # Check the results
        self.assertFalse(category in partners.category_id)
        # self.assertTrue(category in partners[1].category_id)
        # self.assertTrue(category in partners[2].category_id)

    def test_check_parent_id(self):
        # Create test data
        category = self.category_model.create({"name": "Category A"})
        segmentation_1 = self.segmentation_model.create(
            {
                "name": "Segmentation A",
                "categ_id": category.id,
                "exclusif": True,
                "sales_purchase_active": True,
                "segmentation_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Criterion A",
                            "expr_value": 100,
                        },
                    )
                ],
            }
        )
        segmentation_2 = self.segmentation_model.create(
            {
                "name": "Segmentation A",
                "categ_id": category.id,
                "exclusif": True,
                "sales_purchase_active": True,
                "parent_id": segmentation_1.id,
                "segmentation_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Criterion A",
                            "expr_value": 100,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(ValidationError) as _:
            segmentation_1.parent_id = segmentation_2.id

    def test_process_start_non_exclusive(self):
        # Create test data
        category = self.category_model.create({"name": "Category A"})
        segmentation = self.segmentation_model.create(
            {
                "name": "Segmentation A",
                "categ_id": category.id,
                "exclusif": False,
                "sales_purchase_active": True,
            }
        )
        partners = self.partner_model.create(
            [{"name": "Partner 1"}, {"name": "Partner 2"}, {"name": "Partner 3"}]
        )
        self.segmentation_line_model.create(
            {
                "segmentation_id": segmentation.id,
                "name": "Criterion A",
                "expr_value": 100,
            }
        )
        partners.write({"category_id": [(4, category.id, 0)]})

        # Start the process
        segmentation.process_start()

        # Check the results
        self.assertTrue(category in partners[0].category_id)
        self.assertTrue(category in partners[1].category_id)
        self.assertTrue(category in partners[2].category_id)

    def test_process_start_partner_check(self):
        category = self.category_model.create({"name": "Category A"})
        segmentation = self.segmentation_model.create(
            {
                "name": "Segmentation A",
                "categ_id": category.id,
                "exclusif": False,
                "sales_purchase_active": True,
            }
        )
        # Create test data
        self.segmentation_line_model.create(
            {
                "name": "Segmentation Line A",
                "expr_name": "sale",
                "expr_operator": ">",
                "expr_value": 1000.0,
                "operator": "and",
                "segmentation_id": segmentation.id,
            }
        )
        self.partner_model.create(
            {"name": "Partner 1", "category_id": [(6, 0, category.ids)]}
        )
        self.partner_model.create(
            {"name": "Partner 2", "category_id": [(6, 0, category.ids)]}
        )
        self.partner_model.create(
            {"name": "Partner 3", "category_id": [(6, 0, category.ids)]}
        )
