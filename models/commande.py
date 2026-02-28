# -*- coding: utf-8 -*-
"""
Modèle : epi.commande
------------------------------------------------------------
Gestion des commandes EPI.

Fonctionnalités :
- lignes mères / filles (backorder)
- réception partielle / totale
- chaînage des lignes filles (historique complet)
- mise à jour du stock à chaque réception
- validation automatique dès que le reliquat tombe à 0
- sécurisation totale : impossible de valider une commande vide
"""

from odoo import models, fields, api
from odoo.exceptions import UserError


class EpiCommande(models.Model):
    _name = "epi.commande"
    _description = "Commande d’articles EPI"
    _inherit = ["mail.thread"]

    # ---------------------------------------------------------
    # Ordre d'affichage : commandes "Commandée" en haut
    # ---------------------------------------------------------
    _order = "is_ordered desc, date_commande desc"

    # ---------------------------------------------------------
    # CHAMPS PRINCIPAUX
    # ---------------------------------------------------------
    active = fields.Boolean(default=True)

    def toggle_active(self):
        for rec in self:
            rec.active = not rec.active

    name = fields.Char(required=True, tracking=True)
    fournisseur = fields.Char()
    date_commande = fields.Date(default=fields.Date.today)
    date_reception = fields.Date()
    remarque = fields.Text()

    line_ids = fields.One2many("epi.commande.line", "commande_id")
    line_ids_simple = fields.One2many("epi.commande.line", "commande_id")

    has_backorder = fields.Boolean(compute="_compute_has_backorder", store=True)

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("ordered", "Commandée"),
            ("received", "Reçue"),
        ],
        default="draft",
        tracking=True
    )

    # ---------------------------------------------------------
    # Priorité d'affichage : commandes commandées
    # ---------------------------------------------------------
    is_ordered = fields.Boolean(
        compute="_compute_is_ordered",
        store=True,
        help="True si la commande est en état 'Commandée'."
    )

    @api.depends("state")
    def _compute_is_ordered(self):
        for cmd in self:
            cmd.is_ordered = (cmd.state == "ordered")

    # ---------------------------------------------------------
    # CALCUL DU RELIQUAT GLOBAL
    # ---------------------------------------------------------
    @api.depends("line_ids.backorder_qty", "line_ids.qty_entree", "line_ids.parent_line_id")
    def _compute_has_backorder(self):
        for cmd in self:

            families = {}

            for line in cmd.line_ids:
                root = line
                while root.parent_line_id:
                    root = root.parent_line_id
                families.setdefault(root, []).append(line)

            last_lines = [
                max(lines, key=lambda l: l.qty_entree)
                for lines in families.values()
            ]

            cmd.has_backorder = any(l.backorder_qty > 0 for l in last_lines)

    # ---------------------------------------------------------
    # ACTION : CONFIRMER
    # ---------------------------------------------------------
    def action_confirmer(self):
        for commande in self:

            if not commande.line_ids:
                raise UserError("La commande ne contient aucune ligne.")

            for line in commande.line_ids:
                if line.parent_line_id:
                    line.unlink()

            for line in commande.line_ids:
                line.write({
                    "qty_entree": 0,
                    "qty_recue": 0,
                    "backorder_qty": line.qty_commande,
                    "is_done": False,
                })

            commande.state = "ordered"

    # ---------------------------------------------------------
    # ACTION : RÉCEPTIONNER
    # ---------------------------------------------------------
    def action_receptionner(self):
        for commande in self:
            today = fields.Date.today()

            if all(line.qty_entree == 0 and line.qty_recue == 0 for line in commande.line_ids):
                raise UserError("Aucune quantité reçue. Impossible de réceptionner.")

            mother_lines = commande.line_ids.filtered(
                lambda l: not l.parent_line_id and l.qty_recue > 0 and not l.is_done
            )

            for line in mother_lines:
                qty_recue = line.qty_recue

                if line.qty_entree + qty_recue > line.qty_commande:
                    raise UserError(
                        f"Quantité reçue trop élevée pour {line.article_id.display_name}."
                    )

                line.article_id.stock += qty_recue

                qty_entree_apres = line.qty_entree + qty_recue
                backorder = line.qty_commande - qty_entree_apres

                line.write({
                    "qty_entree": qty_entree_apres,
                    "qty_recue": 0,
                    "backorder_qty": backorder,
                    "date_reception_partielle": today,
                })

                if backorder > 0:
                    self.env["epi.commande.line"].create({
                        "commande_id": commande.id,
                        "article_id": line.article_id.id,
                        "qty_commande": line.qty_commande,
                        "qty_entree": qty_entree_apres,
                        "qty_recue": 0,
                        "backorder_qty": backorder,
                        "parent_line_id": line.id,
                    })

            child_lines = commande.line_ids.filtered(
                lambda l: l.parent_line_id and l.qty_recue > 0 and not l.is_done
            )

            for child in child_lines:
                qty_recue = child.qty_recue
                previous = child.parent_line_id

                qty_entree_apres = previous.qty_entree + qty_recue

                if qty_entree_apres > previous.qty_commande:
                    raise UserError(
                        f"Quantité reçue trop élevée pour {child.article_id.display_name}."
                    )

                child.article_id.stock += qty_recue

                backorder = previous.qty_commande - qty_entree_apres

                child.write({
                    "qty_entree": qty_entree_apres,
                    "qty_recue": 0,
                    "backorder_qty": backorder,
                    "date_reception_partielle": today,
                })

                if backorder > 0:
                    self.env["epi.commande.line"].create({
                        "commande_id": commande.id,
                        "article_id": child.article_id.id,
                        "qty_commande": previous.qty_commande,
                        "qty_entree": qty_entree_apres,
                        "qty_recue": 0,
                        "backorder_qty": backorder,
                        "parent_line_id": child.id,
                    })

            commande._compute_has_backorder()

            if not commande.has_backorder:
                commande.write({
                    "state": "received",
                    "date_reception": today,
                })
            else:
                commande.state = "ordered"
