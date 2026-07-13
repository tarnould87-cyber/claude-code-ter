{
    'name': "Suivi Achats par Commande Client",
    'version': '18.0.1.0.0',
    'summary': "Rapport listant, pour chaque commande client, les demandes de prix et commandes fournisseurs liées via le champ Source",
    'category': 'Sales/Purchase',
    'depends': ['sale', 'purchase'],
    'data': [
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'report/sale_purchase_report_templates.xml',
        'report/sale_purchase_report_actions.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
