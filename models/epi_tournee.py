# -*- coding: utf-8 -*-
"""
Modèle : epi.tournee & epi.tournee.ligne
------------------------------------------------------------
Gestion des tournées EPI.

Fonctionnalités :
- optimisation OSRM (ordre des bâtiments)
- lien Google Maps complet
- rafraîchissement GPS depuis epi.batiment
- export Excel chauffeurs (ordre / bâtiment / adresse / linge)
- boutons métier : optimiser / maps / refresh / export
"""

import base64
import requests
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import xlsxwriter


# =====================================================================
#                         MODÈLE : Tournée
# =====================================================================
class EpiTournee(models.Model):
    _name = "epi.tournee"
    _description = "Tournée quotidienne EPI"
    _order = "jour_semaine, name"

    # ---------------------------------------------------------
    # Champs principaux
    # ---------------------------------------------------------
    name = fields.Char(required=True)
    jour_semaine = fields.Selection(
        [
            ("lundi", "Lundi"),
            ("mardi", "Mardi"),
            ("mercredi", "Mercredi"),
            ("jeudi", "Jeudi"),
            ("vendredi", "Vendredi"),
            ("samedi", "Samedi"),
            ("dimanche", "Dimanche"),
        ],
        required=True,
    )

    point_depart_id = fields.Many2one("epi.batiment", string="Point de départ")
    point_arrivee_id = fields.Many2one("epi.batiment", string="Point d'arrivée")

    ligne_ids = fields.One2many(
        "epi.tournee.ligne",
        "tournee_id",
        string="Bâtiments de la tournée",
    )

    # =====================================================================
    #                EXPORT EXCEL – Tournée chauffeurs
    # =====================================================================
    def action_export_excel(self):
        """Export Excel formaté (ordre / bâtiment / adresse / linge)."""
        self.ensure_one()
        tour = self

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Tournée")

        # Formats
        header_format = workbook.add_format({
            "bold": True, "font_size": 14,
            "align": "center", "valign": "vcenter", "border": 1,
        })

        col_header = workbook.add_format({
            "bold": True, "border": 1,
            "bg_color": "#D9D9D9", "align": "center",
        })

        cell = workbook.add_format({"border": 1, "align": "left"})

        sheet.set_column(0, 3, 35)

        # En-têtes
        sheet.merge_range(0, 0, 0, 3, f"Tournée : {tour.name}", header_format)
        sheet.merge_range(1, 0, 1, 3, f"Jour : {tour.jour_semaine.capitalize()}", header_format)
        sheet.write(2, 0, "")

        # Titres
        headers = ["Ordre", "Bâtiment", "Adresse", "Emplacement linge"]
        for col, title in enumerate(headers):
            sheet.write(3, col, title, col_header)

        # Lignes
        row = 4
        for ligne in tour.ligne_ids.sorted(key=lambda l: l.ordre):
            bat = ligne.batiment_id
            sheet.write(row, 0, ligne.ordre or "", cell)
            sheet.write(row, 1, bat.name or "", cell)
            sheet.write(row, 2, bat.adresse or "", cell)
            sheet.write(row, 3, bat.emplacement_linge or "", cell)
            row += 1

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env["ir.attachment"].create({
            "name": f"tournee_{tour.name}.xlsx",
            "type": "binary",
            "datas": file_data,
            "res_model": "epi.tournee",
            "res_id": tour.id,
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        })

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }

    # =====================================================================
    #                BOUTON : Optimisation OSRM
    # =====================================================================
    def action_optimize_itinerary(self):
        """Optimise l'ordre des bâtiments via OSRM."""
        for tournee in self:

            if not tournee.point_depart_id:
                raise UserError(_("Veuillez définir un point de départ."))

            if not tournee.point_depart_id.latitude or not tournee.point_depart_id.longitude:
                raise UserError(_("Le point de départ n’a pas de coordonnées GPS."))

            lignes = tournee.ligne_ids
            if not lignes:
                raise UserError(_("Aucun bâtiment dans la tournée."))

            # Points OSRM
            points = [
                f"{tournee.point_depart_id.longitude},{tournee.point_depart_id.latitude}"
            ]

            for ligne in lignes:
                if not ligne.latitude or not ligne.longitude:
                    raise UserError(_("Le bâtiment '%s' n’a pas de coordonnées GPS.") % ligne.batiment_id.name)
                points.append(f"{ligne.longitude},{ligne.latitude}")

            has_arrival = bool(tournee.point_arrivee_id)
            if has_arrival:
                if not tournee.point_arrivee_id.latitude or not tournee.point_arrivee_id.longitude:
                    raise UserError(_("Le point d'arrivée n’a pas de coordonnées GPS."))
                points.append(
                    f"{tournee.point_arrivee_id.longitude},{tournee.point_arrivee_id.latitude}"
                )

            # Appel OSRM
            url = (
                "http://router.project-osrm.org/trip/v1/driving/"
                + ";".join(points)
                + "?source=first&roundtrip=false"
            )

            try:
                response = requests.get(url, timeout=10)
            except Exception:
                raise UserError(_("Impossible de contacter le serveur OSRM."))

            if response.status_code != 200:
                raise UserError(_("Erreur lors de l'appel à OSRM."))

            data = response.json()
            if "trips" not in data or not data["trips"]:
                raise UserError(_("OSRM n’a pas pu calculer l’itinéraire."))

            waypoints = data.get("waypoints", [])
            if not waypoints:
                raise UserError(_("OSRM n’a renvoyé aucun waypoint."))

            # Mapping index OSRM
            trip_pos_by_orig_index = {
                orig_index: wp.get("waypoint_index", 0)
                for orig_index, wp in enumerate(waypoints)
            }

            lignes_ids = lignes.ids

            # Position OSRM pour une ligne
            def _trip_position_for_line(ligne):
                orig_index = 1 + lignes_ids.index(ligne.id)
                return trip_pos_by_orig_index.get(orig_index, 0)

            lignes_sorted = sorted(lignes, key=_trip_position_for_line)

            # Application ordre
            for idx, ligne in enumerate(lignes_sorted, start=1):
                ligne.ordre = idx

        return True

    # =====================================================================
    #      Lien Google Maps
    # =====================================================================
    def get_google_maps_url(self):
        """Génère un lien Google Maps complet."""
        self.ensure_one()

        if not self.point_depart_id or not self.point_depart_id.latitude or not self.point_depart_id.longitude:
            return ""

        origin = f"{self.point_depart_id.latitude},{self.point_depart_id.longitude}"

        lignes = self.ligne_ids.sorted(key=lambda l: l.ordre)
        if not lignes:
            return ""

        # Destination
        if self.point_arrivee_id and self.point_arrivee_id.latitude and self.point_arrivee_id.longitude:
            destination = f"{self.point_arrivee_id.latitude},{self.point_arrivee_id.longitude}"
        else:
            last = lignes[-1]
            if not last.latitude or not last.longitude:
                return ""
            destination = f"{last.latitude},{last.longitude}"

        waypoints = [
            f"{l.latitude},{l.longitude}"
            for l in lignes
            if l.latitude and l.longitude
        ]

        url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={origin}"
            f"&destination={destination}"
        )

        if waypoints:
            url += "&waypoints=" + "|".join(waypoints)

        return url

    # =====================================================================
    #      BOUTON : Ouvrir Google Maps
    # =====================================================================
    def action_open_google_maps(self):
        """Ouvre Google Maps dans un nouvel onglet."""
        self.ensure_one()

        url = self.get_google_maps_url()
        if not url:
            raise UserError(_("Impossible de générer le lien Google Maps."))

        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    # =====================================================================
    #      BOUTON : Rafraîchir GPS
    # =====================================================================
    def action_refresh_gps(self):
        """Recopie les coordonnées GPS depuis les bâtiments."""
        self.ensure_one()

        for ligne in self.ligne_ids:
            if ligne.batiment_id:
                ligne.latitude = ligne.batiment_id.latitude
                ligne.longitude = ligne.batiment_id.longitude

        return {
            "effect": {
                "fadeout": "slow",
                "message": _("Coordonnées GPS mises à jour pour toutes les lignes."),
                "type": "rainbow_man",
            }
        }


# =====================================================================
#                         MODÈLE : Ligne de tournée
# =====================================================================
class EpiTourneeLigne(models.Model):
    _name = "epi.tournee.ligne"
    _description = "Ligne de tournée EPI"
    _order = "ordre asc"

    tournee_id = fields.Many2one("epi.tournee", required=True, ondelete="cascade")
    batiment_id = fields.Many2one("epi.batiment", required=True)

    adresse = fields.Char(
        related="batiment_id.adresse",
        store=True,
        readonly=False,
    )

    latitude = fields.Float()
    longitude = fields.Float()

    ordre = fields.Integer(string="Ordre")
    distance = fields.Float(string="Distance (m)")
    temps_estime = fields.Float(string="Temps estimé (min)")

    @api.onchange("batiment_id")
    def _onchange_batiment_id(self):
        """Mise à jour GPS lors du changement de bâtiment."""
        if self.batiment_id:
            self.latitude = self.batiment_id.latitude
            self.longitude = self.batiment_id.longitude

    def write(self, vals):
        """Mise à jour GPS lors de la modification du bâtiment."""
        res = super().write(vals)
        if "batiment_id" in vals:
            for rec in self:
                if rec.batiment_id:
                    rec.latitude = rec.batiment_id.latitude
                    rec.longitude = rec.batiment_id.longitude
        return res
