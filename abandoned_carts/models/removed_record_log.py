from odoo import fields, models


class RemovedRecordLog(models.Model):
    """Shows a log for records which were removed"""

    _name = "removed.record.log"
    _description = "Abandoned removed Record Log"
    _order = "date desc"

    name = fields.Char()
    date = fields.Datetime()
    res_model = fields.Char("Model")
    res_id = fields.Integer("Record ID")
    user_id = fields.Many2one("res.users")
    error = fields.Text("Delete Error")
