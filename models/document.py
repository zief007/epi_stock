# -*- coding: utf-8 -*-
"""
Modèle : epi.document & epi.document.folder
------------------------------------------------------------
Gestion des documents EPI (dossiers + documents).

Fonctionnalités :
- chatter actif (mail.thread + activity)
- documents finalisables via is_ready
- contrainte appliquée uniquement lorsque is_ready = True
- type automatique : fichier ou lien
"""

from odoo import models, fields, api
from odoo.exceptions import UserError


# =====================================================================
#  DOSSIER DE DOCUMENTS
# =====================================================================
class EpiDocumentFolder(models.Model):
    _name = "epi.document.folder"
    _description = "Dossier de documents EPI"
    _order = "name"

    name = fields.Char(required=True)
    description = fields.Text()
    document_ids = fields.One2many("epi.document", "folder_id")


# =====================================================================
#  DOCUMENT
# =====================================================================
class EpiDocument(models.Model):
    _name = "epi.document"
    _description = "Document EPI"
    _order = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ---------------------------------------------------------
    # Champs principaux
    # ---------------------------------------------------------
    name = fields.Char(
        string="Titre",
        required=True,
        tracking=True,
        default="Nouveau document",
    )

    folder_id = fields.Many2one(
        "epi.document.folder",
        string="Dossier",
        required=True,
        tracking=True,
    )

    description = fields.Text()

    # ---------------------------------------------------------
    # Champ technique PRO
    # ---------------------------------------------------------
    is_ready = fields.Boolean(
        string="Document finalisé",
        default=False,
        help="Active les contraintes (fichier OU lien obligatoire)."
    )

    # ---------------------------------------------------------
    # Lien externe
    # ---------------------------------------------------------
    url = fields.Char(string="Lien externe")

    # ---------------------------------------------------------
    # Type automatique
    # ---------------------------------------------------------
    type = fields.Selection(
        [
            ("file", "Fichier"),
            ("url", "Lien"),
        ],
        compute="_compute_type",
        store=True
    )

    @api.depends("url", "message_main_attachment_id")
    def _compute_type(self):
        """Détermine automatiquement le type du document."""
        for doc in self:
            if doc.message_main_attachment_id:
                doc.type = "file"
            elif doc.url:
                doc.type = "url"
            else:
                doc.type = False

    # ---------------------------------------------------------
    # Contrainte PRO : appliquée uniquement si is_ready = True
    # ---------------------------------------------------------
    @api.constrains("url", "message_main_attachment_id", "is_ready")
    def _check_file_or_url(self):
        """
        Contrainte stricte uniquement lorsque le document est finalisé :
        - fichier XOR lien
        - jamais les deux
        - jamais aucun
        """
        for doc in self:

            # Ne jamais bloquer lors du create()
            if not doc.id:
                continue

            # Tant que non finalisé → aucune contrainte
            if not doc.is_ready:
                continue

            has_file = bool(doc.message_main_attachment_id)
            has_url = bool(doc.url)

            if has_file and has_url:
                raise UserError(
                    "Un document ne peut pas avoir à la fois une pièce jointe ET un lien."
                )

            if not has_file and not has_url:
                raise UserError(
                    "Un document doit avoir soit une pièce jointe, soit un lien."
                )
