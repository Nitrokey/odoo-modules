Abandoned carts
===============

__Abandoned carts__ is a module for __Odoo__ which allows you to delete website
Quotations and  related partner records when those are older than a definable retention period.

Features supported:
* Configure a retention period of x hours (48 hours are default)
* Specify a maximum of abandoned items to be deleted at a time (2000 items are default) in order to avoid unresponsive server
* A log for reviewing purposes

Algorithm
=========

This module identifies orders as abandoned (and to be deleted) if all of the following is true:

"state = __draft__" and "sales = website_sales" and "date_of_order <= hours_from_retention_period"

These orders will be displayed in "Abandoned orders" and can be deleted manually. If you setup the cron job, the abandoned_orders and abandoned_ customers will be deleted automaticly, depending on your setup.

Customers, which have the 

"status = __draft__" and "orders = 0" and "lead = 0" and "meetings = 0" and "opportunities = 0" and "calls = 0" and "newsletter = none" and "date_of_order <= hours_from_retention_period"

will be displayed in "Abandoned customers" and can be deleted manually.

Deleted items are listed with name, date, model & user in "Removed Log" for verification purposes.

Order_retention_period is set as default = 48 hours
max_delete_batch_limit is set by default = 2000 items

When you change Order_retention_period and max_delete_batch_limit, then this value will change and affect "abandoned_orders" and "abandoned_customers".

Configuration
=============

Under Settings -> Configuration:Sales -> Retention Period you can set hours
and maximum abandoned items:

![Configuration](/abandoned_carts/images/1_settings.png)

Usage
=====

__How to find removable orders with draft-status?__

go to Sales -> Abandoned Log:Abandoned Order. Now you can see a window like in the picture below. When you click
on the "bin" Symbol on the right side, you can skip the order from the removing-process. If you scroll down and click on the red remove button, all orders will be deleted.

![Abandoned_order](/abandoned_carts/images/2_abandoned_order.png)

__How to see which data was deleted?__

go to Sales -> Abandoned Log:Removed Log. Now you can see a window like in the picture below. You can see here which orders have just been deleted. 

![Removed_Log](/abandoned_carts/images/3_removed_log.png)

You can export the data to a csv-file if you activate the check button on the left side and go to more -> export.

![export](/abandoned_carts/images/5_export.png)

__How to view and delete customers with zero orders?__

As soon as you have deleted the orders, customers will not be removed automatically. In order to do so
go to Sales -> Abandoned Log:Abandoned Customer. Now you can see a window like in the picture below. When you click
on the "bin" Symbol on the right side, you can skip the customer from the removing process. If you scroll down and click on the red remove button, all customers will be deleted.

![Abandoned_customers](/abandoned_carts/images/4_abandoned_customer.png)
