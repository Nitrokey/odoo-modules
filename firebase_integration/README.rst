====================
Firebase Integration
====================

This module provides Firebase integration for Odoo, allowing administrators to configure Firebase credentials through the Odoo interface and enabling other modules to send Firebase push notifications.

Features
========

* **Admin-configurable**: Firebase credentials can be configured through Odoo's Settings interface
* **Database storage**: Firebase service account credentials stored securely in the database
* **Easy setup**: Upload Firebase JSON credentials file through the web interface
* **Integration ready**: Provides tools for other modules to send Firebase notifications
* **Multiple configurations**: Support for multiple Firebase configurations with active/inactive states

Configuration
=============

1. Go to **Settings > General Settings**
2. Find the **Firebase Integration** section
3. Upload your Firebase service account private key JSON file
4. Save the configuration

Alternatively, you can manage Firebase configurations through:
**Settings > Technical > Firebase Configuration**

Usage for Developers
====================

Other modules can use this integration to send Firebase notifications:

.. code-block:: python

    from odoo.addons.firebase_integration.tools.firebase import send_firebase_notifications

    messages = [
        {'token': 'device_token', 'body': 'Message body', 'title': 'Message title'},
        {'token': 'device_token2', 'body': 'Another message', 'title': 'Another title'}
    ]
    
    # Pass the environment to the function
    success_count = send_firebase_notifications(messages, self.env)

Technical Details
=================

* Extends res.config.settings to add Firebase configuration fields
* Provides firebase.config model for storing multiple configurations
* Includes proper access rights for system administrators
* Comprehensive error handling and logging
* Supports Firebase Admin SDK for Python

Dependencies
============

* base
* bus

External Dependencies
=====================

* firebase-admin (Python package)

Installation
============

1. Install the firebase-admin Python package: ``pip install firebase-admin``
2. Install this module in Odoo
3. Configure your Firebase credentials through Settings

Author
======

IdeaCode Academy

License
=======

LGPL-3
