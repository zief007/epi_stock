# -*- coding: utf-8 -*-
"""
Extension : ir.ui.menu
------------------------------------------------------------
Mise à jour automatique des badges (🟥🟧🟩) au chargement du menu.

Objectifs IT :
- surcharge sécurisée (pas de récursion, pas de boucle infinie)
- compatible Odoo 16 CE
- NBSP (\u00A0) indispensables pour l’affichage des emojis
"""

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    # ---------------------------------------------------------
    # SURCHARGE : load_menus()
    # ---------------------------------------------------------
    def load_menus(self, debug=False):
        """Met à jour les badges avant le chargement du menu principal."""
        try:
            self.sudo().update_vetes_badges()
        except Exception as e:
            _logger.error("Erreur update_vetes_badges(): %s", e)

        return super().load_menus(debug)

    # ---------------------------------------------------------
    # LOGIQUE MÉTIER : update_vetes_badges()
    # ---------------------------------------------------------
    def update_vetes_badges(self):
        """Met à jour les noms de menus avec alertes (🟥🟧🟩)."""

        # AGENTS
        menu_agents = self.env.ref("epi_stock.menu_epi_agents", raise_if_not_found=False)
        expired_agents = self.env["epi.agent"].search_count([("is_expired", "=", True)])

        if menu_agents:
            menu_agents.name = "Agents\u00A0🟥" if expired_agents > 0 else "Agents"

        # ARTICLES
        menu_articles = self.env.ref("epi_stock.menu_epi_articles", raise_if_not_found=False)
        expired_articles = self.env["epi.article"].search_count([("is_expired", "=", True)])
        low_stock_articles = self.env["epi.article"].search_count([("is_below_threshold", "=", True)])

        if menu_articles:
            if expired_articles > 0 and low_stock_articles > 0:
                menu_articles.name = "Articles\u00A0🟧🟩"
            elif expired_articles > 0:
                menu_articles.name = "Articles\u00A0🟧"
            elif low_stock_articles > 0:
                menu_articles.name = "Articles\u00A0🟩"
            else:
                menu_articles.name = "Articles"
