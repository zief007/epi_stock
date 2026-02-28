# -*- coding: utf-8 -*-
"""
Modèle : epi.inventory
------------------------------------------------------------
Inventaire EPI.

Fonctionnalités :
- chargement automatique des articles par catégorie
- validation simple (mise à jour du stock réel)
- export Excel imprimable (stock réel vide)
- structure légère, sans mouvements de stock
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from io import BytesIO
import xlsxwriter


class EpiInventory(models.Model):
    _name = "epi.inventory"
    _description = "Inventaire des articles"
    _order = "date_inventory desc"

    # ---------------------------------------------------------
    # Champs principaux
    # ---------------------------------------------------------
    name = fields.Char(required=True)
    date_inventory = fields.Date(default=fields.Date.today, required=True)
    category_id = fields.Many2one("epi.article.category", required=True)

    line_ids = fields.One2many(
        "epi.inventory.line",
        "inventory_id",
        string="Lignes d’inventaire"
    )

    state = fields.Selection(
        [("draft", "Brouillon"), ("done", "Validé")],
        default="draft"
    )

    status_display = fields.Char(
        compute="_compute_status_display",
        store=False
    )

    @api.depends("state")
    def _compute_status_display(self):
        """Affichage visuel pour la vue liste."""
        for rec in self:
            rec.status_display = "Validé" if rec.state == "done" else ""

    export_file = fields.Binary(readonly=True)
    export_filename = fields.Char(readonly=True)

    # ---------------------------------------------------------
    # Action : charger les articles
    # ---------------------------------------------------------
    def action_charger_articles(self):
        """Recharge les lignes selon la catégorie (1 ligne = 1 article)."""
        self.ensure_one()

        if not self.category_id:
            raise UserError("Veuillez sélectionner une catégorie.")

        self.line_ids.unlink()

        articles = self.env["epi.article"].search([
            ("category_id", "=", self.category_id.id)
        ])

        for article in articles:
            self.env["epi.inventory.line"].create({
                "inventory_id": self.id,
                "article_id": article.id,
                "stock_theorique": article.stock,
                "stock_reel": 0,
            })

    # ---------------------------------------------------------
    # Action : valider l’inventaire
    # ---------------------------------------------------------
    def action_valider(self):
        """Met à jour le stock réel des articles (sans mouvement)."""
        self.ensure_one()

        if not self.line_ids:
            raise UserError("Aucune ligne d’inventaire à valider.")

        for line in self.line_ids:
            line.article_id.stock = line.stock_reel

        self.state = "done"

    # =====================================================================
    #  EXPORT EXCEL (imprimable)
    # =====================================================================
    def action_export_excel(self):
        """Export Excel : article / stock théorique / stock réel vide."""
        self.ensure_one()

        if not self.line_ids:
            raise UserError("Aucune ligne d’inventaire à exporter.")

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Inventaire")

        header_format = workbook.add_format({
            "bold": True, "bg_color": "#D9D9D9",
            "border": 1, "align": "center", "valign": "vcenter",
        })

        left_format = workbook.add_format({
            "border": 1, "align": "left", "valign": "vcenter",
        })

        center_format = workbook.add_format({
            "border": 1, "align": "center", "valign": "vcenter",
        })

        empty_format = workbook.add_format({
            "border": 1, "align": "center", "valign": "vcenter",
        })

        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)

        headers = ["Article", "Stock théorique", "Stock réel"]
        for col, title in enumerate(headers):
            sheet.write(0, col, title, header_format)

        row = 1
        for line in self.line_ids:
            sheet.write(row, 0, line.article_id.name, left_format)
            sheet.write(row, 1, line.stock_theorique, center_format)
            sheet.write(row, 2, "", empty_format)
            row += 1

        workbook.close()
        output.seek(0)

        self.export_file = base64.b64encode(output.read())
        self.export_filename = f"inventaire_{self.name}.xlsx"

        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/{self.id}"
                f"?model=epi.inventory"
                f"&field=export_file"
                f"&filename={self.export_filename}"
                f"&download=true"
            ),
            "target": "self",
        }
