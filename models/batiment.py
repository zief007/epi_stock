# -*- coding: utf-8 -*-
"""
Modèle : epi.batiment
------------------------------------------------------------
Représente un bâtiment / site de la Ville de Liège.

Fonctionnalités :
- gestion des bâtiments et coordonnées GPS
- agents rattachés (expirés / désactivés exclus)
- export Excel formaté (A4 paysage)
- géolocalisation via Nominatim (OpenStreetMap)

Note :
- Aucun héritage mail.thread (chatter désactivé dans tout le module EPI).
"""

from odoo import models, fields
from odoo.exceptions import UserError
import base64
from io import BytesIO
import xlsxwriter
import requests


# =====================================================================
#  MODÈLE PRINCIPAL : BÂTIMENT
# =====================================================================
class EpiBatiment(models.Model):
    _name = "epi.batiment"
    _description = "Bâtiment / Site"
    _order = "name"

    # ---------------------------------------------------------
    # Champs principaux
    # ---------------------------------------------------------
    name = fields.Char(
        string="Nom du bâtiment",
        required=True,
        help="Nom du bâtiment ou du site."
    )

    adresse = fields.Char(string="Adresse")
    responsable = fields.Char(string="Responsable")
    phone = fields.Char(string="N° Tel")
    note = fields.Text(string="Remarque")

    # ---------------------------------------------------------
    # Emplacement du linge
    # ---------------------------------------------------------
    emplacement_linge = fields.Text(
        string="Emplacement linge",
        help="Lieu exact où les chauffeurs récupèrent le linge."
    )

    # ---------------------------------------------------------
    # Coordonnées GPS
    # ---------------------------------------------------------
    latitude = fields.Float(string="Latitude")
    longitude = fields.Float(string="Longitude")

    # ---------------------------------------------------------
    # Agents rattachés (expirés / désactivés exclus)
    # ---------------------------------------------------------
    agent_ids = fields.One2many(
        "epi.agent",
        "batiment_id",
        string="Agents actifs",
        domain=[
            ("is_expired", "=", False),
            ("active", "=", True)
        ],
        help="Agents actifs rattachés à ce bâtiment."
    )

    # ---------------------------------------------------------
    # Contrainte SQL
    # ---------------------------------------------------------
    _sql_constraints = [
        ("batiment_unique", "unique(name)", "Un bâtiment portant ce nom existe déjà !"),
    ]

    # ---------------------------------------------------------
    # GÉOLOCALISATION AUTOMATIQUE (Nominatim)
    # ---------------------------------------------------------
    def action_geolocate(self):
        """
        Récupère latitude/longitude via Nominatim (OpenStreetMap).
        Adresse obligatoire.
        """
        self.ensure_one()

        if not self.adresse:
            raise UserError("Veuillez d'abord encoder une adresse.")

        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": self.adresse, "format": "json", "limit": 1}

        try:
            response = requests.get(
                url,
                params=params,
                timeout=10,
                headers={"User-Agent": "Odoo-EPI-Module"}
            )
        except Exception:
            raise UserError("Impossible de contacter le service de géolocalisation.")

        if response.status_code != 200:
            raise UserError("Erreur lors de l'appel à Nominatim.")

        data = response.json()
        if not data:
            raise UserError("Aucune coordonnée trouvée pour cette adresse.")

        # Mise à jour des coordonnées GPS
        self.latitude = float(data[0]["lat"])
        self.longitude = float(data[0]["lon"])

        return {
            "effect": {
                "fadeout": "slow",
                "message": "Coordonnées GPS mises à jour avec succès.",
                "type": "rainbow_man",
            }
        }

    # ---------------------------------------------------------
    # EXPORT EXCEL PROFESSIONNEL
    # ---------------------------------------------------------
    def action_export_excel(self):
        """
        Exporte un fichier Excel formaté (A4 paysage).
        Les agents expirés / désactivés sont exclus automatiquement.
        """
        self.ensure_one()
        bat = self

        # Buffer mémoire
        output = BytesIO()

        # Création du fichier Excel
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Bâtiment")

        # ---------------------------------------------------------
        # FORMATS
        # ---------------------------------------------------------
        header_format = workbook.add_format({
            'bold': True, 'font_size': 14,
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })

        text_format = workbook.add_format({'border': 1, 'align': 'left'})

        table_header_format = workbook.add_format({
            'bold': True, 'border': 1,
            'bg_color': '#D9D9D9', 'align': 'center'
        })

        table_cell_format = workbook.add_format({'border': 1, 'align': 'left'})

        # ---------------------------------------------------------
        # MISE EN PAGE A4 PAYSAGE
        # ---------------------------------------------------------
        sheet.set_landscape()
        sheet.fit_to_pages(1, 1)
        sheet.set_paper(9)  # A4

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 5, 25)

        # ---------------------------------------------------------
        # EN-TÊTE
        # ---------------------------------------------------------
        sheet.merge_range(0, 0, 0, 5, f"BÂTIMENT : {bat.name}", header_format)
        sheet.merge_range(1, 0, 1, 5, f"Adresse : {bat.adresse or ''}", text_format)
        sheet.merge_range(2, 0, 2, 5, f"Remarque : {bat.note or ''}", text_format)

        export_date = fields.Date.today().strftime("%d/%m/%Y")
        sheet.merge_range(3, 0, 3, 5, f"Date d’export : {export_date}", text_format)

        sheet.write(4, 0, "")

        # ---------------------------------------------------------
        # TITRES DU TABLEAU
        # ---------------------------------------------------------
        headers = ["Matricule", "Nom", "Prénom", "Fonction", "Vêtements", "Remarque"]

        for col, title in enumerate(headers):
            sheet.write(5, col, title, table_header_format)

        # ---------------------------------------------------------
        # LIGNES DES AGENTS
        # ---------------------------------------------------------
        row = 6
        for agent in bat.agent_ids:
            sheet.write(row, 0, agent.matricule or "", table_cell_format)
            sheet.write(row, 1, agent.name or "", table_cell_format)
            sheet.write(row, 2, agent.firstname or "", table_cell_format)
            sheet.write(row, 3, agent.fonction or "", table_cell_format)
            sheet.write(row, 4, "", table_cell_format)
            sheet.write(row, 5, "", table_cell_format)
            row += 1

        sheet.autofilter(5, 0, row - 1, 5)

        workbook.close()

        file_data = base64.b64encode(output.getvalue())

        attachment = self.env['ir.attachment'].create({
            'name': f"batiment_{bat.name}.xlsx",
            'type': 'binary',
            'datas': file_data,
            'res_model': 'epi.batiment',
            'res_id': bat.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }
