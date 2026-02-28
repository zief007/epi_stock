# -*- coding: utf-8 -*-
"""
Modèle : epi.article
------------------------------------------------------------
Gère :
- articles EPI / vêtements
- péremption (dates multiples)
- seuils d’alerte
- commandes en cours (corrigé : uniquement si reliquat > 0)
- recherche intelligente (code + nom)
- tri prioritaire : périmés → sous seuil → autres
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EpiArticle(models.Model):
    _name = "epi.article"
    _description = "Article EPI / vêtement"

    # ---------------------------------------------------------
    # Ordre d'affichage prioritaire
    # ---------------------------------------------------------
    _order = "is_expired desc, is_below_threshold desc, name asc"

    # ---------------------------------------------------------
    # Affichage ergonomique dans les Many2one
    # ---------------------------------------------------------
    display_name = fields.Char(
        compute="_compute_display_name",
        store=False
    )

    @api.depends('code', 'name')
    def _compute_display_name(self):
        """Affiche : CODE - Nom."""
        for rec in self:
            if rec.code and rec.name:
                rec.display_name = f"{rec.code} - {rec.name}"
            else:
                rec.display_name = rec.name or rec.code or ""

    # ---------------------------------------------------------
    # Champs principaux
    # ---------------------------------------------------------
    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)

    @api.constrains("code")
    def _check_code_unique(self):
        """Numéro d’article unique (contrôle Python)."""
        for rec in self:
            if rec.code:
                exists = self.search([
                    ("code", "=", rec.code),
                    ("id", "!=", rec.id)
                ], limit=1)
                if exists:
                    raise ValidationError("Ce numéro d’article est déjà utilisé.")

    stock = fields.Integer(default=0)
    seuil_alerte = fields.Integer(default=0)
    emplacement = fields.Char()
    remarque = fields.Text()

    # ---------------------------------------------------------
    # Péremption
    # ---------------------------------------------------------
    perissable = fields.Boolean()
    peremption_ids = fields.One2many("epi.article.peremption", "article_id")

    is_expired = fields.Boolean(
        compute="_compute_is_expired",
        store=True,
        help="True si au moins une date de péremption est dépassée."
    )

    @api.depends('perissable', 'peremption_ids.date_peremption')
    def _compute_is_expired(self):
        """Détermine si l’article est périmé."""
        today = fields.Date.today()
        for rec in self:
            rec.is_expired = bool(
                rec.perissable and any(
                    p.date_peremption and p.date_peremption <= today
                    for p in rec.peremption_ids
                )
            )

    # ---------------------------------------------------------
    # Seuil d’alerte
    # ---------------------------------------------------------
    is_below_threshold = fields.Boolean(
        compute="_compute_is_below_threshold",
        store=True,
        help="True si stock <= seuil d’alerte."
    )

    @api.depends('stock', 'seuil_alerte')
    def _compute_is_below_threshold(self):
        """Détermine si l’article est sous le seuil d’alerte."""
        for rec in self:
            rec.is_below_threshold = (
                rec.seuil_alerte > 0 and rec.stock <= rec.seuil_alerte
            )

    # ---------------------------------------------------------
    # Compteur global (dashboard)
    # ---------------------------------------------------------
    expired_count = fields.Integer(compute="_compute_expired_count")

    def _compute_expired_count(self):
        """Nombre total d’articles périmés (tous articles confondus)."""
        today = fields.Date.today()
        count = self.env['epi.article'].search_count([
            ('perissable', '=', True),
            ('peremption_ids.date_peremption', '<=', today),
        ])
        for rec in self:
            rec.expired_count = count

    # ---------------------------------------------------------
    # Commandes en cours (VERSION CORRIGÉE IT/PRO)
    # ---------------------------------------------------------
    category_id = fields.Many2one("epi.article.category", ondelete="set null")
    move_ids = fields.One2many("epi.article.move", "article_id")

    en_commande = fields.Boolean(compute="_compute_en_commande", store=False)
    commandes_en_attente = fields.Char(compute="_compute_en_commande", store=False)
    en_commande_search = fields.Boolean(compute="_compute_en_commande", store=True, index=True)
    commande_ids = fields.Many2many("epi.commande", compute="_compute_en_commande")

    def _compute_en_commande(self):
        """
        IT PRO :
        Détermine si l’article est présent dans une commande EN COURS,
        mais uniquement si cet article a encore un RELIQUAT.

        Correction :
        - Avant : affichait toutes les commandes en brouillon/commandées
        - Maintenant : n'affiche que celles où backorder_qty > 0
        """

        CommandeLine = self.env["epi.commande.line"]

        for article in self:

            # Lignes où l’article a encore un reliquat
            lignes = CommandeLine.search([
                ("article_id", "=", article.id),
                ("backorder_qty", ">", 0),
                ("commande_id.state", "in", ["draft", "ordered"]),
            ])

            has_cmd = bool(lignes)

            article.en_commande = has_cmd
            article.en_commande_search = has_cmd
            article.commande_ids = lignes.mapped("commande_id")

            # Affichage ergonomique : "cmd1 / cmd2 / cmd3"
            article.commandes_en_attente = (
                " / ".join(lignes.mapped("commande_id.name")) if has_cmd else ""
            )

    # ---------------------------------------------------------
    # Recherche intelligente
    # ---------------------------------------------------------
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Recherche par code ou nom (signature Odoo 16)."""
        args = args or []

        if name:
            domain = ['|',
                ('code', operator, name),
                ('name', operator, name),
            ]
            records = self.search(domain + args, limit=limit)
        else:
            records = self.search(args, limit=limit)

        return records.name_get()
