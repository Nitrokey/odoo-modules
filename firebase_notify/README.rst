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

**Step 2: Enable Browser Notifications**

**🔔 Real Firebase Integration (Recommended)**

1. In the Firebase Notifications section, click **"Enable Browser Notifications"**
2. **Allow notifications** when prompted by your browser
3. Your real Firebase token will be automatically generated and registered
4. Click **"Test Notification"** to verify it works
5. You should see an actual desktop notification appear!

**📱 Alternative Methods**

If you prefer to use mobile app tokens or manual entry:

- **Mobile App**: Install a Firebase-enabled mobile app and copy the token from app settings
- **Manual Entry**: Enter any Firebase token in the manual entry field
- **Test Tokens**: The system auto-generates test tokens for development

**Step 3: Test and Verify**

4. **Test Notifications**: Click the "Test Notification" button
5. **Check Desktop**: You should see a real browser notification
6. **Test Message Flow**: Send yourself a message in Odoo to test the complete flow

**🎯 What You'll Experience:**
- **Browser permission prompt**: "Allow notifications" dialog
- **Real desktop notifications**: Actual notifications that appear on your desktop
- **Background notifications**: Works even when Odoo tab is not active
- **Click actions**: Clicking notifications opens/focuses Odoo
- **Foreground alerts**: In-app notifications when Odoo is active

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
