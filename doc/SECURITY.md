# SECURITY — Module EPI Stock (V.E.T.E.S)

Ce document décrit les règles de sécurité, de gestion des accès et de bonnes pratiques pour garantir l’intégrité du module `epi_stock` et des données qu’il manipule.

---

## 1. Principes généraux

Le module EPI Stock manipule des données sensibles liées :

- aux agents
- aux équipements de protection individuelle
- aux mouvements et inventaires
- aux documents internes
- aux tournées terrain

La sécurité repose sur trois piliers :

1. **Contrôle strict des accès (ACL)**
2. **Séparation claire des rôles**
3. **Protection des modèles techniques**

---

## 2. Groupes et responsabilités

### Administrateur EPI
- Accès complet à tous les modèles
- Accès complet aux modèles techniques
- Peut installer, mettre à jour et configurer le module
- Réservé à l’IT ou au support technique

### Responsable EPI
- Accès complet aux modèles métier
- Ne peut pas modifier les modèles techniques
- Peut gérer les agents, articles, mouvements, commandes, inventaires, tournées

### Magasinier EPI
- Accès limité selon les règles métier
- Accès complet aux opérations terrain
- Accès lecture seule aux documents et articles
- Ne peut pas accéder aux modèles techniques

---

## 3. Modèles techniques (protégés)

Les modèles suivants sont **réservés à l’administrateur** :

- `vetes_homepage`
- `epi_annee_selection`
- `epi_badge_service`
- `epi.article.move`
- surcharge `ir.ui.menu` (aucune ACL nécessaire)

Ces modèles ne doivent **jamais** :

- être exposés dans un menu
- être accessibles à un groupe métier
- être utilisés dans des relations visibles (Many2one, One2many)
- être modifiés par un utilisateur non‑IT

Ils assurent :

- la page d’accueil
- les sélections internes
- les badges de menu
- les placeholders techniques

---

## 4. Sécurité des ACL

### Règles obligatoires
- Chaque modèle métier doit avoir une ACL explicite.
- Les modèles techniques doivent être **admin only**.
- Aucun modèle ne doit être laissé sans ACL (risque d’accès implicite).
- Aucun modèle ne doit être référencé dans les ACL s’il n’existe pas dans la base.
- Les ACL doivent contenir **exactement 8 colonnes** (Odoo 16 + Docker).

### Risques en cas d’erreur ACL
- erreurs de chargement du module
- vues fantômes
- modèles fantômes
- accès non autorisés
- crash du registre Odoo
- comportements incohérents dans l’interface

---

## 5. Sécurité des données

### Données sensibles
- informations agents
- historique des mouvements
- dates de péremption
- documents internes
- inventaires et tournées

### Bonnes pratiques
- ne jamais supprimer massivement des données sans sauvegarde
- privilégier les désactivations plutôt que les suppressions
- éviter les modifications directes en base PostgreSQL
- utiliser les outils Odoo (ORM) pour toute opération

---

## 6. Sécurité du code

### Python
- ne jamais exposer de méthodes dangereuses via RPC
- éviter les `sudo()` sauf nécessité absolue
- journaliser les erreurs critiques
- ne jamais écrire de logique métier dans les contrôleurs

### XML
- ne jamais exposer un modèle technique dans une vue
- vérifier les domaines et filtres
- éviter les actions non sécurisées

---

## 7. Sécurité Docker / Odoo 16

### Recommandations
- ne jamais modifier les ACL en production sans test préalable
- toujours redémarrer Odoo après mise à jour du module :
- vérifier les logs en cas d’erreur :
- utiliser des volumes persistants pour PostgreSQL
- limiter l’accès au port Odoo aux réseaux internes

---

## 8. Procédure en cas d’incident

### 1. Identifier le type d’incident
- erreur ACL
- erreur de chargement du module
- accès non autorisé
- données incohérentes
- crash du registre

### 2. Actions immédiates
- consulter les logs Docker
- désactiver temporairement l’accès utilisateur si nécessaire
- restaurer une sauvegarde si les données sont corrompues

### 3. Escalade
- contacter l’équipe IT responsable d’Odoo
- documenter l’incident dans le CHANGELOG

---

## 9. Contact IT

Pour toute question de sécurité, incident ou demande d’audit, contacter l’équipe IT responsable du déploiement Odoo.


