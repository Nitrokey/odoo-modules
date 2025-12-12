============================
Sale Order Picking Hold Paid
============================

This module adds a dropdown field "Delivery Block Reason" to payment terms. If a sale order is validated with a payment term where a delivery block reason is selected, the creation of the picking will be held until the invoice has been fully paid.

The creation of manufacturing orders is not blocked, allowing products with routes Make-to-order and Manufacturing to proceed with production even if delivery is on hold.

Features
--------

* Add "Delivery Block Reason" dropdown to payment terms
* Add "Remove Block on Payment" checkbox to delivery block reasons for automatic removal upon payment
* Automatically hold delivery orders for sale orders with payment terms that have a delivery block reason selected
* Automatically create delivery orders when invoices are fully paid (if the block reason has "Remove Block on Payment" enabled)
* Allow manufacturing orders to be created even when delivery is on hold

Configuration
-------------

To configure this module, you need to:

1. Go to Accounting > Configuration > Payment Terms
2. Edit or create a payment term
3. Select a "Delivery Block Reason" from the dropdown if you want to hold deliveries until payment
4. On the delivery block reason itself, enable "Remove Block on Payment" if you want the block to be automatically removed when the invoice is paid

Usage
-----

To use this module:

1. Create a sale order and select a payment term with a "Delivery Block Reason" selected
2. Confirm the sale order
3. Create and post an invoice for the sale order
4. No delivery order will be created until the invoice is fully paid
5. Once the invoice is paid, the delivery order will be automatically created if the block reason has "Remove Block on Payment" enabled

For products with Make-to-order and Manufacturing routes, manufacturing and delivery orders will be created immediately upon sale order confirmation, regardless of payment status.

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
* Dmytro Kashuba <dmytro.kashuba@ext.initos.com>
