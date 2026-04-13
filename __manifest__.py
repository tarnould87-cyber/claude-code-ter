# -*- coding: utf-8 -*-
{
    'name': 'Devis - Mise en page A4 Premium',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Mise en page A4 professionnelle pour les devis et bons de commande',
    'description': """
        Ce module fournit une mise en page A4 professionnelle pour les devis et bons de commande.

        Fonctionnalités :
        - Design moderne avec palette de couleurs professionnelle
        - En-tête avec numéro, date et référence client
        - Barre de conditions commerciales (paiement, délai, incoterm, commercial)
        - Tableau des lignes avec numérotation, gestion des sections/notes et remises
        - Bloc totaux avec détail TVA
        - Section notes & conditions
        - Zone de signature pour les devis en cours
        - Compatible Odoo v18.0 / wkhtmltopdf
    """,
    'author': 'Custom',
    'depends': ['sale_management'],
    'data': [
        'views/report_saleorder_quotation.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
