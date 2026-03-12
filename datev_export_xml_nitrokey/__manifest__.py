# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "DATEV Export XML Nitrokey customization",
    "version": "18.0.1.0.0",
    "category": "Hidden",
    "author": "initOS GmbH, Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules/",
    "license": "AGPL-3",
    "summary": "DATEV export will contain sales order number instead of "
    "invoice number.",
    "depends": [
        "datev_export_xml",
    ],
    "data": [
        "templates/export_invoice_line.xml",
    ],
    "auto_install": True,
    "installable": True,
}
