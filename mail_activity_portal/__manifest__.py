# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mail Activity on Messages over Portal",
    "version": "18.0.1.0.0",
    "category": "Social Network",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "license": "AGPL-3",
    "summary": """
    * If a messages arrives over the portal an activity for a
    configured team is scheduled automatically to process the message
    * The configuration to add RMA and PO models
    (Settings --> Technical --> Activity Teams menu)
    """,
    "depends": [
        "mail_activity_team",
        "portal",
    ],
    "installable": True,
}
