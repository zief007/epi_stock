# -*- coding: utf-8 -*-
"""
Modèle : epi.commande.line
------------------------------------------------------------
Ligne de commande EPI.

Fonctionnalités :
- lignes mères / filles (backorder)
- chaînage complet des réceptions
- historique des réceptions
- sécurisation des quantités
- cohérence avec epi.commande (réception partielle / totale)
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EpiCommandeLine(models.Model):
    _name = "epi.commande.line"
    _description = "Ligne de commande EPI"
    _order = "id"

    # ============================================================
    # RELATIONS
    # ============================================================
    commande_id = fields.Many2one(
        "epi.commande",
        string="Commande",
        required=True,
        ondelete="cascade",
        help="Commande à laquelle appartient cette ligne."
    )

    article_id = fields.Many2one(
        "epi.article",
        string="Article",
        required=True
    )

    parent_line_id = fields.Many2one(
        "epi.commande.line",
        string="Ligne précédente",
        ondelete="cascade",
        help="Chaînage : ligne mère ou ligne fille précédente."
    )

    child_line_ids = fields.One2many(
        "epi.commande.line",
        "parent_line_id",
        string="Historique"
    )

    # ============================================================
    # QUANTITÉS
    # ============================================================
    qty_commande = fields.Float(
        string="Qté commandée",
        required=True
    )

    qty_entree = fields.Float(
        string="Qté entrée",
        default=0.0,
        help="Quantité cumulée déjà reçue."
    )

    qty_recue = fields.Float(
        string="Qté reçue",
        default=0.0,
        help="Quantité reçue lors de l’opération en cours."
    )

    backorder_qty = fields.Float(
        string="Reliquat",
        default=0.0,
        help="Quantité restante à recevoir."
    )

    # ============================================================
    # ÉTAT / DATES
    # ============================================================
    date_reception_partielle = fields.Date(
        string="Date réception",
        help="Date de la dernière réception partielle."
    )

    # ------------------------------------------------------------
    # IT PRO : ligne terminée si backorder = 0 ET qty_entree > 0
    # ------------------------------------------------------------
    is_done = fields.Boolean(
        string="Terminé",
        compute="_compute_is_done",
        store=True,
        help="La ligne est terminée lorsque backorder = 0 et qu'au moins une quantité a été reçue."
    )

    @api.depends("backorder_qty", "qty_entree")
    def _compute_is_done(self):
        """
        IT PRO :
        - Une ligne est terminée si son reliquat = 0
        - ET si au moins une quantité a été réellement reçue.
        - Empêche les commandes 'terminées' alors que rien n'a été reçu.
        """
        for line in self:
            line.is_done = (line.backorder_qty == 0 and line.qty_entree > 0)

    remarque = fields.Char(string="Remarque")

    # ============================================================
    # CONTRÔLES AUTOMATIQUES
    # ============================================================
    @api.onchange("qty_recue")
    def _onchange_qty_recue(self):
        """Empêche la saisie de quantités négatives."""
        if self.qty_recue and self.qty_recue < 0:
            self.qty_recue = 0

    @api.constrains("qty_commande", "qty_entree")
    def _check_quantites(self):
        """Empêche les incohérences : entrée > commandée."""
        for line in self:
            if line.qty_entree > line.qty_commande:
                raise ValidationError(
                    "La quantité entrée ne peut pas dépasser la quantité commandée."
                )
