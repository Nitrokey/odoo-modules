==============================================
DHL Parcel (Post & Parcel Germany) Integration
==============================================

This module provides integration with DHL Parcel Germany (Post & Parcel Germany) for Odoo.

Features
--------
* Create DHL Parcel DE shipments directly from Odoo
* Update tracking information in Odoo from DHL
* Generate and print shipping labels in Odoo

Instructions
------------
* For integration to work, you need the following information from DHL account:
  * account username
  * account password
  * API key

1. Enable DHL Parcel DE shipping: "Users & Companies" -> "Companies" -> select company -> "DHL Parcel DE Configuration"
2. Configure the DHL credentials: "DHL UserId", "DHL Password", "DHL API Key"
3. Configure DHL Parcel Delivery Method: "Inventory" -> "Configuration" -> "Delivery Methods" -> select provider "DHL Parcel DE" by setting all required fields
4. Publish delivery method on website if needed.

Testing
-------
For testing, you can use the following sandbox credentials (mentioned in official documentation):
* Username (UserID): user-valid
* Password: SandboxPasswort2023!
* API Key: FENtYydXijyFIG8a8aQIioOVhHgRaIYS

For shipment to generate correctly and avoid incorrect billing number error, you can use the following delivery method configuration:
* Product name: "V53WPAK-DHL Paket International"
* DHL Account number: "3333333333"
* DHL Procedure number: "53"
* DHL Participation number: "01"
You can find other working configurations of these parameters in the documentation: https://developer.dhl.com/api-reference/parcel-de-shipping-post-parcel-germany-v2#get-started-section/

=======

Credits
=======

Authors
~~~~~~~

* Vraja Technologies
* initOS GmbH

Contributors
~~~~~~~~~~~~

* Dmytro Kashuba <dmytro.kashuba@ext.initos.com>
