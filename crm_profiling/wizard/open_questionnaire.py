from odoo import _, api, fields, models


class OpenQuestionnaireLine(models.TransientModel):
    _name = "open.questionnaire.line"
    _rec_name = "question_id"
    _description = "Open Questionnaire Line"

    question_id = fields.Many2one("crm_profiling.question", "Question", required=True)
    answer_id = fields.Many2one("crm_profiling.answer", "Answer")
    wizard_id = fields.Many2one("open.questionnaire", "Questionnaire")


class OpenQuestionnaire(models.TransientModel):
    _name = "open.questionnaire"
    _description = "Open Questionnaire"

    questionnaire_id = fields.Many2one(
        "crm_profiling.questionnaire", "Questionnaire name"
    )
    question_ans_ids = fields.One2many(
        "open.questionnaire.line", "wizard_id", "Question / Answers"
    )

    @api.model
    def default_get(self, fields):
        context = self._context.copy()
        res = super().default_get(fields)
        questionnaire_id = context.get("questionnaire_id", False)
        if questionnaire_id and "question_ans_ids" in fields:
            query = """
                SELECT question AS question_id
                FROM profile_questionnaire_quest_rel
                WHERE questionnaire = %s"""
            self._cr.execute(query, (questionnaire_id,))
            result = self._cr.dictfetchall()
            final_data = []
            for data in result:
                final_data.append((0, 0, data))
            res.update(question_ans_ids=final_data)
        return res

    def questionnaire_compute(self):
        """Adds selected answers in partner form"""
        model = self._context.get("active_model")
        answers = []
        if model == "res.partner":
            for d in self.question_ans_ids:
                if d.answer_id:
                    answers.append(d.answer_id.id)
            self.env[model]._questionnaire_compute(answers)
        return {"type": "ir.actions.act_window_close"}

    def build_form(self):
        models_data = self.env["ir.model.data"]
        result = models_data.check_object_reference(
            "crm_profiling", "open_questionnaire_form"
        )
        res_id = models_data.browse(result[1]).id
        context = dict(
            self.env.context or {},
            questionnaire_id=self.questionnaire_id.id,
        )

        return {
            "name": _("Questionnaire"),
            "view_mode": "form",
            "res_model": "open.questionnaire",
            "type": "ir.actions.act_window",
            "views": [(res_id, "form")],
            "target": "new",
            "context": context,
        }
