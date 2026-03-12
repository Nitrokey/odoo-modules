from datetime import datetime, timedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

try:
    import vobject
except ImportError:
    vobject = None


@tagged("post_install", "-at_install")
class TestCalendarIcsUrl(TransactionCase):
    """Test calendar event ICS file generation with URL field."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.ref("base.user_admin")
        cls.partner = cls.env.ref("base.partner_admin")

    def test_ics_file_with_url(self):
        """Test that URL is added to ICS file when videocall_location is set."""
        if not vobject:
            self.skipTest("vobject module not available")

        # Create a calendar event with videocall_location
        event = self.env["calendar.event"].create(
            {
                "name": "Test Meeting with URL",
                "start": datetime.now(),
                "stop": datetime.now() + timedelta(hours=1),
                "user_id": self.user.id,
                "partner_ids": [(6, 0, [self.partner.id])],
                "videocall_location": "https://meet.example.com/test-meeting",
            }
        )

        # Generate ICS file
        ics_files = event._get_ics_file()

        # Verify ICS file was generated
        self.assertIn(event.id, ics_files)

        # Parse the ICS content
        ics_content = ics_files[event.id].decode("utf-8")
        cal = vobject.readOne(ics_content)

        # Verify URL property exists and has correct value
        self.assertTrue(hasattr(cal.vevent, "url"))
        self.assertEqual(cal.vevent.url.value, "https://meet.example.com/test-meeting")

    def test_ics_file_without_url(self):
        """Test that ICS file is generated correctly without videocall_location."""
        if not vobject:
            self.skipTest("vobject module not available")

        # Create a calendar event without videocall_location
        event = self.env["calendar.event"].create(
            {
                "name": "Test Meeting without URL",
                "start": datetime.now(),
                "stop": datetime.now() + timedelta(hours=1),
                "user_id": self.user.id,
                "partner_ids": [(6, 0, [self.partner.id])],
            }
        )

        # Generate ICS file
        ics_files = event._get_ics_file()

        # Verify ICS file was generated
        self.assertIn(event.id, ics_files)

        # Parse the ICS content
        ics_content = ics_files[event.id].decode("utf-8")
        cal = vobject.readOne(ics_content)

        # Verify URL property does not exist
        self.assertFalse(hasattr(cal.vevent, "url"))

    def test_ics_file_preserves_other_fields(self):
        """Test that adding URL preserves other ICS fields like LOCATION."""
        if not vobject:
            self.skipTest("vobject module not available")

        # Create a calendar event with both location and videocall_location
        event = self.env["calendar.event"].create(
            {
                "name": "Test Meeting with Location and URL",
                "start": datetime.now(),
                "stop": datetime.now() + timedelta(hours=1),
                "user_id": self.user.id,
                "partner_ids": [(6, 0, [self.partner.id])],
                "location": "Conference Room A",
                "videocall_location": "https://meet.example.com/room-a",
            }
        )

        # Generate ICS file
        ics_files = event._get_ics_file()

        # Parse the ICS content
        ics_content = ics_files[event.id].decode("utf-8")
        cal = vobject.readOne(ics_content)

        # Verify both LOCATION and URL exist
        self.assertTrue(hasattr(cal.vevent, "location"))
        self.assertEqual(cal.vevent.location.value, "Conference Room A")
        self.assertTrue(hasattr(cal.vevent, "url"))
        self.assertEqual(cal.vevent.url.value, "https://meet.example.com/room-a")

    def test_ics_file_with_empty_videocall_location(self):
        """Test that empty videocall_location doesn't add URL field."""
        if not vobject:
            self.skipTest("vobject module not available")

        # Create a calendar event with empty videocall_location
        event = self.env["calendar.event"].create(
            {
                "name": "Test Meeting with Empty URL",
                "start": datetime.now(),
                "stop": datetime.now() + timedelta(hours=1),
                "user_id": self.user.id,
                "partner_ids": [(6, 0, [self.partner.id])],
                "videocall_location": "",
            }
        )

        # Generate ICS file
        ics_files = event._get_ics_file()

        # Parse the ICS content
        ics_content = ics_files[event.id].decode("utf-8")
        cal = vobject.readOne(ics_content)

        # Verify URL property does not exist
        self.assertFalse(hasattr(cal.vevent, "url"))
