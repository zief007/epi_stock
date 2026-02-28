# -*- coding: utf-8 -*-
"""
Modèle : epi.annee.selection
------------------------------------------------------------
Modèle technique utilisé dans les wizards d’export.

Fonctionnalités :
- liste d’années (affichage + valeur numérique)
- génération automatique 2015 → 2035 à l’installation
"""

from odoo import models, fields, api


class EpiAnneeSelection(models.Model):
    _name = "epi.annee.selection"
    _description = "Sélection d'années pour les rapports EPI"
    _order = "value asc"

    # -------------------------------------------------------------
    # Champs
    # -------------------------------------------------------------
    name = fields.Char(
        string="Année",
        required=True,
        help="Année affichée dans les listes."
    )

    value = fields.Integer(
        string="Valeur",
        required=True,
        help="Valeur numérique de l'année (ex : 2026)."
    )

    # -------------------------------------------------------------
    # Génération automatique des années à l'installation
    # -------------------------------------------------------------
    @api.model
    def create_years_if_missing(self):
        """
        Crée les années 2015 → 2035 si absentes.
        Appelée via un fichier data XML.
        """
        for year in range(2015, 2036):
            if not self.search([("value", "=", year)]):
                self.create({
                    "name": str(year),
                    "value": year,
                })
