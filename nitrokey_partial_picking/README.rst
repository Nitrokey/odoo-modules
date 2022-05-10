# Partial Picking

This module allows for a given sales order to import delivery data via a CSV file which will automatically create a delivery order with the delivery address and amount.

Each sales manager will also see the "Partial pickings" button. This opens a wizard where you can upload the CSV file. When you press "Import" Odoo reads the CSV file, creates the delivery addresses if necessary and creates the corresponding delivery orders. This only works for sales orders with exactly one storable product. All delivery orders are created as drafts. Importing the same CSV twice will create delivery orders twice, as I have not included any additional checks.

The following must exist:

* Transaction type with the barcode: NK-DELIVERY (Warehouse > Configuration > Operation types).
* Sales order with exactly one storable product (service etc. are ignored)

The CSV needs to follow the format as shown in example.csv.
