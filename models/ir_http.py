# -*- coding: utf-8 -*-
"""
Extension : ir.http
------------------------------------------------------------
Objectif :
- déclencher la mise à jour des badges V.E.T.E.S
  immédiatement après l’authentification utilisateur.

Notes IT :
- surcharge minimale et sûre
- aucune modification du flux d’authentification
- utilise le service interne epi.badge.service
"""

from odoo import models, api


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def session_authenticate(cls, db, login, password, env):
        """Après login réussi → mise à jour des badges."""
        res = super().session_authenticate(db, login, password, env)

        if res.get('uid'):
            env['epi.badge.service'].run()

        return res
