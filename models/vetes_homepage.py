# -*- coding: utf-8 -*-
"""
Modèle : vetes.homepage
------------------------------------------------------------
Objectif IT :
- fournir un enregistrement statique pour la page d’accueil V.E.T.E.S
- modèle minimal, sans logique métier
- structure stable et sans impact sur Odoo
"""

from odoo import models, fields


class VetesHomepage(models.Model):
    _name = "vetes.homepage"
    _description = "Page d'accueil V.E.T.E.S"
    _rec_name = "name"

    # Titre affiché dans la page d’accueil
    name = fields.Char(
        default="Accueil V.E.T.E.S",
        readonly=True
    )

    # Champ minimal pour permettre la création d’un enregistrement
    dummy = fields.Char(default="")
