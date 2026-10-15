from odoo.exceptions import AccessDenied
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDisablePassword(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password = "Sup3r-secret-pw!"
        cls.user = cls.env["res.users"].create(
            {
                "name": "OAuth Test User",
                "login": "oauth_test_user",
                "password": cls.password,
            }
        )

    def _token_vals(self, token):
        """Values to create a user with an OAuth token"""
        # auth_oauth_multi_token replaces the single token by a list of tokens
        if "oauth_access_token_ids" in self.env["res.users"]._fields:
            return {"oauth_access_token_ids": [(0, 0, {"oauth_access_token": token})]}
        return {"oauth_access_token": token}

    def _set_oauth_token(self, user, token="some-token"):
        if "oauth_access_token_ids" in user._fields:
            self.env["auth.oauth.multi.token"].create(
                {"user_id": user.id, "oauth_access_token": token}
            )
        else:
            user.oauth_access_token = token

    def _clear_oauth_token(self, user):
        if "oauth_access_token_ids" in user._fields:
            user.oauth_access_token_ids.unlink()
        else:
            user.oauth_access_token = False

    def _check_password(self, user, password=None):
        return user.with_user(user)._check_credentials(
            {"type": "password", "password": password or self.password},
            {"interactive": True},
        )

    def test_default_not_disabled(self):
        """Users without OAuth token can log in with their password"""
        self.assertFalse(self.user.disable_password_login)
        self.assertTrue(self.user._crypt_context())
        result = self._check_password(self.user)
        self.assertEqual(result["uid"], self.user.id)

    def test_compute_from_token(self):
        """Setting or removing the OAuth token toggles the flag"""
        self._set_oauth_token(self.user)
        self.assertTrue(self.user.disable_password_login)
        self._clear_oauth_token(self.user)
        self.assertFalse(self.user.disable_password_login)

    def test_create_with_token(self):
        """Users created with a token have the password login disabled"""
        user = self.env["res.users"].create(
            {
                "name": "OAuth Token User",
                "login": "oauth_token_user",
                **self._token_vals("another-token"),
            }
        )
        self.assertTrue(user.disable_password_login)

    def test_password_login_blocked(self):
        """Password checks are denied if the password login is disabled"""
        self._set_oauth_token(self.user)
        with self.assertRaises(AccessDenied):
            self.user._crypt_context()
        with self.assertRaises(AccessDenied):
            self._check_password(self.user)

    def test_password_login_blocked_manually(self):
        """The flag can be set manually without any OAuth token"""
        self.assertFalse(self.user.disable_password_login)
        self.user.disable_password_login = True
        self.assertTrue(self.user.disable_password_login)
        with self.assertRaises(AccessDenied):
            self._check_password(self.user)

    def test_password_login_reenabled(self):
        """Resetting the flag manually restores password login"""
        self._set_oauth_token(self.user)
        self.user.disable_password_login = False
        self.assertFalse(self.user.disable_password_login)
        result = self._check_password(self.user)
        self.assertEqual(result["uid"], self.user.id)

    def test_other_users_unaffected(self):
        """Only the user with the flag set is blocked"""
        other = self.env["res.users"].create(
            {
                "name": "Other User",
                "login": "oauth_other_user",
                "password": self.password,
            }
        )
        self._set_oauth_token(self.user)
        self.assertFalse(other.disable_password_login)
        self.assertTrue(other._crypt_context())
        result = self._check_password(other)
        self.assertEqual(result["uid"], other.id)

    def test_wrong_password_still_denied(self):
        """Wrong passwords are denied for users with password login enabled"""
        with self.assertRaises(AccessDenied):
            self._check_password(self.user, "wrong-password")
