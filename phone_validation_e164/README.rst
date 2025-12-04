Phone Validation E164
=====================

This module enforces E.164 phone number formatting for `res.partner` records, overriding the default Odoo core behavior.
The module also adds logic to handle phone number formatting during website/API saves, guaranteeing consistency regardless of how records are created or updated.

Features
--------

- Overrides Odoo's phone validation to use E.164 format for phone and mobile fields.
- Applies E.164 formatting on both onchange and save actions (including website/API calls).
- Handles country-specific formatting using the `phonenumbers` library.

Dependencies
------------

- Odoo `phone_validation` module
- Python `phonenumbers` library

Author
------

Nitrokey GmbH
