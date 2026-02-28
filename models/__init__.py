# -*- coding: utf-8 -*-
"""
Initialisation des modèles du module epi_stock.
------------------------------------------------------------
Objectif IT :
- Odoo ne charge pas automatiquement les fichiers Python.
- Chaque modèle doit être importé explicitement ici.
- Ce fichier est le point d’entrée unique pour tous les modèles.
"""

# -------------------------------------------------------------
# Modèles métier principaux (structure EPI)
# -------------------------------------------------------------
from . import agent
from . import article
from . import article_category
from . import article_peremption
from . import batiment
from . import commande
from . import commande_line
from . import mouvement
from . import inventory
from . import inventory_line
from . import document

# -------------------------------------------------------------
# Modèles complémentaires
# -------------------------------------------------------------
from . import epi_annee_selection
from . import epi_tournee

# -------------------------------------------------------------
# Accueil statique
# -------------------------------------------------------------
from . import vetes_homepage

# -------------------------------------------------------------
# Badges sur les menus
# -------------------------------------------------------------
from . import ir_ui_menu_badges
from . import epi_badge_service

# -------------------------------------------------------------
# Extensions techniques
# -------------------------------------------------------------
from . import res_partner
from . import ir_http

# -------------------------------------------------------------
# Placeholder technique pour cohérence ORM
# -------------------------------------------------------------
from . import article_move
