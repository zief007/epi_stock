# -*- coding: utf-8 -*-
{
    "name": "epi_stock",
    "version": "16.0.1.0.0",
    "summary": "Gestion complète des EPI : agents, articles, mouvements, commandes, inventaires, tournées, statistiques et documents.",
    "description": (
        "Module V.E.T.E.S – Gestion des Équipements de Protection Individuelle.\n"
        "Fonctionnalités : gestion des agents, articles, mouvements, commandes, "
        "inventaires, tournées, statistiques et documents internes.\n"
        "Inclut un système de badges dynamiques sur les menus."
    ),
    "author": "Ville de Liège – Service Informatique",
    "website": "https://www.liege.be",
    "license": "LGPL-3",
    "category": "Hidden",

    "depends": [
        "base",
        "mail",
        "web",
        "stock",
    ],

    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",

        "data/epi_annee_selection_data.xml",

        "views/vetes_homepage_view.xml",
        "data/vetes_homepage_data.xml",

        "views/agent_views.xml",
        "views/article_views.xml",
        "views/article_category_views.xml",
        "views/batiment_views.xml",
        "views/commande_views.xml",
        "views/mouvement_views.xml",
        "views/inventory_views.xml",
        "views/inventory_line_views.xml",
        "views/epi_tournee_views.xml",
        "views/epi_mouvement_stats_views.xml",
        "views/document_views.xml",

        "views/actions.xml",
        "views/menu_views.xml",

        "data/server_actions.xml",
        "data/vetes_badges_cron.xml",

        "report/feuille_route_report.xml",
        "report/report_inventory_line.xml",
        "report/report_inventory_line_action.xml",
    ],

    "assets": {},

    "installable": True,
    "application": True,
    "auto_install": False,
}
