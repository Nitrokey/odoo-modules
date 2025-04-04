============================
Sale Order Picking Hold Paid
============================

This module adds a checkbox "Hold Picking Until Paid" to payment terms. If a sale order is validated with a payment term where this checkbox is enabled, the creation of the picking will be held until the invoice has been fully paid.

The creation of manufacturing orders is not blocked, allowing products with routes Make-to-order and Manufacturing to proceed with production even if delivery is on hold.

Features
--------

* Add "Hold Picking Until Paid" checkbox to payment terms
* Automatically hold delivery orders for sale orders with payment terms that have this option enabled
* Automatically create delivery orders when invoices are fully paid
* Allow manufacturing orders to be created even when delivery is on hold

Configuration
-------------

To configure this module, you need to:

1. Go to Accounting > Configuration > Payment Terms
2. Edit or create a payment term
3. Check the "Hold Picking Until Paid" checkbox if you want to hold deliveries until payment

Usage
-----

To use this module:

1. Create a sale order and select a payment term with "Hold Picking Until Paid" enabled
2. Confirm the sale order
3. Create and post an invoice for the sale order
4. No delivery order will be created until the invoice is fully paid
5. Once the invoice is paid, the delivery order will be automatically created

For products with Make-to-order and Manufacturing routes, manufacturing orders will be created immediately upon sale order confirmation, regardless of payment status.

Bug Tracker
-----------

Bugs are tracked on `GitHub Issues <https://github.com/Nitrokey/odoo-modules/issues>`_.
In case of trouble, please check there if your issue has already been reported.

Credits
-------

Authors
~~~~~~~

* Nitrokey GmbH

Contributors
~~~~~~~~~~~~

* Nitrokey GmbH <info@nitrokey.com>
