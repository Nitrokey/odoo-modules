# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict

from odoo import models, api

_logger = logging.getLogger(__name__)


class InvoiceBVRFromInvoice(models.AbstractModel):
    _name = 'report.deutsch_report'


class IrActionsReportReportlab(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        if (self.report_name not in ['carrier_shipping_label_template.deutsch_report']) \
                or not res_ids:
            return super().render_qweb_pdf(res_ids, data)

        save_in_attachment = OrderedDict()
        Model = self.env[self.model]
        records = Model.browse(res_ids)
        wk_record_ids = Model
        for record in records:
            attachment_id = record.label_de_attach_id
            if attachment_id:
                save_in_attachment[record.id] = attachment_id
            if not attachment_id:
                wk_record_ids += record
        res_ids = wk_record_ids.ids
        return self._post_pdf(save_in_attachment, res_ids=res_ids), 'pdf'
