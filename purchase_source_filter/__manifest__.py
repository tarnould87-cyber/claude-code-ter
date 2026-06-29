{
    'name': 'Purchase Source Field Filter',
    'version': '18.0.1.0.0',
    'summary': 'Restreint le champ Source des achats aux commandes ventes non facturées depuis plus de 3 mois',
    'author': 'Technique et Réalisation',
    'category': 'Purchase',
    'depends': ['purchase', 'sale', 'hr_timesheet'],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
