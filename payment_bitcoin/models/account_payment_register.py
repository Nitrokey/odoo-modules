from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.model
    def _get_batch_communication(self, batch_result):
        """Helper to compute the communication based on the batch.
        :param batch_result:    A batch returned by '_get_batches'.
        :return:                A string representing a communication to be set on payment.
        """
        labels = {
            line.move_id.ref or line.name or line.move_id.name
            for line in batch_result["lines"]
        }
        return " ".join(sorted(labels))
