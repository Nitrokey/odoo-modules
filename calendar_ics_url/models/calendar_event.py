import vobject

from odoo import models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    def _get_ics_file(self):
        """Override to add URL field to ICS files from videocall_location."""
        result = super()._get_ics_file()

        for meeting in self:
            if meeting.id not in result:
                continue

            # Only add URL if videocall_location is set
            if not meeting.videocall_location:
                continue

            # Parse the existing ICS content
            cal = vobject.readOne(result[meeting.id].decode("utf-8"))

            # Add URL property to the event
            if hasattr(cal, "vevent"):
                cal.vevent.add("url").value = meeting.videocall_location

            # Re-serialize the calendar
            result[meeting.id] = cal.serialize().encode("utf-8")

        return result
