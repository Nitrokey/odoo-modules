from collections import defaultdict

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def filter_shipping_labels(self, attachments):
        """Filtering function to get only the labels. Naming etc. depends on the
        delivery module which is why the hook exists"""
        return attachments

    def send_shipping(self, pickings):
        domain = [("res_model", "=", pickings._name), ("res_id", "in", pickings.ids)]
        labels = self.env["ir.attachment"].search(domain)
        res = super().send_shipping(pickings)

        # All attachments that are generated during send_shipping call should be
        # shipping labels
        attachments = defaultdict(labels.browse)
        for label in (labels.search(domain) - labels).exists():
            attachments[label.res_id] |= label

        for pick in pickings:
            labels = attachments.get(pick.id)
            label_ids = self.filter_shipping_labels(labels).ids if labels else []
            pick.shipping_label_ids = [(6, 0, label_ids)]

        return res
