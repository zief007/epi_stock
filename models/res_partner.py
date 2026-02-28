# -*- coding: utf-8 -*-
"""
Extension : res.partner
------------------------------------------------------------
Objectif IT :
- fichier nécessaire pour déclarer l'héritage du modèle
- aucune surcharge, aucun champ ajouté
- garantit le chargement propre du module
"""

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"
    # Aucun champ ou méthode : héritage déclaré volontairement
