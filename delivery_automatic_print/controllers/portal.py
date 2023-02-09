from odoo import SUPERUSER_ID
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class NitrokeyCustomerPortal(CustomerPortal):
    def _show_report(self, model, report_type, report_ref, download=False):
        if download == "true":
            report_sudo = request.env.ref(report_ref).with_user(SUPERUSER_ID)
            new_dict = dict(report_sudo._context)
            new_dict["must_skip_send_to_printer"] = True
            report_sudo.env.context = new_dict
        data = super()._show_report(model, report_type, report_ref, download)
        return data
