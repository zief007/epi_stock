# -*- coding: utf-8 -*-
"""
Modèle : epi.inventory.line
------------------------------------------------------------
Ligne d’inventaire EPI.

Fonctionnalités :
- cohérence totale avec epi.inventory
- stock réel = 0 par défaut
- calcul automatique de l’écart
- statut visuel dynamique
- impression PDF via report_action
"""

from odoo import models, fields, api
from odoo.exceptions import UserError


class EpiInventoryLine(models.Model):
    _name = "epi.inventory.line"
    _description = "Ligne d’inventaire"
    _order = "id"

    # ============================================================
    # RELATIONS
    # ============================================================
    inventory_id = fields.Many2one(
        "epi.inventory",
        required=True,
        ondelete="cascade"
    )

    article_id = fields.Many2one(
        "epi.article",
        required=True
    )

    # ============================================================
    # DONNÉES DE STOCK
    # ============================================================
    stock_theorique = fields.Integer(default=0)
    stock_reel = fields.Integer(default=0)

    ecart = fields.Integer(
        compute="_compute_ecart",
        store=True
    )

    remarque = fields.Char()

    # ============================================================
    # STATUT VISUEL
    # ============================================================
    status_display = fields.Char(
        compute="_compute_status_display",
        store=False
    )

    @api.depends("inventory_id.state")
    def _compute_status_display(self):
        """Affiche 'Validé' si l’inventaire parent est validé."""
        for rec in self:
            rec.status_display = "Validé" if rec.inventory_id.state == "done" else ""

    # ============================================================
    # CALCUL AUTOMATIQUE DE L’ÉCART
    # ============================================================
    @api.depends("stock_theorique", "stock_reel")
    def _compute_ecart(self):
        """Écart = stock réel - stock théorique."""
        for rec in self:
            rec.ecart = (rec.stock_reel or 0) - (rec.stock_theorique or 0)

    # ============================================================
    # IMPRESSION PDF
    # ============================================================
    def print_inventory_line(self):
        """Retourne l’action PDF définie dans report_inventory_line_action.xml."""
        self.ensure_one()

        if not self.article_id:
            raise UserError("Aucun article défini pour cette ligne d’inventaire.")

        return self.env.ref("epi_stock.report_inventory_line").report_action(self)
