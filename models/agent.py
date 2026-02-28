# -*- coding: utf-8 -*-
"""
Modèle : epi.agent
------------------------------------------------------------
Gère :
- identité et informations professionnelles
- suivi des contrats (agents expirés)
- historique des mouvements EPI
- remarques internes
- pièces jointes via mail.thread (messages désactivés)

RGPD :
- Le registre national est affiché en clair uniquement lors de la création.
- Après création, il est masqué (*****1234).
- Le bouton "œil" affiche/masque temporairement le vrai numéro.
- Le masquage revient automatiquement à chaque ouverture.
- Aucun popup, aucun JS, aucun widget → 100% Odoo standard.
- La recherche reste possible sur le registre national.
"""

from datetime import date
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class EpiAgent(models.Model):
    _name = 'epi.agent'
    _description = 'Agent'
    _inherit = ['mail.thread']
    _order = "is_expired desc, name, firstname"

    # -------------------------------------------------------------
    # Activation / archivage standard Odoo
    # -------------------------------------------------------------
    active = fields.Boolean(
        string="Actif",
        default=True,
        help="Décochez pour archiver l’agent sans le supprimer."
    )

    message_main_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Pièce jointe principale'
    )

    # -------------------------------------------------------------
    # IDENTITÉ
    # -------------------------------------------------------------
    name = fields.Char(required=True, tracking=True)
    firstname = fields.Char(required=True, tracking=True)
    matricule = fields.Char(string="Matricule")

    # Champ réel (recherchable)
    registre_national = fields.Char(string="N° Registre National")

    # Champ masqué (affiché après création)
    registre_national_masked = fields.Char(
        compute="_compute_registre_national_masked",
        string="N° Registre National",
        store=False
    )

    # Champ stocké → permet le rafraîchissement de la vue
    show_registre = fields.Boolean(
        default=False,
        store=True,
        help="Affiche temporairement le registre national."
    )

    # -------------------------------------------------------------
    # Masquage automatique à chaque ouverture de fiche
    # -------------------------------------------------------------
    def read(self, fields=None, load='_classic_read'):
        """
        À chaque ouverture de fiche :
        - show_registre est remis à False
        - garantit le masquage automatique RGPD
        """
        res = super().read(fields, load)
        for rec in self:
            rec.show_registre = False
        return res

    # -------------------------------------------------------------
    # Compute du registre masqué / affiché
    # -------------------------------------------------------------
    @api.depends("registre_national", "show_registre")
    def _compute_registre_national_masked(self):
        """
        RGPD :
        - En création → afficher en clair.
        - Après création → masqué sauf si show_registre = True.
        """
        for rec in self:

            # En création → toujours en clair
            if not rec.id:
                rec.registre_national_masked = rec.registre_national or ""
                continue

            # Après création
            if rec.show_registre:
                rec.registre_national_masked = rec.registre_national or ""
            else:
                if rec.registre_national:
                    rec.registre_national_masked = "*****" + rec.registre_national[-4:]
                else:
                    rec.registre_national_masked = ""

    # -------------------------------------------------------------
    # Bouton œil : afficher / masquer
    # -------------------------------------------------------------
    def action_toggle_registre(self):
        """
        Inverse l'état d'affichage du registre national.
        Le champ étant stocké, la vue se rafraîchit correctement.
        """
        for rec in self:
            rec.show_registre = not rec.show_registre

    # -------------------------------------------------------------
    # CONTRÔLE : registre national unique (actifs + archivés)
    # -------------------------------------------------------------
    @api.constrains("registre_national")
    def _check_registre_national_unique(self):
        for rec in self:
            if rec.registre_national:
                exists = self.with_context(active_test=False).search([
                    ("registre_national", "=", rec.registre_national),
                    ("id", "!=", rec.id),
                ], limit=1)

                if exists:
                    raise ValidationError(
                        "Ce numéro de registre national est déjà utilisé par "
                        f"{exists.name} {exists.firstname}."
                    )

    # -------------------------------------------------------------
    # INFORMATIONS PROFESSIONNELLES
    # -------------------------------------------------------------
    fonction = fields.Char(string="Fonction")

    contrat = fields.Selection(
        [
            ('cdi', 'CDI'),
            ('cdd', 'CDD'),
            ('interim', 'Intérim'),
            ('stagiaire', 'Stagiaire'),
            ('art60', 'ART 60'),
            ('autres', 'Autres'),
        ],
        string="Contrat"
    )

    batiment_id = fields.Many2one('epi.batiment', string="Bâtiment")
    travail_en_hauteur = fields.Boolean(string="Travail en hauteur")

    # -------------------------------------------------------------
    # CONTRAT : suivi de la fin
    # -------------------------------------------------------------
    date_fin_contrat = fields.Date(string="Fin de contrat")

    is_expired = fields.Boolean(
        string="Contrat expiré",
        compute="_compute_is_expired",
        store=True
    )

    @api.depends("date_fin_contrat", "contrat")
    def _compute_is_expired(self):
        """Détermine si le contrat est expiré (hors CDI)."""
        today = date.today()
        for agent in self:

            if agent.contrat == "cdi":
                agent.is_expired = False
                continue

            agent.is_expired = bool(
                agent.date_fin_contrat and agent.date_fin_contrat < today
            )

    @api.constrains("contrat", "date_fin_contrat")
    def _check_date_fin_contrat(self):
        """Contrats non-CDI → date de fin obligatoire."""
        for agent in self:

            if agent.contrat == "cdi":
                continue

            if not agent.date_fin_contrat:
                raise UserError(
                    "Vous devez indiquer une date de fin de contrat pour cet agent "
                    "car son contrat n'est pas un CDI."
                )

    # -------------------------------------------------------------
    # REMARQUES
    # -------------------------------------------------------------
    remarque = fields.Text(string="Remarque")

    # -------------------------------------------------------------
    # HISTORIQUE DES MOUVEMENTS
    # -------------------------------------------------------------
    mouvement_ligne_ids = fields.One2many(
        'epi.mouvement.ligne',
        'agent_id',
        readonly=True
    )

    # -------------------------------------------------------------
    # ARCHIVAGE : suppression matricule + bâtiment
    # -------------------------------------------------------------
    def write(self, vals):
        """
        Lors de l'archivage :
        - suppression du matricule
        - suppression du bâtiment
        """
        for rec in self:
            if vals.get('active') is False:
                rec.matricule = False
                rec.batiment_id = False

        return super().write(vals)

    # -------------------------------------------------------------
    # BOUTON ARCHIVER / RÉACTIVER
    # -------------------------------------------------------------
    def toggle_active(self):
        for agent in self:
            agent.active = not agent.active

    # -------------------------------------------------------------
    # AFFICHAGE MANY2ONE
    # -------------------------------------------------------------
    def name_get(self):
        """Affichage enrichi : nom + matricule + bâtiment."""
        result = []
        for agent in self:
            label = f"{agent.name} {agent.firstname}"

            if agent.matricule:
                label += f" – {agent.matricule}"

            if agent.batiment_id:
                label += f" – {agent.batiment_id.name}"

            result.append((agent.id, label))
        return result

    # -------------------------------------------------------------
    # RECHERCHE AMÉLIORÉE (nom, prénom, matricule, bâtiment, RN)
    # -------------------------------------------------------------
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []

        domain = ['|', '|', '|', '|',
            ('name', operator, name),
            ('firstname', operator, name),
            ('matricule', operator, name),
            ('batiment_id.name', operator, name),
            ('registre_national', operator, name),
        ]

        agents = self.search(domain + args, limit=limit)
        return agents.name_get()

    # -------------------------------------------------------------
    # DÉSACTIVATION DES MESSAGES
    # -------------------------------------------------------------
    def _message_post_check_access(self, **kwargs):
        """Empêche l'envoi de messages/notes (pièces jointes OK)."""
        raise UserError("L'envoi de messages et de notes est désactivé pour ce document.")
