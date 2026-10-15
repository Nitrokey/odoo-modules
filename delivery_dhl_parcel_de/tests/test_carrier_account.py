from unittest.mock import patch

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.delivery_dhl_parcel_de.models.carrier_account import CarrierAccount

from . import common


@tagged("post_install", "-at_install")
class TestCarrierAccount(common.DhlCommon):
    def test_get_access_token_success(self):
        """The token is stored and the OAuth2 request is built correctly."""
        self.account.dhl_access_token = False
        response = common.mock_response(200, {"access_token": "new-token"})
        with patch(common.ACCOUNT_REQUEST, return_value=response) as request:
            result = self.account.dhl_parcel_de_get_access_token()
        self.assertEqual(self.account.dhl_access_token, "new-token")
        self.assertEqual(result["effect"]["type"], "rainbow_man")
        method, url = request.call_args.args
        kwargs = request.call_args.kwargs
        self.assertEqual(method, "POST")
        self.assertEqual(url, f"{common.API_URL}/parcel/de/account/auth/ropc/v1/token")
        self.assertEqual(
            kwargs["data"],
            {
                "grant_type": "password",
                "username": "user",
                "password": "secret",
                "client_id": "key",
                "client_secret": "shh",
            },
        )
        self.assertEqual(
            kwargs["headers"]["Content-Type"], "application/x-www-form-urlencoded"
        )
        self.assertEqual(kwargs["timeout"], 30)

    def test_get_access_token_created_status(self):
        """HTTP 201 is accepted as success as well."""
        response = common.mock_response(201, {"access_token": "t201"})
        with patch(common.ACCOUNT_REQUEST, return_value=response):
            self.account.dhl_parcel_de_get_access_token()
        self.assertEqual(self.account.dhl_access_token, "t201")

    def test_get_access_token_http_error(self):
        """A non-2xx answer raises with the body and keeps the old token."""
        response = common.mock_response(401, text="invalid credentials")
        with (
            patch(common.ACCOUNT_REQUEST, return_value=response),
            self.assertRaises(ValidationError) as cm,
        ):
            self.account.dhl_parcel_de_get_access_token()
        self.assertIn("invalid credentials", str(cm.exception))
        self.assertEqual(self.account.dhl_access_token, "tok")

    def test_get_access_token_empty_token(self):
        """An empty access_token in a 200 answer is an error."""
        response = common.mock_response(200, {"access_token": ""})
        with (
            patch(common.ACCOUNT_REQUEST, return_value=response),
            self.assertRaises(ValidationError),
        ):
            self.account.dhl_parcel_de_get_access_token()
        self.assertEqual(self.account.dhl_access_token, "tok")

    def test_get_access_token_missing_key(self):
        """A malformed answer (no access_token key) becomes a ValidationError."""
        response = common.mock_response(200, {"error": "x"})
        with (
            patch(common.ACCOUNT_REQUEST, return_value=response),
            self.assertRaises(ValidationError),
        ):
            self.account.dhl_parcel_de_get_access_token()

    def test_get_access_token_connection_error(self):
        """Network failures are wrapped in a ValidationError."""
        with (
            patch(
                common.ACCOUNT_REQUEST,
                side_effect=requests.ConnectionError("no route"),
            ),
            self.assertRaises(ValidationError) as cm,
        ):
            self.account.dhl_parcel_de_get_access_token()
        self.assertIn("no route", str(cm.exception))

    def test_token_cron_refreshes_all_dhl_accounts(self):
        """The cron refreshes the token of every DHL account (and only those)."""
        dhl_accounts = self.env["carrier.account"].search(
            [("delivery_type", "=", "dhl_parcel_de_provider")]
        )
        self.assertIn(self.account, dhl_accounts)
        other = self.env["carrier.account"].create(
            {"name": "Other", "account": "1", "password": "x"}
        )
        with patch.object(
            CarrierAccount, "dhl_parcel_de_get_access_token", autospec=True
        ) as get_token:
            self.env["carrier.account"].dhl_parcel_de_get_access_token_cron()
        self.assertEqual(get_token.call_count, len(dhl_accounts))
        called = self.env["carrier.account"].browse(
            [call.args[0].id for call in get_token.call_args_list]
        )
        self.assertEqual(called, dhl_accounts)
        self.assertNotIn(other, called)
