# © 2021 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Nitrokey: Partial picking from CSV',
    'version': '15.0.1.0.0',
    'category': 'Hidden',
    'author': 'initOS GmbH',
    'website': 'http://www.initos.com',
    'license': 'AGPL-3',
    'summary': """Import a CSV with delivery addresses to prepare pickings
    based on a sale order""",
    'depends': [
        "sale",
        "stock",
    ],
    'data': [
        'security/ir.model.access.csv',
        "wizards/partial_picking_wizard.xml",
    ],
    'installable': True,
}
