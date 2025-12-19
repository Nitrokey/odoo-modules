===========================
Stock Lot/Serial No Default
===========================

This module modifies Odoo's default behavior for products tracked by serial numbers.

Problem
=======

In standard Odoo, when products are tracked by serial numbers, the system automatically:

* Picks an available serial number when reserving stock (clicking "Check Availability")
* Pre-fills this serial number in delivery orders, stock transfers, and manufacturing orders
* Proposes the serial number to staff without requiring conscious selection

This can lead to situations where staff processes transfers without verifying they have the correct physical item.

Solution
========

This module prevents automatic serial number selection while maintaining quantity reservation:

* **Quantities are still reserved** - inventory levels are correctly tracked
* **Serial numbers are NOT pre-filled** - fields remain empty after reservation
* **Staff must manually enter serial numbers** - ensures conscious selection of physical items
* **No validation added** - staff can still complete operations (following your workflow requirements)

Technical Details
=================

The module overrides the ``_update_reserved_quantity_vals`` method in ``stock.move`` model:

* For products with ``tracking='serial'``, the ``lot_id`` parameter is cleared
* Move lines are created without pre-assigned serial numbers
* Works for all stock operations: deliveries, transfers, and manufacturing orders

Configuration
=============

No configuration needed. The module works automatically for all products tracked by serial number.

Usage
=====

1. You may need to enable Settings -> inventory -> Lots & Serial Numbers
2. Create a product and set Track Inventory By Unique Serial Number
3. Create a delivery order / stock transfer / manufacturing order for serial-tracked products
4. Click "Check Availability" to reserve stock
5. The quantity will be reserved but serial number fields will be empty
6. Staff must manually scan or enter the serial number for each item
7. Validate the operation as usual
