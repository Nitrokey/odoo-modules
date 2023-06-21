from odoo.tests.common import TransactionCase


class TestOpenQuestionnaire(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Questionnaire = self.env["crm_profiling.questionnaire"]
        self.Partner = self.env["res.partner"]

    def test_questionnaire_compute(self):
        partner = self.Partner.create({"name": "Test Partner"})
        question = self.env["crm_profiling.question"].create(
            {"name": "Sample Question"}
        )
        answer = self.env["crm_profiling.answer"].create(
            {"name": "Sample Answer", "question_id": question.id}
        )

        wizard = self.env["open.questionnaire"].create(
            {
                "questionnaire_id": False,
                "question_ans_ids": [
                    (0, 0, {"question_id": question.id, "answer_id": answer.id})
                ],
            }
        )
        wizard.with_context(
            active_model="res.partner", active_id=partner.id
        ).questionnaire_compute()

        self.assertEqual(partner.answers_ids, answer)

    def test_build_form(self):
        questionnaire = self.Questionnaire.create(
            {"name": "Sample Questionnaire", "description": "Testing"}
        )
        question = self.env["crm_profiling.question"].create(
            {"name": "Sample Question"}
        )
        questionnaire.write({"questions_ids": [(4, question.id)]})
        wizard = (
            self.env["open.questionnaire"]
            .with_context(questionnaire_id=questionnaire.id)
            .create({"questionnaire_id": questionnaire.id})
        )
        self.assertEqual(wizard.question_ans_ids.question_id.id, question.id)
        action = wizard.build_form()
        self.assertEqual(action["res_model"], "open.questionnaire")
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["context"]["questionnaire_id"], questionnaire.id)
