from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.delivery_dhl_parcel_de.models.delivery_carrier import DeliveryCarrier


@tagged("post_install", "-at_install")
class TestPackstation(TransactionCase):
    """Unit tests for DHL Packstation (locker) address parsing helpers."""

    def test_is_packstation(self):
        """Street2 containing 'Packstation' (any case) is detected as a locker."""
        self.assertTrue(DeliveryCarrier._is_packstation("Packstation 123"))
        self.assertTrue(DeliveryCarrier._is_packstation("PACKSTATION 456"))
        self.assertTrue(DeliveryCarrier._is_packstation("packstation 789"))

    def test_is_packstation_false(self):
        """Normal street2 values, empty strings and None are not Packstations."""
        self.assertFalse(DeliveryCarrier._is_packstation("Apartment 2B"))
        self.assertFalse(DeliveryCarrier._is_packstation(""))
        self.assertFalse(DeliveryCarrier._is_packstation(None))

    def test_get_locker_id_simple(self):
        """Locker ID is extracted from 'Packstation NNN' formats."""
        self.assertEqual(
            DeliveryCarrier._get_packstation_locker_id("Packstation 123"), "123"
        )
        self.assertEqual(
            DeliveryCarrier._get_packstation_locker_id("PACKSTATION 456"), "456"
        )

    def test_get_locker_id_with_colon(self):
        """Locker ID is extracted when a colon separates the keyword from the ID."""
        self.assertEqual(
            DeliveryCarrier._get_packstation_locker_id("Packstation: 456"), "456"
        )
        self.assertEqual(
            DeliveryCarrier._get_packstation_locker_id("PACKSTATION  :  789"), "789"
        )
