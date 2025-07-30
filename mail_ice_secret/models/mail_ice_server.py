# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import hmac
import time

from odoo import fields, models


class MailIceServer(models.Model):
    _inherit = "mail.ice.server"

    # Extend server types to include TURNS (TLS)
    server_type = fields.Selection(
        [("stun", "stun:"), ("turn", "turn:"), ("turns", "turns:")],
        string="Type",
        required=True,
        default="stun",
    )

    # Add secret field for secret-based authentication (parallel to username/password)
    secret = fields.Char(help="Secret for secret-based authentication", password=True)

    # Add realm field for TURN server authentication
    realm = fields.Char(help="Realm for TURN server authentication (optional)")

    def _get_local_ice_servers(self):
        """
        Override to support both username/password and secret-based authentication.
        Also adds support for TURNS (TLS) protocol and realm configuration.
        :return: List of up to 5 dict, each representing a stun or turn server
        """
        # firefox has a hard cap of 5 ice servers
        ice_servers = self.sudo().search([], limit=5)
        formatted_ice_servers = []

        for ice_server in ice_servers:
            formatted_ice_server = {
                "urls": "%s:%s" % (ice_server.server_type, ice_server.uri),
            }

            # Handle authentication - prefer secret-based if available,
            # fallback to username/password
            if ice_server.secret and ice_server.server_type in ("turn", "turns"):
                # Secret-based authentication with time-based HMAC
                # Create timestamp-based username (valid for 1 hour)
                timestamp = int(time.time()) + 3600
                username = str(timestamp)

                # Generate HMAC-SHA1 credential using the secret
                credential = hmac.new(
                    ice_server.secret.encode("utf-8"),
                    username.encode("utf-8"),
                    hashlib.sha1,
                ).hexdigest()

                formatted_ice_server["username"] = username
                formatted_ice_server["credential"] = credential

            elif ice_server.username and ice_server.server_type in ("turn", "turns"):
                # Traditional username/password authentication
                formatted_ice_server["username"] = ice_server.username
                if ice_server.credential:
                    formatted_ice_server["credential"] = ice_server.credential

            # Add realm if specified (for both authentication methods)
            if ice_server.realm and ice_server.server_type in ("turn", "turns"):
                formatted_ice_server["realm"] = ice_server.realm

            formatted_ice_servers.append(formatted_ice_server)

        return formatted_ice_servers
