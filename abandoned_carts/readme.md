===============
Abandoned carts
===============

**Abandoned carts** is a Modul for **Odoo** which allows you to delete website
Quotations when those are older than x days.

Features supported:
    - set a retention period in x hours (48 hours are preset)
    - type in a maximum of abandoned items to delete at a time
      (2000 items are preset)
    - delete x items at a time
    - check if there are customers with 0 orders left
    - see abandoned log for checkup

Algorithm to set a retention Period (Settings -> Configuration: Sales -> Retention Period):
===========================================================================================

```python

    from openerp import models, fields, api
    from openerp.tools.safe_eval import safe_eval

    class SaleConfigSettings(models.TransientModel):
        _inherit='sale.config.settings'

        # you can set a retention period. 48 hours is by default
        order_retention_period = fields.Integer("Order older than X hours", default=48, help='Retention period for order. Afer X hours order are deleted automatically.')

        # user can delete a maximum of x records at one time (2000 is preset)
        max_delete_batch_limit = fields.Integer("Maximum record Delete limit", default=2000, help="User can delete maximum x records at a time.")

        @api.model
        # get the default values
        def get_default_order_retention_period(self, fields):
            # we use safe_eval on the result, since the value of the parameter is a nonempty string
            return {
            # get value for 'order_retention_period'
            'order_retention_period': safe_eval(self.env['ir.config_parameter'].get_param('abandoned_carts.order_retention_period', '48')),
            # get value for 'max_delete_batch_limit'
            'max_delete_batch_limit': safe_eval(self.env['ir.config_parameter'].get_param('abandoned_carts.max_delete_batch_limit', '2000')),
            }

            @api.multi
            # set values
            def set_order_retention_period(self):
                # set value for 'order_retention_period'
                self.env['ir.config_parameter'].set_param('abandoned_carts.order_retention_period', repr(self.order_retention_period))
                # set value for 'max_delete_batch_limit'
                self.env['ir.config_parameter'].set_param('abandoned_carts.max_delete_batch_limit', repr(self.max_delete_batch_limit))
```
Algorithm for the removed_record_log (Sales -> Abandoned Log: Removed Log):
===========================================================================

```python

    from openerp import models, fields

    class RemovedRecordLog(models.Model):
        _name = 'removed.record.log'

        # get the data form the current fields
        name = fields.Char(string='Name')
        date = fields.Datetime(string="Date")
        res_model = fields.Char('Model')
        res_id = fields.Integer('Record ID')
        user_id = fields.Many2one('res.users', string='User')
```
Configuration
=============



Usage
=====
