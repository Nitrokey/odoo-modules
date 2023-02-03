from odoo import fields, models


class QueueJobBatch(models.Model):
    _inherit = "queue.job.batch"

    segmentation_id = fields.Many2one(
        comodel_name="crm.segmentation", inverse_name="job_batch_ids"
    )
