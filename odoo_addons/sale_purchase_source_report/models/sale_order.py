from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # 'x_studio_source' is the many2one (purchase.order -> sale.order) created
    # via Studio. This one2many only adds the reverse navigation, it does not
    # redefine the underlying column.
    x_studio_purchase_order_ids = fields.One2many(
        'purchase.order', 'x_studio_source',
        string="Achats liés (DDP / commandes fournisseurs)",
    )
    purchase_order_source_count = fields.Integer(
        string="Nb achats liés",
        compute='_compute_purchase_order_source_count',
    )

    def _compute_purchase_order_source_count(self):
        for order in self:
            order.purchase_order_source_count = len(order.x_studio_purchase_order_ids)

    def action_view_linked_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Achats liés à %s" % self.name,
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('x_studio_source', '=', self.id)],
        }
