from odoo.tests.common import TransactionCase


class TestCRMProfiling(TransactionCase):
    def setUp(self):
        super().setUp()
        self.question = self.env["crm_profiling.question"]
        self.questionnaire = self.env["crm_profiling.questionnaire"]
        self.answer = self.env["crm_profiling.answer"]
        self.resPartner = self.env["res.partner"]
        self.category_model = self.env["res.partner.category"]
        self.segmentation_model = self.env["crm.segmentation"]

    def test_recompute_categ(self):
        # Create test data
        category_1 = self.category_model.create({"name": "First Category"})
        category_2 = self.category_model.create({"name": "Second Category"})
        question = self.question.create({"name": "Question A"})
        answer1 = self.answer.create({"name": "Answer 1", "question_id": question.id})
        answer2 = self.answer.create({"name": "Answer 2", "question_id": question.id})
        answer3 = self.answer.create({"name": "Answer 3", "question_id": question.id})
        answer4 = self.answer.create({"name": "Answer 4", "question_id": question.id})
        self.questionnaire.create(
            {
                "name": "Questionnaire 1",
                "description": "Test",
                "questions_ids": [(6, 0, question.ids)],
            }
        )
        partner = self.resPartner.create(
            {
                "name": "Partner",
                "category_id": [(6, 0, category_1.ids)],
                "answers_ids": [(6, 0, answer1.ids)],
            }
        )
        segmentation_1 = self.segmentation_model.create(
            {
                "name": "Segmentation A",
                "categ_id": category_2.id,
                "exclusif": False,
                "sales_purchase_active": True,
                "profiling_active": True,
                "answer_yes": [(6, 0, answer1.ids)],
                "answer_no": [(6, 0, answer2.ids)],
            }
        )
        segmentation = self.segmentation_model.create(
            {
                "name": "Segmentation A",
                "categ_id": category_1.id,
                "exclusif": False,
                "sales_purchase_active": True,
                "profiling_active": True,
                # 'answer_yes': [(6, 0, answer1.ids)],
                # 'answer_no': [(6, 0, answer2.ids)],
            }
        )
        segmentation_1.parent_id = segmentation.id
        # Perform the test with wrong answer
        partner._recompute_categ([answer3.id, answer4.id])
        # Perform the test with right answer
        partner._recompute_categ([answer1.id, answer2.id])
        # Perform the test with 1 right answer
        partner._recompute_categ([answer1.id])

        partner.with_context(active_id=partner.id)._questionnaire_compute(
            [answer1.id, answer2.id]
        )
