==============================================
DHL Parcel (Post & Parcel Germany) Integration
==============================================

This module provides integration with DHL Parcel Germany (Post & Parcel Germany) for Odoo.

Features
--------
* Create DHL Parcel DE shipments directly from Odoo
* Update tracking information in Odoo from DHL
* Generate and print shipping labels in Odoo
* Deliver to DHL Packstations (lockers)

Note that shipping rates are not retrieved from DHL but need to be configured.

Packstation (Locker) Delivery
------------------------------

To ship to a DHL Packstation, set the recipient's address fields as follows:

* **Street 1**: The recipient's DHL post number (8-digit customer number).
* **Street 2**: ``Packstation <lockerID>``, e.g. ``Packstation 183`` or ``Packstation: 183`` (case-insensitive).
* **ZIP / City / Country**: The Packstation's postal address.

The module detects the keyword ``Packstation`` in Street 2 and automatically
sends a locker-addressed shipment request to DHL instead of a regular contact
address.

Configuration
-------------

Create Delivery Methods
^^^^^^^^^^^^^^^^^^^^^^^

1. "Inventory" -> "Configuration" -> "Delivery" -> "Delivery Methods"
2. Select or create a method
3. Set the "Provider" to "DHL Parcel DE"
4. Select or create an 'Account'.
   1. Choose the Delivery Type 'DHL Parcel DE' in the Account form view to display the DHL fields

   2. Fill in the necessary information in the 'Account' form. The values below are for testing purposes only:

      * DHL API URL: ``https://api-sandbox.dhl.com``
      * DHL UserId: ``user-valid``
      * DHL Password: ``SandboxPasswort2023!``
      * DHL Account number: ``3333333333`` (sandbox account)
      * DHL API Key: Add your own API key here
      * DHL API Secret: Add your own API secret here
      * DHL Tracking URL: (optional) Leave empty or use: ``https://www.dhl.de/en/privatkunden/pakete-empfangen/verfolgen.html?piececode=``

5. Fill out the necessary information. The information below is only meant as an example:

   * Company: Company Name
   * DHL Weight UOM: ``KG``
   * DHL Services Name: ``V53WPAK-DHL Paket``
   * DHL Procedure number: ``01``
   * DHL Participation number: ``02``
   * DHL Package Info: Create package type

     1. Click "Create"
     2. Fill in package details:

        * Package Type Name: ``DHL Parcel DE``
        * Carrier Code: e.g., ``DHL-Paket``
        * Height: e.g., ``5.00`` cm
        * Width: e.g., ``5.00`` cm
        * Length: e.g., ``5.00`` cm
        * Weight: e.g., ``0.5`` kg
        * Max Weight: e.g., ``10.00`` kg

     3. Save your changes

6. Save your changes


Testing
-------

1. Create a Sales Order
^^^^^^^^^^^^^^^^^^^^^^^

1. "Sales" -> "Orders" -> "Quotations" -> "+New"
2. Fill out the necessary information
3. "Add Shipping" button -> set "Shipping Method" as "DHL Parcel DE" -> "Get Rate" button -> "Add" button -> "Confirm" button

2. Create Delivery Order
^^^^^^^^^^^^^^^^^^^^^^^^

1. Click the "Delivery" button at the top of the panel in the sales order
2. In the delivery order, set the shipping details:

   * "Carrier" is set to your DHL Parcel DE method
   * Ensure products have a weight configured

3. "Validate" button -> set "Number Of Packages" to minimum 1 -> "Apply" button
4. In the "Additional Info" tab, there should be a field called "Tracking Reference" (shows the shipment number for the product)
5. At the top of the panel, look for the "Tracking" button (it will take you to the DHL tracking section)
6. At the top of the panel, look for the "Valuation" button (it will display the minused quantities)


Credits
-------

Authors
^^^^^^^

* Vraja Technologies
* initOS GmbH
* Nitrokey GmbH

Contributors
^^^^^^^^^^^^

* Dmytro Kashuba <dmytro.kashuba@ext.initos.com>
