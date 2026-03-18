# CONTRIBUTING — Module EPI Stock (V.E.T.E.S)

Ce document décrit les règles et bonnes pratiques pour contribuer au module `epi_stock`.
Il s’adresse aux développeurs, intégrateurs et membres de l’équipe IT.

---

## 1. Environnement de développement

### Prérequis
- Odoo 16 Community Edition
- Python 3.10+
- PostgreSQL 14+
- Docker et Docker Compose (environnement recommandé)
- VS Code ou équivalent

### Installation (Docker)
1. Cloner le dépôt contenant le module.
2. Placer le module dans le dossier `addons` du projet Docker.
3. Lancer l’environnement :
4. Vérifier que le conteneur Odoo est actif :

### Mise à jour du module

---

## 2. Structure du module

- `models/` : modèles métier et techniques  
- `views/` : vues XML  
- `security/` : ACL et règles d’accès  
- `data/` : données initiales  
- `static/` : ressources statiques  
- `README.md` : documentation fonctionnelle  
- `CHANGELOG.md` : historique des versions  
- `CONTRIBUTING.md` : ce document  

---

## 3. Règles de développement

### 3.1. Python
- Respecter les conventions Odoo (snake_case, API env).
- Toujours importer `models`, `fields`, `api` depuis `odoo`.
- Ne jamais écrire de logique métier dans les contrôleurs.
- Utiliser `@api.depends`, `@api.constrains`, `@api.onchange` lorsque pertinent.
- Préférer les méthodes atomiques et explicites.

### 3.2. XML
- Préfixer toutes les vues : `epi_..._view`.
- Ne jamais modifier une vue standard sans `_inherit`.
- Tester chaque vue avec les trois groupes (admin, responsable, magasinier).
- Vérifier que chaque action pointe vers une vue valide.

### 3.3. Sécurité (ACL)
- Toute création de modèle nécessite une ACL admin.
- Les modèles techniques doivent être **admin only**.
- Ne jamais exposer un modèle technique à un groupe métier.
- Vérifier systématiquement que chaque modèle métier a les droits adaptés :
  - lecture
  - écriture
  - création
  - suppression  
  selon les règles définies dans le README.

### 3.4. Menus et actions
- Ne jamais créer de menu pointant vers un modèle technique.
- Vérifier que chaque menu a une action valide.
- Vérifier que chaque action a une vue valide.

---

## 4. Tests et validation

### 4.1. Tests manuels
Avant toute PR ou mise en production :

- Créer un agent  
- Modifier un agent  
- Tester les dates de péremption  
- Créer un mouvement  
- Supprimer un mouvement  
- Valider une commande  
- Encoder une réception  
- Créer un inventaire  
- Modifier un inventaire  
- Tester les tournées  
- Tester les documents  
- Vérifier les badges de menu  

### 4.2. Tests ACL
Tester les trois groupes :

- **Admin** : accès complet  
- **Responsable** : accès complet sauf IT  
- **Magasinier** : accès limité selon règles métier  

---

## 5. Bonnes pratiques Git

### Branches
- `main` : production  
- `dev` : développement  
- `feature/...` : nouvelles fonctionnalités  
- `fix/...` : corrections  
- `hotfix/...` : corrections urgentes  

### Commits
Format recommandé :

### Pull Requests
Chaque PR doit contenir :
- une description claire  
- une justification métier  
- des captures d’écran si nécessaire  
- une mise à jour du CHANGELOG  
- des tests manuels validés  

---

## 6. Modèles techniques (important)

Les modèles suivants sont **réservés à l’admin** :

- `vetes_homepage`  
- `epi_annee_selection`  
- `epi_badge_service`  
- `epi.article.move`  
- surcharge `ir.ui.menu` (aucune ACL nécessaire)  

Ne jamais :
- les exposer dans un menu  
- leur donner des droits à un groupe métier  
- les utiliser dans des relations Many2one visibles  

---

## 7. Déploiement en production

1. Mettre à jour le module :
2. Redémarrer Odoo :
3. Vérifier les logs :
4. Tester les ACL  
5. Tester les vues  
6. Tester les badges de menu  

---

## 8. Support

Pour toute question technique ou demande d’évolution, contacter l’équipe IT responsable du déploiement Odoo.
