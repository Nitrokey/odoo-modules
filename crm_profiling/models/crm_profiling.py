from odoo import api, fields, models


class Question(models.Model):
    """Question"""

    _name = "crm_profiling.question"
    _description = "Question"

    name = fields.Char("Question", required=True)
    answers_ids = fields.One2many(
        "crm_profiling.answer", "question_id", "Available Answers", copy=True
    )


class Questionnaire(models.Model):
    """Questionnaire"""

    _name = "crm_profiling.questionnaire"
    _description = "Questionnaire"

    name = fields.Char("Questionnaire", required=True)
    description = fields.Text(required=True)
    questions_ids = fields.Many2many(
        "crm_profiling.question",
        "profile_questionnaire_quest_rel",
        "questionnaire",
        "question",
        "Questions",
    )


class Answer(models.Model):
    _name = "crm_profiling.answer"
    _description = "Answer"

    name = fields.Char("Answer", required=True)
    question_id = fields.Many2one("crm_profiling.question", "Question")


class ResPartner(models.Model):
    _inherit = "res.partner"

    answers_ids = fields.Many2many(
        "crm_profiling.answer",
        "partner_question_rel",
        "partner",
        "answer",
        "Answers",
    )

    def _recompute_categ(self, answers_ids):
        """
        Recompute category
        :param self:            The current res.partner.
        :param answers_ids:     Answers's IDs.
        """
        self.ensure_one()

        ok = []
        self.env.cr.execute(
            """
            SELECT r.category_id
            FROM res_partner_res_partner_category_rel r
            LEFT JOIN crm_segmentation s ON (r.category_id = s.categ_id)
            WHERE r.partner_id = %s AND
            (s.exclusif = false OR s.exclusif IS NULL)
            """,
            (self.id,),
        )
        for x in self.env.cr.fetchall():
            ok.append(x[0])

        query = """
            SELECT id, categ_id
            FROM crm_segmentation
            WHERE profiling_active = true"""
        if ok:
            query += " AND categ_id NOT IN (%s) ORDER BY id"
            self.env.cr.execute(query, (",".join(str(i) for i in ok),))
        else:
            query = query + """ ORDER BY id """
            self.env.cr.execute(query)
        segm_cat_ids = self.env.cr.fetchall()
        segm_obj = self.env["crm.segmentation"]

        for segm_id, cat_id in segm_cat_ids:
            segm = segm_obj.browse([segm_id])
            if segm.test_prof(self.id, answers_ids):
                ok.append(cat_id)
        return ok

    @api.model
    def _questionnaire_compute(self, answers):
        """
        :param self:       The current res.partner.
        :param answers:       A standard dictionary for contextual values.
        """
        partner_id = self._context.get("active_id")
        query = "SELECT answer FROM partner_question_rel WHERE partner=%s"
        self._cr.execute(query, (partner_id,))
        for x in self._cr.fetchall():
            answers.append(x[0])
        self.browse(partner_id).write({"answers_ids": [[6, 0, answers]]})
        return {}

    def write(self, vals):
        """
        :param self:       The current res.partner.
        :param vals:       A standard dictionary for contextual values.
        """

        if "answers_ids" in vals:
            vals["category_id"] = [
                (6, 0, self._recompute_categ(vals["answers_ids"][0][2]))
            ]

        return super().write(vals)
