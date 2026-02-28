# -*- coding: utf-8 -*-
"""
Modèle : epi.article.move
Représente un mouvement de sortie d’article.

Ce modèle :
- enregistre les sorties d’EPI
- décrémente automatiquement le stock
- assure la traçabilité
"""

from odoo import models, fields, api
from odoo.exceptions import UserError


class EpiArticleMove(models.Model):
    _name = "epi.article.move"
    _description = "Mouvement de sortie d'article"
    _order = "date_move desc"

    # ---------------------------------------------------------
    # Champs principaux
    # ---------------------------------------------------------

    agent_id = fields.Many2one(
        "epi.agent",
        string="Agent",
        help="Agent ayant reçu l’article. Peut être vide pour un ajustement d’inventaire."
    )

    article_id = fields.Many2one(
        "epi.article",
        string="Article",
        required=True,
        help="Article concerné par le mouvement."
    )

    quantity = fields.Integer(
        string="Quantité",
        required=True,
        help="Quantité sortie ou ajustée."
    )

    date_move = fields.Date(
        string="Date du mouvement",
        default=fields.Date.today,
        required=True,
        help="Date à laquelle le mouvement a été effectué."
    )

    note = fields.Text(
        string="Remarque",
        help="Informations complémentaires sur le mouvement."
    )

    # ---------------------------------------------------------
    # Contraintes
    # ---------------------------------------------------------

    @api.constrains("quantity")
    def _check_quantity(self):
        """Empêche les quantités négatives ou nulles."""
        for move in self:
            if move.quantity <= 0:
                raise UserError("La quantité doit être strictement positive.")

    # ---------------------------------------------------------
    # Surcharge de create() pour décrémenter le stock
    # ---------------------------------------------------------

    @api.model
    def create(self, vals):
        """
        Lorsqu’un mouvement est créé :
        - vérifie que le stock est suffisant
        - décrémente automatiquement le stock
        """
        article = self.env["epi.article"].browse(vals["article_id"])
        qty = vals.get("quantity", 0)

        if article.stock < qty:
            raise UserError(
                f"Stock insuffisant pour l’article '{article.name}'. "
                f"Stock actuel : {article.stock}, demandé : {qty}."
            )

        article.stock -= qty

        return super().create(vals)
