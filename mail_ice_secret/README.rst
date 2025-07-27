==============================
Mail ICE Secret Authentication
==============================

This module extends Odoo's WebRTC functionality to support secret-based 
authentication for ICE (STUN/TURN) servers, replacing the traditional 
username/password authentication with a single secret.

Configuration
=============

1. Go to Settings > Technical > Discuss > ICE Servers
2. Create or edit an ICE server record
3. Enter the secret value in the Secret field

Usage
=====

The module automatically uses the secret for authentication when WebRTC calls 
are initiated. No additional configuration is required once the ICE servers 
are properly configured with their secrets.

Technical Details
=================

The module extends the ``mail.ice.server`` model to replace the ``username`` 
and ``credential`` fields with a single ``secret`` field for proper 
secret-based authentication.

For TURN servers, the module implements time-based HMAC authentication:

* **Username**: Generated as a timestamp (current time + 1 hour validity)
* **Credential**: HMAC-SHA1 hash of the username using the secret as key
* **Validity**: Credentials automatically expire after 1 hour for security

STUN servers typically don't require authentication credentials, so only 
the server URL is used for STUN entries.

This implementation follows the standard secret-based authentication pattern 
used by most TURN servers (like coturn) and provides automatic credential 
rotation for enhanced security.
