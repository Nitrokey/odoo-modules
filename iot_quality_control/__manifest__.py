# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "IoT Quality Control",
    "version": "18.0.1.0.0",
    "category": "IoT",
    "license": "AGPL-3",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "summary": "Post IoT device measurements as notes on the quality control "
    "of a manufacturing order",
    "depends": ["iot_input_oca", "iot_template_oca", "quality_control_mrp_oca"],
    "data": ["data/iot_template.xml"],
    "installable": True,
}
