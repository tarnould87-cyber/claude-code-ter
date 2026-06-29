from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    # Vrai lorsque la tâche liée est un Ordre de Fabrication (nom commençant
    # par "OF"). Sert à rendre le champ H. Préalables (x_studio_commande) non
    # saisissable dans ce cas, via une condition Studio fiable côté client.
    x_task_is_of = fields.Boolean(
        string="Tâche de type OF",
        compute='_compute_x_task_is_of',
        store=True,
    )

    @api.depends('task_id', 'task_id.name')
    def _compute_x_task_is_of(self):
        for line in self:
            name = (line.task_id.name or '').strip().upper()
            line.x_task_is_of = name.startswith('OF')
