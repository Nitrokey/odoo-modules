from odoo import models,http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class NitrokeyCustomerPortal(CustomerPortal):

    def _show_report(self, model, report_type, report_ref, download=False):
        if download == 'true':
            report_sudo = request.env.ref(report_ref).sudo()
            new_dict = dict(report_sudo._context)
            new_dict['must_skip_send_to_printer'] = True
            report_sudo.env.context = new_dict
        return super(NitrokeyCustomerPortal, self)._show_report(model, report_type, report_ref, download)
