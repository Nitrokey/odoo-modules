# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import hmac
import time

from odoo import fields, models


class MailIceServer(models.Model):
    _inherit = "mail.ice.server"

    # Replace username/password fields with secret
    secret = fields.Char(help="Secret for secret-based authentication")

    def _get_local_ice_servers(self):
        """
        Override to support secret-based authentication with time-based HMAC.
        :return: List of up to 5 dict, each representing a stun or turn server
        """
        # firefox has a hard cap of 5 ice servers
        ice_servers = self.sudo().search([], limit=5)
        formatted_ice_servers = []

        for ice_server in ice_servers:
            formatted_ice_server = {
                "urls": "%s:%s" % (ice_server.server_type, ice_server.uri),
            }

            # Use secret for authentication if provided
            if ice_server.secret:
                if ice_server.server_type == "turn":
                    # Generate time-based credentials for TURN servers
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
                # STUN servers typically don't need authentication credentials

            formatted_ice_servers.append(formatted_ice_server)

        return formatted_ice_servers
