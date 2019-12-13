Abandoned carts
===============

__Abandoned carts__ is a module for __Odoo__ which allows you to delete website
Quotations and  related partner records when those are older than a definable retention period.

Features supported:
* Configure a retention period of x hours (48 hours are default)
* Specify a maximum of abandoned items to be deleted at a time (2000 items are default) in order to avoid unresponsive server
* delete x items at a time
* check if there are customers with 0 orders left
* see abandoned log for checkup

Algorithm
=========

This module identifies orders as abandoned (and to be deleted) if all of the following is true:

"state = __draft__" and "sales = website_sales" and "date_of_order <= hours_from_retention_period"

These orders will be displayed in "Abandoned orders". If the user confirms the deletion, these orders will be marked for the cron job to remove these in the database. if the cron job is set for a particular time, the orders will be deleted completely and remains only in the "Removed Log. If the user delete several orders one more time, the orders will be append to the deleted orders in the "Removed Log". First after the order is deleted the customer is able to appear in "Abandoned customer"

If you setup in Settings -> Configuration:Sales -> Retention Period -> "max_delete_batch > 2000 and you try to remove these in "Abandoned Order" the folowing warning will be displayed "For safety reasons, you cannot delete more than %d sale orders together. You can re-open the wizard several times if needed."

Customers, which have the 

"status = __draft__" and "orders = 0" and "lead = 0" and "meetings = 0" and "opportunities = 0" and "calls = 0" and "newsletter = none" 

will be displayed in "Abandones customers". Customers have to be removed seperatly with the remove button. If they are removed, they will disappear from the database

Configuration
=============

Under Settings -> Configuration:Sales -> Retention Period you can set hours
and maximum abandoned items by typing:

![Configuration](/abandoned_carts/images/1_settings.png)

Usage
=====

__How to find removable orders with draft-status?__

go to Sales -> Abandoned Log:Abandoned Order. Now you can see a window like in the picture below. When you click
on the "bin" Symbol on the right side, you can skip the order from the removing-process. If you scoll down and click on the red remove button, all orders will be deleted from this view.

![Abandoned_order](/abandoned_carts/images/2_abandoned_order.png)

__How to see which data was deleted?__

go to Sales -> Abandoned Log:Removed Log. Now you can see a window like in the picture below. You can see here which orders have just been deleted. 

![Removed_Log](/abandoned_carts/images/3_removed_log.png)

You can export the data to a csv-file if you activate the check button on the left side and go to more -> export.

![export](/abandoned_carts/images/5_export.png)

__How to view and delete customers with zero orders?__

As soon as you have deleted the orders, customers will not be removed automatically. In order to do so
go to Sales -> Abandoned Log:Abandoned Customer. Now you can see a window like in the picture below. When you click
on the "bin" Symbol on the right side, you can skip the customer from the removing process. If you scoll down and can click on the red remove button, all customers will be deleted from this view.

![Abandoned_customers](/abandoned_carts/images/4_abandoned_customer.png)
