=================
Mail ICE Security
=================

This module extends Odoo's WebRTC functionality to support both traditional username/password 
and secret-based authentication for ICE (STUN/TURN/TURNS) servers. It adds support for 
TLS-encrypted TURN servers (TURNS) and provides flexible authentication options.

Features
========

* **TURNS Protocol Support**: Adds support for TLS-encrypted TURN servers (turns:)
* **Dual Authentication**: Supports both username/password and secret-based authentication
* **Time-based HMAC**: Implements secure time-based HMAC authentication for secret-based servers
* **Realm Support**: Optional realm configuration for TURN server authentication
* **Automatic Protocol Selection**: WebRTC automatically chooses optimal transport (UDP/TCP)

Configuration
=============

1. Go to Settings > Technical > Discuss > ICE Servers
2. Create or edit an ICE server record
3. Configure the server based on your authentication method

Server Types
============

**STUN Server**
- **Type**: stun:
- **URI**: stun.example.com:3478
- **Authentication**: None required

**TURN Server (Unencrypted)**
- **Type**: turn:
- **URI**: turn.example.com:3478
- **Authentication**: Username/Password or Secret-based

**TURNS Server (TLS Encrypted)**
- **Type**: turns:
- **URI**: turn.example.com:443 or turn.example.com:5349
- **Authentication**: Username/Password or Secret-based
- **Transport**: Automatically uses TCP with TLS encryption

Port and Transport Configuration
================================

**Standard Ports:**
- **3478**: Standard TURN (UDP/TCP, unencrypted)
- **5349**: Standard TURNS (TCP with TLS)
- **443**: HTTPS port (TCP with TLS, firewall-friendly)

**URI Format:**
Configure the port as part of the URI: ``server.example.com:port``

**Transport Protocol Selection:**
- **Single Entry**: ``turn:server:port`` - WebRTC tries UDP first, falls back to TCP
- **Explicit Transport**: ``turn:server:port?transport=udp`` or ``turn:server:port?transport=tcp``
- **TLS (TURNS)**: Always uses TCP with TLS encryption

Authentication Methods
======================

**Method 1: Username/Password Authentication**
- **Username**: Static username provided by server administrator
- **Credential**: Static password provided by server administrator
- **Use case**: Traditional TURN server setups

**Method 2: Secret-based Authentication (Recommended)**
- **Secret**: Shared secret configured on both client and server
- **Username**: Auto-generated timestamp (current time + 1 hour validity)
- **Credential**: Auto-generated HMAC-SHA1 hash of username using secret
- **Use case**: Modern TURN servers (like coturn) with enhanced security

**Realm Configuration (Optional)**
- **Realm**: Domain or identifier required by some TURN servers
- **Common values**: server domain name, empty string, or specific realm
- **Example**: ``turn.example.com`` or ``example.com``

Configuration Examples
======================

**Example 1: Public STUN Server**
- **Type**: stun:
- **URI**: stun.l.google.com:19302
- **Authentication**: None

**Example 2: TURN Server with Username/Password**
- **Type**: turn:
- **URI**: turn.example.com:3478
- **Username**: myuser
- **Credential**: mypassword
- **Realm**: (optional)

**Example 3: TURN Server with Secret-based Authentication**
- **Type**: turn:
- **URI**: turn.example.com:3478
- **Secret**: mysecretkey123
- **Realm**: (optional)

**Example 4: TLS TURN Server (TURNS) on Port 443**
- **Type**: turns:
- **URI**: turn.example.com:443
- **Secret**: mysecretkey123
- **Realm**: (optional)
- **Benefits**: Encrypted, firewall-friendly (HTTPS port)

**Example 5: Dual Configuration for Maximum Compatibility**
Create two entries for the same server:

*Entry 1 (Fast UDP):*
- **Type**: turn:
- **URI**: turn.example.com:3478
- **Secret**: mysecretkey123

*Entry 2 (Secure TLS):*
- **Type**: turns:
- **URI**: turn.example.com:443
- **Secret**: mysecretkey123

Usage
=====

The module automatically handles authentication when WebRTC calls are initiated. 
No additional configuration is required once the ICE servers are properly configured.

**Authentication Priority:**
1. If **Secret** is provided: Uses time-based HMAC authentication
2. If **Username/Credential** is provided: Uses traditional authentication
3. **Secret takes precedence** if both are configured for the same entry

Technical Details
=================

**Secret-based Authentication:**
- **Username**: Generated as timestamp (current time + 1 hour validity)
- **Credential**: HMAC-SHA1 hash of username using secret as key
- **Validity**: Credentials automatically expire after 1 hour for security
- **Algorithm**: ``HMAC-SHA1(secret, timestamp)``

**Protocol Handling:**
- **STUN**: No authentication required
- **TURN**: Uses provided authentication method
- **TURNS**: Same as TURN but with mandatory TLS encryption

**WebRTC Transport Selection:**
- **turn: protocol**: UDP preferred, TCP fallback
- **turns: protocol**: TCP with TLS (UDP not possible with TLS)
- **Automatic**: WebRTC client chooses optimal transport based on network conditions

**Compatibility:**
- **coturn**: Full support for secret-based authentication
- **rfc5766-turn-server**: Username/password authentication
- **Cloud services**: Both authentication methods supported

Security Considerations
=======================

**Secret-based Authentication Benefits:**
- **Automatic credential rotation**: New credentials every hour
- **No static passwords**: Reduces credential theft risk
- **Time-limited access**: Credentials expire automatically
- **Server-side validation**: Server can verify timestamp validity

**TLS Encryption Benefits:**
- **Credential protection**: Authentication data encrypted in transit
- **Data privacy**: Media relay traffic encrypted
- **Firewall traversal**: Port 443 typically allowed through firewalls
- **Deep packet inspection**: Encrypted traffic appears as HTTPS

**Best Practices:**
- Use **TURNS (TLS)** for production environments
- Use **secret-based authentication** when supported by server
- Configure **realm** if required by your TURN server
- Use **port 443** for maximum firewall compatibility

Troubleshooting
===============

**Common Issues:**

*Authentication Errors:*
- Verify secret matches server configuration
- Check username/password if using traditional auth
- Ensure realm matches server requirements

*Connection Failures:*
- Test with both turn: and turns: protocols
- Verify port accessibility (firewall rules)
- Check server logs for allocation errors

*WebRTC Issues:*
- Use browser developer tools (chrome://webrtc-internals/)
- Look for ICE candidate generation
- Check for relay candidates (indicates TURN usage)

**Testing:**
Use browser console to test ICE server configuration:

.. code-block:: javascript

    const iceServers = [{
        urls: 'turns:turn.example.com:443',
        username: 'generated-timestamp',
        credential: 'generated-hmac'
    }];
    
    const pc = new RTCPeerConnection({ iceServers });
    pc.onicecandidate = (event) => {
        if (event.candidate) {
            console.log('ICE candidate:', event.candidate.candidate);
        }
    };
    pc.createOffer().then(offer => pc.setLocalDescription(offer));
