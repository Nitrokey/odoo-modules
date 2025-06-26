======================
Firebase Notifications
======================

This module sends Firebase push notifications when users receive chat messages and inbox messages in Odoo.

Features
========

* **User-configurable**: Each user can enable/disable Firebase notifications in their profile
* **Firebase token management**: Users can set their Firebase device token in their preferences
* **Automatic notifications**: Sends push notifications for new chat and inbox messages
* **Disabled by default**: Firebase notifications are disabled by default for all users
* **Integration**: Works seamlessly with the firebase_integration module

Configuration
=============

1. Install the firebase_integration module first
2. Configure Firebase credentials in Settings > General Settings
3. Install this notify_firebase module
4. Users can enable notifications in their profile under Preferences

Usage
=====

For Users
---------

**Step 1: Enable Firebase Notifications**

1. Go to your user preferences (click on your name > Preferences)
2. Find the "Firebase Notifications" section
3. Check "Enable Firebase Notifications"

**Step 2: Register Your Browser for Notifications**

**Automatic Registration (Recommended)**

1. In the Firebase Notifications section, click **"Enable Browser Notifications"**
2. Allow notifications when prompted by your browser
3. Your Firebase token will be automatically registered with Odoo
4. You'll see a confirmation that notifications are enabled

**Manual Registration (Alternative)**

If automatic registration doesn't work, you can manually enter a Firebase token:

- **Mobile App**: Install a Firebase-enabled mobile app and copy the token from app settings
- **Web Browser**: Visit a Firebase-enabled website and copy the displayed token
- **Developer Tools**: Use browser console with ``messaging.getToken()``

**Step 3: Save and Test**

4. Save your preferences
5. Test by sending yourself a message in Odoo

**Important Notes:**
- **Browser-specific**: Each browser/device needs separate registration
- **Permission required**: You must allow browser notifications when prompted
- **Automatic updates**: Tokens are automatically refreshed when needed
- **Background notifications**: Works even when Odoo tab is not active

For Developers
--------------

The module automatically hooks into the mail.message creation process and sends Firebase notifications to users who have:

* Enabled Firebase notifications in their profile
* Configured a valid Firebase token
* Are recipients of the message (excluding the message author)

Technical Details
=================

* Extends res.users model to add firebase_token and firebase_notifications_enabled fields
* Overrides mail.message.create() to trigger Firebase notifications
* Supports both direct messages and channel messages
* Includes HTML stripping and message length limiting for notification body
* Comprehensive error handling and logging

Dependencies
============

* base
* mail
* firebase_integration

Author
======

IdeaCode Academy
