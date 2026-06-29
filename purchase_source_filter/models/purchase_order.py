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
        today = fields.Date.today()
        cutoff_invoice = today - relativedelta(months=3)
        cutoff_quotation = today - relativedelta(months=8)
        # Keep an order only if BOTH blocks are true:
        #   1. Invoice block: not considered fully invoiced ('invoiced' and
        #      'upselling' both mean fully invoiced), OR an invoice dated within
        #      the last 3 months.
        #   2. Quotation block: not a draft/sent quotation, OR ordered within
        #      the last 8 months.
        domain = str([
            '&',
            '|',
            ('invoice_status', 'not in', ['invoiced', 'upselling']),
            ('invoice_ids.invoice_date', '>=', cutoff_invoice.strftime('%Y-%m-%d')),
            '|',
            ('state', 'not in', ['draft', 'sent']),
            ('date_order', '>=', cutoff_quotation.strftime('%Y-%m-%d')),
        ])
        for record in self:
            record.x_studio_source_domain = domain
