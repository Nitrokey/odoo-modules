from unittest.mock import MagicMock, patch

import jwt

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.mail.tools.discuss import Store

LIVEKIT_URL = "wss://livekit.example.com"
LIVEKIT_KEY = "test_api_key"
LIVEKIT_SECRET = "test_api_secret_which_is_long_enough_for_hs256"
SESSION_MODEL = "odoo.addons.mail_livekit.models.mail_rtc_session"


@tagged("post_install", "-at_install")
class TestMailLivekit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env["ir.config_parameter"].sudo()
        cls.partner = cls.env["res.partner"].create({"name": "Livekit Partner"})
        cls.channel = cls.env["discuss.channel"].create(
            {"name": "Livekit Channel", "channel_type": "channel"}
        )
        cls.member = cls.env["discuss.channel.member"].create(
            {"channel_id": cls.channel.id, "partner_id": cls.partner.id}
        )

    def _configure(self, enabled="True", url=LIVEKIT_URL, key=LIVEKIT_KEY, secret=None):
        secret = LIVEKIT_SECRET if secret is None else secret
        self.icp.set_param("mail_livekit.livekit_enabled", enabled)
        self.icp.set_param("mail_livekit.livekit_server_url", url)
        self.icp.set_param("mail_livekit.livekit_api_key", key)
        self.icp.set_param("mail_livekit.livekit_api_secret", secret)

    def _create_session(self, member=None):
        return self.env["discuss.channel.rtc.session"].create(
            {"channel_member_id": (member or self.member).id}
        )

    def _decode(self, token):
        return jwt.decode(
            token,
            LIVEKIT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )

    # config parameters

    def test_config_params_default(self):
        params = self.env["discuss.channel.rtc.session"]._get_livekit_config_params()
        self.assertFalse(params["enabled"])
        self.assertFalse(params["valid"])

    def test_config_params_valid(self):
        self._configure()
        params = self.env["discuss.channel.rtc.session"]._get_livekit_config_params()
        self.assertTrue(params["enabled"])
        self.assertTrue(params["valid"])
        self.assertEqual(params["url"], LIVEKIT_URL)
        self.assertEqual(params["api_key"], LIVEKIT_KEY)
        self.assertEqual(params["api_secret"], LIVEKIT_SECRET)

    def test_config_params_disabled_but_filled(self):
        self._configure(enabled="False")
        params = self.env["discuss.channel.rtc.session"]._get_livekit_config_params()
        self.assertFalse(params["enabled"])
        self.assertFalse(params["valid"])

    def test_config_params_enabled_incomplete(self):
        for kwargs in (
            {"url": "  "},
            {"key": ""},
            {"secret": " "},
        ):
            self._configure(**kwargs)
            with self.assertRaises(UserError):
                self.env["discuss.channel.rtc.session"]._get_livekit_config_params()

    def test_config_params_enabled_missing(self):
        self.icp.set_param("mail_livekit.livekit_enabled", "True")
        with self.assertRaises(UserError):
            self.env["discuss.channel.rtc.session"]._get_livekit_config_params()

    # session creation / tokens

    def test_session_without_livekit(self):
        session = self._create_session()
        self.assertFalse(session.livekit_token)
        self.assertFalse(session.livekit_room_name)
        self.assertFalse(session.livekit_url)

    def test_session_disabled_with_incomplete_config(self):
        self._configure(enabled="False", url="")
        session = self._create_session()
        self.assertFalse(session.livekit_token)

    def test_session_enabled_but_misconfigured(self):
        self._configure(key="")
        with self.assertRaises(UserError):
            self._create_session()

    def test_session_token_partner(self):
        self._configure()
        session = self._create_session()
        self.assertEqual(session.livekit_room_name, f"odoo_channel_{self.channel.id}")
        self.assertEqual(session.livekit_url, LIVEKIT_URL)
        self.assertTrue(session.livekit_token)
        claims = self._decode(session.livekit_token)
        self.assertEqual(claims["iss"], LIVEKIT_KEY)
        self.assertEqual(claims["sub"], f"partner:{self.partner.id}")
        self.assertEqual(claims["name"], self.partner.name)
        video = claims["video"]
        self.assertTrue(video["roomJoin"])
        self.assertEqual(video["room"], session.livekit_room_name)
        self.assertTrue(video["canPublish"])
        self.assertTrue(video["canSubscribe"])

    def test_session_token_guest(self):
        self._configure()
        guest = self.env["mail.guest"].create({"name": "Some Guest"})
        member = self.env["discuss.channel.member"].create(
            {"channel_id": self.channel.id, "guest_id": guest.id}
        )
        session = self._create_session(member)
        claims = self._decode(session.livekit_token)
        self.assertEqual(claims["sub"], f"guest:{member.id}")
        self.assertEqual(claims["name"], f"Guest {member.id}")

    def test_generate_token_mocked(self):
        session = self._create_session()
        token_builder = MagicMock()
        token_builder.with_identity.return_value = token_builder
        token_builder.with_name.return_value = token_builder
        token_builder.with_grants.return_value = token_builder
        token_builder.to_jwt.return_value = "fake.jwt.token"
        with patch(
            f"{SESSION_MODEL}.AccessToken", return_value=token_builder
        ) as access_token:
            session._generate_livekit_token(
                {"api_key": "k", "api_secret": "s", "url": "wss://x"}
            )
        access_token.assert_called_once_with("k", "s")
        token_builder.with_identity.assert_called_once_with(
            f"partner:{self.partner.id}"
        )
        token_builder.with_name.assert_called_once_with(self.partner.name)
        self.assertEqual(session.livekit_token, "fake.jwt.token")
        self.assertEqual(session.livekit_url, "wss://x")
        self.assertEqual(session.livekit_room_name, f"odoo_channel_{self.channel.id}")

    # store serialization

    def test_to_store_without_livekit(self):
        session = self._create_session()
        store = Store()
        session._to_store(store)
        data = store.get_result()["discuss.channel.rtc.session"][0]
        self.assertNotIn("livekit_token", data)
        self.assertNotIn("livekit_url", data)

    def test_to_store_with_livekit(self):
        self._configure()
        session = self._create_session()
        store = Store()
        session._to_store(store)
        data = store.get_result()["discuss.channel.rtc.session"][0]
        self.assertEqual(data["id"], session.id)
        self.assertEqual(data["livekit_token"], session.livekit_token)
        self.assertEqual(data["livekit_room_name"], session.livekit_room_name)
        self.assertEqual(data["livekit_url"], LIVEKIT_URL)

    # settings

    def test_res_config_settings_roundtrip(self):
        settings = self.env["res.config.settings"].create(
            {
                "livekit_enabled": True,
                "livekit_server_url": LIVEKIT_URL,
                "livekit_api_key": LIVEKIT_KEY,
                "livekit_api_secret": LIVEKIT_SECRET,
            }
        )
        settings.execute()
        self.assertEqual(self.icp.get_param("mail_livekit.livekit_enabled"), "True")
        get_param = self.icp.get_param
        self.assertEqual(get_param("mail_livekit.livekit_server_url"), LIVEKIT_URL)
        self.assertEqual(get_param("mail_livekit.livekit_api_key"), LIVEKIT_KEY)
        self.assertEqual(get_param("mail_livekit.livekit_api_secret"), LIVEKIT_SECRET)
        new_settings = self.env["res.config.settings"].create({})
        self.assertTrue(new_settings.livekit_enabled)
        self.assertEqual(new_settings.livekit_server_url, LIVEKIT_URL)
        self.assertEqual(new_settings.livekit_api_key, LIVEKIT_KEY)
