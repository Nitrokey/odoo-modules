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

1. Go to your user preferences (click on your name > Preferences)
2. Find the "Firebase Notifications" section
3. Check "Enable Firebase Notifications"
4. Enter your Firebase device token
5. Save your preferences

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
