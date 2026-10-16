# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from markupsafe import Markup

from odoo import _, models

_logger = logging.getLogger(__name__)

CLOSED_STATES = ("success", "failed", "canceled")


class IotQualityControl(models.AbstractModel):
    _name = "iot.quality.control"
    _description = "IoT measurements for Quality Control"

    def _error(self, message):
        _logger.warning(message)
        return {"status": "error", "message": message}

    def _get_inspection(self, production):
        """Return the quality inspection of the MO that receives the notes.

        If the system parameter ``iot_quality_control.qc_test_id`` is set, only
        inspections of that test are considered. Open inspections are preferred
        over closed ones; the most recent one wins.
        """
        domain = [("production_id", "=", production.id)]
        test_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("iot_quality_control.qc_test_id")
        )
        if test_id and test_id.isdigit():
            domain.append(("test", "=", int(test_id)))
        inspections = self.env["qc.inspection"].search(domain, order="id desc")
        open_inspections = inspections.filtered(lambda i: i.state not in CLOSED_STATES)
        return (open_inspections or inspections)[:1]

    def post_measurement(self, value=None, mo_id=None):
        """Post one key/value measurement as a note on the MO's inspection.

        Called through ``iot.device.input``: the key is the address of the
        input that received the value. ``mo_id`` is the reference of the
        Manufacturing Order, e.g. ``WH/MO/00001``.
        """
        device_input = self.env["iot.device.input"].browse(
            self.env.context.get("iot_device_input_id")
        )
        key = device_input.address or device_input.name
        if not key:
            return self._error(_("Measurement key could not be determined"))
        mo_name = str(mo_id or "").strip()
        if not mo_name:
            return self._error(_("A valid mo_id is required"))
        production = self.env["mrp.production"].search([("name", "=", mo_name)])
        if not production:
            return self._error(_("Manufacturing Order %s not found", mo_name))
        if len(production) > 1:
            return self._error(_("Manufacturing Order %s is not unique", mo_name))
        inspection = self._get_inspection(production)
        if not inspection:
            return self._error(
                _("No quality control found for %s", production.display_name)
            )
        inspection.message_post(
            body=Markup("<b>%s</b>: %s") % (key, value),
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        return {"status": "ok"}
