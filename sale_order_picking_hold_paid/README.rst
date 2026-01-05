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

1. Go to: "Accounting" -> "Configuration" -> "Invoicing" -> "Payment Terms"
2. Edit or create a payment term
3. In the "Delivery Block Reason" field choose or create an option and
4. Expand the option that you choose
5. In the expanded view you will see the "Remove Block on Payment" option; enable it

Usage
-----

1. Go to: "Sales" -> "Orders" -> "Orders" -> "+New"
2. In the "Payment Terms" field make sure that the option you choose has "Remove Block on Payment" enabled
3. Confirm the sale order
4. Create the invoice and then confirm it
5. The delivery order will not be created until the invoice is fully paid
6. Once the invoice is paid go back into the sale order section
7. The delivery order will be automatically created if the "Delivery Block Reason" field that has the option selected with the "Remove Block on Payment" enabled

For products with Make-to-order (MTO) and Manufacturing routes enabled, manufacturing and delivery orders will be created upon clicking "Release Delivery Block" on Sale Order, regardless of payment status.

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
