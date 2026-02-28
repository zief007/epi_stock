# -*- coding: utf-8 -*-
"""
Modèle : epi.article.move (OBSOLÈTE)
------------------------------------------------------------
Ancien modèle conservé uniquement pour compatibilité.

Objectif :
- empêcher toute création d’enregistrements
- éviter les erreurs ORM si des données historiques existent encore

NOTE IT :
- Ne pas supprimer ce modèle tant que les bases de production
  n'ont pas été vérifiées (risque de références résiduelles).
"""

from odoo import models
from odoo.exceptions import UserError


class EpiArticleMove(models.Model):
    _name = "epi.article.move"
    _description = "Ancien modèle (désactivé)"

    # ---------------------------------------------------------
    # Blocage total de la création
    # ---------------------------------------------------------
    def create(self, vals):
        raise UserError(
            "Ce modèle est obsolète. "
            "Utilisez le menu 'Mouvements d’EPI' basé sur epi.mouvement."
        )
