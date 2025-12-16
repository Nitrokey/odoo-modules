====================
Mail Activity Portal
====================
This module adds an activity board with form, tree, kanban, calendar, pivot, graph and search views.


Usage
=====
If a messages arrives over the portal an activity for a configured team is scheduled automatically to process the message.

The configuration to add RMA and PO models (Settings --> Technical --> Activity Teams menu)


Testing
=======

Step 1:

1. Go to: "Settings" -> "Users & Companies" -> "Users" -> "+New" button
2. In the "Access Rights" tab, set the "User types" to "Portal"
3. Fill out all other necessary details to create a new testing account

Step 2:

1. Go to: "Settings" -> "Technical" -> "Activities" -> "Activity Teams" -> "+New"
2. Add the "admin account" in the "Members" section
3. Set the "Used models" at least to "Sales Order" (or any other portal-accessible models)
4. Fill out all other necessary details

Step 3:

In this case we are gonna use "Sales Order" as an example.

1. Open a browser window in incognito mode
2. Log into the testing account
3. Purchase an item in the online shop

Step 4:

1. Go back into the admin account and navigate to the "Sales Order" that was made with the testing account.
2. In the chatter panel on the right there should be an automatically generated activity under "Planned Activities"
