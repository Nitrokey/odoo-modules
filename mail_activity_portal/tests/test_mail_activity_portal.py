# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMailActivityPortal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Make sure no pre-existing team interferes with the lookup
        cls.env["mail.activity.team"].search([]).write({"active": False})
        cls.partner_model = cls.env["ir.model"]._get("res.partner")
        cls.user_leader = cls.env["res.users"].create(
            {
                "name": "Team Leader",
                "login": "team_leader_portal",
                "email": "leader@example.com",
            }
        )
        cls.user_member = cls.env["res.users"].create(
            {
                "name": "Team Member",
                "login": "team_member_portal",
                "email": "member@example.com",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Portal Partner"})
        cls.activity_type = cls.env.ref("mail.mail_activity_data_email")

    def _create_team(self, **kwargs):
        vals = {
            "name": "Portal Team",
            "res_model_ids": [(6, 0, self.partner_model.ids)],
        }
        vals.update(kwargs)
        return self.env["mail.activity.team"].create(vals)

    def _get_activities(self):
        return self.env["mail.activity"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", self.partner.id),
                ("activity_type_id", "=", self.activity_type.id),
                ("automated", "=", True),
            ]
        )

    def test_message_post_without_portal_context(self):
        """No activity is created for a regular message post."""
        self._create_team(user_id=self.user_leader.id)
        msg = self.partner.message_post(body="Hello", message_type="comment")
        self.assertTrue(msg)
        self.assertFalse(self._get_activities())

    def test_message_post_from_portal_with_leader(self):
        """Portal message schedules an activity for the team (leader set)."""
        team = self._create_team(
            user_id=self.user_leader.id, member_ids=[(6, 0, self.user_member.ids)]
        )
        msg = self.partner.with_context(message_post_store=True).message_post(
            body="From portal", message_type="comment"
        )
        self.assertTrue(msg)
        activity = self._get_activities()
        self.assertEqual(len(activity), 1)
        self.assertEqual(activity.team_id, team)

    def test_message_post_from_portal_with_members_only(self):
        """Without leader the team members are used."""
        team = self._create_team(member_ids=[(6, 0, self.user_member.ids)])
        self.partner.with_context(message_post_store=True).message_post(
            body="From portal", message_type="comment"
        )
        activity = self._get_activities()
        self.assertEqual(len(activity), 1)
        self.assertEqual(activity.team_id, team)

    def test_no_duplicate_activity(self):
        """A second portal message does not create another activity."""
        self._create_team(user_id=self.user_leader.id)
        thread = self.partner.with_context(message_post_store=True)
        thread.message_post(body="One", message_type="comment")
        thread.message_post(body="Two", message_type="comment")
        self.assertEqual(len(self._get_activities()), 1)

    def test_no_team_for_model(self):
        """No activity if no team is configured for the model."""
        self.partner.schedule_email_activity()
        self.assertFalse(self._get_activities())
        # team for another model only
        self._create_team(
            user_id=self.user_leader.id,
            res_model_ids=[(6, 0, self.env["ir.model"]._get("res.users").ids)],
        )
        self.partner.schedule_email_activity()
        self.assertFalse(self._get_activities())

    def test_team_without_users(self):
        """Team without leader and members creates no activity."""
        self._create_team()
        self.partner.schedule_email_activity()
        self.assertFalse(self._get_activities())

    def test_empty_recordset(self):
        """Calling on an empty recordset is a no-op."""
        self.assertIsNone(self.env["res.partner"].schedule_email_activity())

    def test_model_without_activity_mixin(self):
        """Models lacking activity_ids are skipped."""
        self._create_team(user_id=self.user_leader.id)
        # discuss.channel is a mail.thread without mail.activity.mixin
        channel = self.env["discuss.channel"].create({"name": "No activities"})
        self.assertNotIn("activity_ids", channel._fields)
        self.assertIsNone(channel.schedule_email_activity())
