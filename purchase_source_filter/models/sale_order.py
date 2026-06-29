from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        # When opened from the purchase 'Source' field, sort the dropdown by
        # reference number descending (most recent first) without affecting
        # the default ordering of sale orders elsewhere.
        if self.env.context.get('source_order_desc') and not order:
            order = 'name desc'
        return super()._name_search(
            name, domain=domain, operator=operator, limit=limit, order=order,
        )
