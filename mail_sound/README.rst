========================
Mail Sound Notifications
========================

This module enhances Odoo's notification system by ensuring that sound notifications
are played for all incoming messages, regardless of the browser window's focus state,
and by giving a sound to the reminders of calendar meetings.

**Key Features:**

* Plays notification sounds even when the browser window has focus
* Works for channel messages, direct messages, and @mentions
* Filters out sounds for self-authored messages
* Plays a sound along with the reminder of a meeting
* Seamless integration with Odoo 18.0's service-based architecture

**Use Case:**

By default, Odoo only plays notification sounds when the browser window is out of focus.
This module ensures users never miss important messages by playing sounds in all cases,
providing better awareness of incoming communications.

Meeting reminders are silent in standard Odoo: a notification appears in the upper
right corner of the screen and nothing else happens. This module makes them audible
too, so an upcoming meeting is not missed while working in another part of Odoo.

**Table of contents**

.. contents::
   :local:

Configuration
=============

No configuration required. The module works automatically after installation.
