===============================
Sale Order Default Payment Term
===============================

This module sets the first payment term as default when creating a new sales order.

Features
========

* Automatically sets the first payment term (ordered by ID) as the default payment term for new sales orders
* Overrides the payment_term_id field in the sale.order model to provide this default value

Configuration
=============

No special configuration is needed. After installing the module, the first payment term in the system will be automatically set as default for new sales orders. You can change the order of payment terms as usual.

Usage
=====

* When creating a new sales order, the payment term will be automatically set to the first payment term in the system
* Users can still manually change the payment term if needed

Testing
=======

The module includes unit tests to verify:

* The default payment term is correctly set when creating a new sales order
* Manually selected payment terms are respected
