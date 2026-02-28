# -*- coding: utf-8 -*-
"""
Modèle : epi.article.category
------------------------------------------------------------
Catégories d’articles EPI (hiérarchie parent → enfant).

Fonctionnalités :
- organisation des articles par catégories
- hiérarchie native Odoo (_parent_store)
- navigation optimisée via parent_path
- lien direct vers les articles associés
"""

from odoo import models, fields


# =====================================================================
#  MODÈLE : Catégorie d’article
# =====================================================================
class EpiArticleCategory(models.Model):
    """
    Catégorie d’article avec hiérarchie native Odoo :
    - parent_id / child_ids : structure arborescente
    - parent_path : géré automatiquement (optimisation des recherches)
    """

    _name = "epi.article.category"
    _description = "Catégorie d’article"
    _order = "name"

    # Active la gestion hiérarchique interne d’Odoo
    _parent_store = True
    _parent_name = "parent_id"

    # ---------------------------------------------------------
    # Champs principaux
    # ---------------------------------------------------------
    name = fields.Char(
        string="Nom de la catégorie",
        required=True,
        index=True,
        help="Nom de la catégorie (ex : Gants, Chaussures…)."
    )

    description = fields.Text(
        string="Description",
        help="Description facultative."
    )

    # ---------------------------------------------------------
    # Hiérarchie Catégorie → Sous-catégorie
    # ---------------------------------------------------------
    parent_id = fields.Many2one(
        "epi.article.category",
        string="Catégorie parente",
        ondelete="set null",
        index=True,
        help="Permet de structurer les catégories en hiérarchie."
    )

    child_ids = fields.One2many(
        "epi.article.category",
        "parent_id",
        string="Sous-catégories"
    )

    # Champ technique pour _parent_store
    parent_path = fields.Char(
        index=True,
        help="Chemin hiérarchique interne utilisé par Odoo."
    )

    # ---------------------------------------------------------
    # Relation avec les articles
    # ---------------------------------------------------------
    article_ids = fields.One2many(
        "epi.article",
        "category_id",
        string="Articles associés"
    )

    # ---------------------------------------------------------
    # Contraintes SQL
    # ---------------------------------------------------------
    _sql_constraints = [
        (
            "category_unique",
            "unique(name)",
            "Une catégorie portant ce nom existe déjà."
        ),
    ]
