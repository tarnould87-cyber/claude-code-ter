from odoo import api, fields, models
from odoo.exceptions import ValidationError


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

    @api.constrains('unit_amount', 'project_id')
    def _check_timesheet_unit_amount_positive(self):
        # Impose une durée strictement positive sur les lignes de feuille de
        # temps (rattachées à un projet). On ignore les minuteurs en cours,
        # qui créent volontairement une ligne à 0 jusqu'à leur arrêt.
        for line in self:
            if not line.project_id:
                continue
            if getattr(line, 'timer_start', False):
                continue
            if line.unit_amount <= 0:
                raise ValidationError(
                    "Le temps passé doit être supérieur à 0 sur une feuille "
                    "de temps."
                )
