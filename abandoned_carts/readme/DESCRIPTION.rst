This module allows to delete Quotations and related partner records when those are older than a definable retention period.

Features:

* Configure a retention period of x hours (default: 48 hours)

* Specify a maximum of abandoned items to be deleted at a time (default: 2000 items) in order to avoid unresponsive server

* A log for reviewing purposes

Algorithm
=========

This module identifies orders as abandoned (and to be deleted) if all of the following is true:

`("state = draft" or "state = sent" or "state = cancelled") and "website_id is set" and "(current_time - create_date) < abandoned_carts.order_retention_period" and "create_uid = system_user"`

These orders will be displayed in "Abandoned orders" and can be deleted manually.

Customers, which have
`"lead = 0" and "meetings = 0" and "is_employee = false" and "helpdesk_tickets = 0" and "newsletter_subscriptions = 0" and "phonecalls = 0" and "orders = 0" and "account moves = 0" and "tasks = 0" and "portal or user account = 0" and "parent_id = NULL" and "is_company = false" and "create_uid = system_user" and "payment_transaction = 0"`

will be displayed in "Abandoned customers" and can be deleted manually.

Child partner records (e.g. delivery addresses) of deleted records will remain and don't get deleted implicitly. However, in subsequent executions they may fulfill all criteria and get deleted too.

A cron job can be configured to delete abandoned orders and abandoned customers automatically.

Deleted items are listed with name, date, model & user in "Removed Log" for verification purposes.

Configuration
=============

Under Settings -> Configuration -> Sales -> Retention Period set hours and maximum abandoned items:

.. image:: images/1_settings.png

**How to set automation (cron job) to delete orders?**

Go to settings -> Activate the developer mode, Technical: Automation -> Scheduled Actions.

Type in Name, Interval Number, Next Execution Date and Inverval Unit. The cron job will be executed at Next Execution Date. In Number of calls you can determine how many intervals it has to run.

For example:

"Number of calls = 1", "Interval Unit = Days" and "next Execution Date = 12/16/2019 15:45:44" means: It runs only one day beginning with this date.

"Number of calls = 7", "Interval Unit = Days" and "next Execution Date = 12/16/2019 15:45:44" means: It runs seven days beginning with this date.

"Number of calls is negative" means that this process will run every day.

.. image:: images/2_cron_job.png


Usage
=====

**How to find removable orders with draft-status?**

Go to Sales -> Abandoned Log: Abandoned Order. When you click on the "bin" Symbol on the right side, you can skip the order from the removing-process. If you scroll down and click on the red remove button, all listed orders will be deleted.

.. image:: images/3_abandoned_order.png

**How to see which data was deleted?**

Go to Sales -> Abandoned Log: Removed Log

.. image:: images/4_removed_log.png

You can export the data to a CSV file if you activate the check box on the left side and go to more -> export.

.. image:: images/5_export.png

**How to view and delete customers with zero orders?**

After deleting abandoned orders, customers will not be removed automatically. In order to do so go to Sales -> Abandoned Log: Abandoned Customer. When you click on the "bin" Symbol on the right side, you can skip the customer from the removing process. If you scroll down and click on the red remove button, all listed customers will be deleted.

.. image:: images/6_abandoned_customer.png
