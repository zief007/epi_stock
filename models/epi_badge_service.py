# -*- coding: utf-8 -*-
"""
Service interne : mise à jour des badges V.E.T.E.S
------------------------------------------------------------
Appelé par l'action serveur (elle-même appelée par le cron).

Objectifs IT :
- encapsuler l'appel à ir.ui.menu.update_vetes_badges()
- éviter toute logique dans le cron
- architecture propre, stable et maintenable
"""

from odoo import models


class EpiBadgeService(models.TransientModel):
    _name = "epi.badge.service"
    _description = "Service interne pour mise à jour des badges"

    def run(self):
        """
        Méthode appelée par l'action serveur.
        Déclenche la mise à jour des badges du menu.
        """
        self.env['ir.ui.menu'].update_vetes_badges()
