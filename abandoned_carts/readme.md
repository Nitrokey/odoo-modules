Abandoned carts
===============

__Abandoned carts__ is a module for __Odoo__ which allows you to delete website
Quotations and  related partner records when those are older than a definable retention period.

Features supported:
* Configure a retention period of x hours (default: 48 hours)
* Specify a maximum of abandoned items to be deleted at a time (default: 2000 items) in order to avoid unresponsive server
* A log for reviewing purposes

Algorithm
=========

This module identifies orders as abandoned (and to be deleted) if all of the following is true:

`"state = __draft__" and "sales = website_sales" and "date_of_order <= hours_from_retention_period"`

These orders will be displayed in "Abandoned orders" and can be deleted manually. 
Customers, which have the 

`"orders = 0" and "lead = 0" and "meetings = 0" and "opportunities = 0" and "calls = 0" and "invoice = 0" and "tasks = 0" and "active = 0" and "is_customer = true"`

will be displayed in "Abandoned customers" and can be deleted manually.

If you setup the cron job, the abandoned_orders and abandoned_ customers will be deleted automaticly, depending on your setup.

Deleted items are listed with name, date, model & user in "Removed Log" for verification purposes.

Configuration
=============

Under Settings -> Configuration:Sales -> Retention Period you can set hours
and maximum abandoned items:

![Configuration](/abandoned_carts/images/1_settings.png)

__How to set automation (cron job) to delete orders?__

If we want to set an automation to remove orders, we have to go to settings -> Technical:Automation -> Scheduled Actions.

Type in Name, Interval Number, Next Execution Date and Inverval Unit. The cron job will be executed at Next Execution Date. In Number of calls you can determine how many intervals it has to run. 

For example:

"Number of calls = 1", "Interval Unit = Days" and "next Execution Date = 12/16/2019 15:45:44" means: It runs only one day beginning with this date.

"Number of calls = 7", "Interval Unit = Days" and "next Execution Date = 12/16/2019 15:45:44" means: It runs seven days beginning with this date.

"Number of calls is negative" means that this process will run every day. 

![Abandoned_customers](/abandoned_carts/images/6_cron_job.png)


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
