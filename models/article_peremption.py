# -*- coding: utf-8 -*-
"""
Modèle : epi.article.peremption
------------------------------------------------------------
Dates de péremption associées à un article.

Fonctionnalités :
- plusieurs dates possibles par article
- gestion simple : ajout / suppression libre
"""

from odoo import models, fields


class EpiArticlePeremption(models.Model):
    _name = "epi.article.peremption"
    _description = "Date de péremption d'un article"
    _order = "date_peremption"

    # ---------------------------------------------------------
    # Article concerné
    # ---------------------------------------------------------
    article_id = fields.Many2one(
        "epi.article",
        string="Article",
        required=True,
        ondelete="cascade",   # Suppression sécurisée des dates liées
        help="Article auquel cette date de péremption est liée."
    )

    # ---------------------------------------------------------
    # Date de péremption
    # ---------------------------------------------------------
    date_peremption = fields.Date(
        string="Date de péremption",
        required=True,
        help="Date à laquelle le lot ou l’article devient périmé."
    )
