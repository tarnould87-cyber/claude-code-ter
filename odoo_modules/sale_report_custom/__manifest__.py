{
    'name': 'Rapport Ventes Personnalisé',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Rapport QWeb personnalisé pour Devis et Bons de Commande',
    'description': """
        Module de personnalisation du rapport de ventes (Devis / Bon de commande).
        - En-tête avec numéro de document stylisé
        - Bloc d'informations (date, validité, vendeur, référence client, délai, incoterm, paiement)
        - Tableau de lignes avec alternance de couleurs
        - Total en bandeau foncé
    """,
    'author': 'TER',
    'depends': ['sale'],
    'data': [
        'report/sale_report_custom.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
