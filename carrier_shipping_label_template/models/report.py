from odoo import models, api


class IrActionsReportReportlab(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        if  self.report_name in ['carrier_shipping_label_template.report_shipping_label']:
            self = self.with_context(shipping_label_res_ids=res_ids)
        return super(IrActionsReportReportlab, self).render_qweb_pdf(res_ids, data)

    @api.model
    def render_qweb_html(self, docids, data=None):
        """This method generates and returns html version of a report.
        """
        if (self.report_name not in ['carrier_shipping_label_template.report_shipping_label']) \
                or not docids:
            return super(IrActionsReportReportlab, self).render_qweb_html(docids, data)
        new_doc_ids = []
        for picking in self.env['stock.picking'].browse(docids):
            if picking.label_de_attach_id:
                continue
            else:
                new_doc_ids.append(picking.id)
        return super(IrActionsReportReportlab, self).render_qweb_html(new_doc_ids, data)

    @api.multi
    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        if self.report_name not in ['carrier_shipping_label_template.report_shipping_label']:
            return super(IrActionsReportReportlab, self)._post_pdf(save_in_attachment, pdf_content, res_ids)

        shipping_label_res_ids = self._context.get('shipping_label_res_ids')
        if shipping_label_res_ids:
            Model = self.env[self.model]
            records = Model.browse(shipping_label_res_ids)
            wk_record_ids = Model
            for record in records:
                attachment_id = record.label_de_attach_id
                if attachment_id:
                    save_in_attachment[record.id] = attachment_id
                else:
                    wk_record_ids += record
            res_ids = wk_record_ids.ids
            if not res_ids:
                pdf_content = None

        return super(IrActionsReportReportlab, self)._post_pdf(save_in_attachment, pdf_content, res_ids)

    @api.multi
    def retrieve_attachment(self, record):
        if self.report_name in ['carrier_shipping_label_template.report_shipping_label']:
            return None
        return super(IrActionsReportReportlab, self).retrieve_attachment(record)
