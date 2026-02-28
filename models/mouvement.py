# -*- coding: utf-8 -*-
"""
Modèle : epi.mouvement & epi.mouvement.ligne
------------------------------------------------------------
Gestion des mouvements EPI (sorties / retours).

Fonctionnalités :
- numérotation automatique (S/R + date + séquence)
- règles métier sorties / retours
- ligne auto pour sorties administratives
- export Excel propre
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
from io import BytesIO
import xlsxwriter


# =====================================================================
#  MOUVEMENT D’EPI
# =====================================================================
class EpiMouvement(models.Model):
    _name = 'epi.mouvement'
    _description = 'Mouvement d’EPI'
    _order = 'date_mouvement desc, id desc'

    # ---------------------------------------------------------
    # Champs principaux
    # ---------------------------------------------------------
    type_mouvement = fields.Selection(
        [('sortie', 'Sortie'), ('retour', 'Retour')],
        default='sortie',
        required=True,
    )

    allow_empty = fields.Boolean(string="Sortie sans article")

    agent_id = fields.Many2one('epi.agent', required=True)
    date_mouvement = fields.Date(default=fields.Date.today, required=True)

    numero_bon = fields.Char(readonly=True, copy=False)
    export_file = fields.Binary(readonly=True)

    ligne_ids = fields.One2many('epi.mouvement.ligne', 'mouvement_id')

    # ---------------------------------------------------------
    # Contraintes métier
    # ---------------------------------------------------------
    @api.constrains('ligne_ids', 'allow_empty', 'type_mouvement')
    def _check_empty_or_lines(self):
        """Règles métier sorties / retours."""
        for rec in self:

            def has_article(lines):
                return any(l.article_id for l in lines)

            # Retour : article obligatoire
            if rec.type_mouvement == "retour":
                if not rec.ligne_ids or not has_article(rec.ligne_ids):
                    raise ValidationError("Un retour doit contenir au moins un article.")
                continue

            # Sortie classique
            if rec.type_mouvement == "sortie" and not rec.allow_empty:
                if not rec.ligne_ids or not has_article(rec.ligne_ids):
                    raise ValidationError(
                        "Une sortie doit contenir au moins un article, "
                        "ou activer 'Sortie sans article'."
                    )

            # Sortie administrative
            if rec.allow_empty:
                if not rec.ligne_ids:
                    raise ValidationError("Une ligne doit être générée automatiquement.")
                if not rec.ligne_ids[0].remarque:
                    raise ValidationError("Une remarque est obligatoire pour une sortie sans article.")

    # ---------------------------------------------------------
    # Création : numérotation + ligne auto
    # ---------------------------------------------------------
    @api.model
    def create(self, vals):
        """Numérotation automatique + ligne auto si allow_empty."""
        date = fields.Date.from_string(vals.get('date_mouvement')) or fields.Date.today()
        date_str = date.strftime('%d%m%Y')

        type_mvt = vals.get('type_mouvement', 'sortie')
        prefix = "S" if type_mvt == "sortie" else "R"

        count = self.search_count([
            ('date_mouvement', '=', date),
            ('type_mouvement', '=', type_mvt)
        ])
        sequence = f"{count + 1:02d}"

        vals['numero_bon'] = f"{prefix}-{date_str}-{sequence}"

        rec = super().create(vals)

        if rec.allow_empty and not rec.ligne_ids:
            rec.ligne_ids = [(0, 0, {
                'article_id': False,
                'quantite': 0,
                'remarque': "",
            })]

        return rec

    # ---------------------------------------------------------
    # Export Excel
    # ---------------------------------------------------------
    def print_mouvement(self):
        """Génère un fichier Excel propre."""
        self.ensure_one()

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Bon de mouvement")

        center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        bold_center = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        header_box = workbook.add_format({
            'bold': True, 'border': 1,
            'align': 'center', 'valign': 'vcenter',
            'bg_color': '#F2F2F2'
        })

        # Titre
        sheet.merge_range('A1:C1', 'BON DE MOUVEMENT', header_box)

        # Infos
        sheet.write('A3', "Numéro :", bold_center)
        sheet.write('B3', self.numero_bon or "", center)

        sheet.write('A4', "Date :", bold_center)
        sheet.write('B4', str(self.date_mouvement), center)

        sheet.write('A6', "Nom :", bold_center)
        sheet.write('B6', self.agent_id.name or "", center)

        sheet.write('A7', "Prénom :", bold_center)
        sheet.write('B7', self.agent_id.firstname or "", center)

        sheet.write('A8', "Matricule :", bold_center)
        sheet.write('B8', self.agent_id.matricule or "", center)

        sheet.write('A9', "Fonction :", bold_center)
        sheet.write('B9', self.agent_id.fonction or "", center)

        sheet.write('A10', "Bâtiment :", bold_center)
        sheet.write('B10', self.agent_id.batiment_id.name or "", center)

        # Lignes
        row = 12
        sheet.write(row, 0, "Article", bold_center)
        sheet.write(row, 1, "Quantité", bold_center)
        sheet.write(row, 2, "Remarque", bold_center)
        row += 1

        for line in self.ligne_ids:
            sheet.write(row, 0, line.article_id.name or "", center)
            sheet.write(row, 1, line.quantite or 0, center)
            sheet.write(row, 2, line.remarque or "", center)
            row += 1

        sheet.set_column(0, 3, 30)

        workbook.close()
        output.seek(0)

        self.export_file = base64.b64encode(output.read())
        filename = f"Bon_mouvement_{self.numero_bon}.xlsx"

        return {
            'type': 'ir.actions.act_url',
            'url': (
                f"web/content/?model=epi.mouvement&id={self.id}"
                f"&field=export_file&filename={filename}&download=true"
            ),
            'target': 'self',
        }


# =====================================================================
#  LIGNE DE MOUVEMENT
# =====================================================================
class EpiMouvementLigne(models.Model):
    _name = 'epi.mouvement.ligne'
    _description = 'Ligne de mouvement d’EPI'
    _order = 'id'

    mouvement_id = fields.Many2one('epi.mouvement', ondelete='cascade')
    article_id = fields.Many2one('epi.article')

    quantite = fields.Integer(default=1)
    remarque = fields.Char()

    date_mouvement = fields.Date(related="mouvement_id.date_mouvement", store=True)
    agent_id = fields.Many2one(related="mouvement_id.agent_id", store=True)
    type_mouvement = fields.Selection(related="mouvement_id.type_mouvement", store=True)

    allow_empty = fields.Boolean(related="mouvement_id.allow_empty", store=False)
