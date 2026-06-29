from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_studio_source_domain = fields.Char(
        compute='_compute_source_domain',
        store=False,
    )

    @api.depends_context('lang')
    def _compute_source_domain(self):
        # Cutoff: sale orders invoiced BEFORE this date are excluded
        cutoff = fields.Date.today() - relativedelta(months=3)
        # Show orders that are either:
        #   - not considered fully invoiced (status 'invoiced' AND 'upselling'
        #     both mean the order is fully invoiced), OR
        #   - have at least one invoice dated on or after the cutoff
        domain = str([
            '|',
            ('invoice_status', 'not in', ['invoiced', 'upselling']),
            ('invoice_ids.invoice_date', '>=', cutoff.strftime('%Y-%m-%d')),
        ])
        for record in self:
            record.x_studio_source_domain = domain
