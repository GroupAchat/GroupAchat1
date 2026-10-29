---
paths:
  - "backend/groupachat/*/migrations/*.py"
  - "backend/groupachat/*/models.py"
---

# Migrations et schéma de base

- Ne jamais modifier une migration déjà appliquée ailleurs que sur ta machine : créer une nouvelle migration.
- Relire le SQL généré avant de le commiter : un renommage est souvent détecté comme suppression + ajout, et efface la colonne.
- Changement destructif en deux déploiements : (1) ajouter la nouvelle colonne, écrire dans les deux, migrer les données ; (2) supprimer l'ancienne dans une migration suivante.
- Nouvelle colonne obligatoire sur une table existante : valeur par défaut ou migration de données, sinon la migration échoue sur une base remplie.
- Contrainte d'unicité et index en base pour toute colonne filtrée ou jointe souvent ; pas seulement une vérification dans le code.
- Montants en entiers ; dates en timestamp avec fuseau (UTC).
- Migration de données réversible, ou marquée irréversible dans le commit et dans `mapper/02-decisions/`.
- Jamais de commande qui efface des données (`migrate reset`, `db push --force-reset`, `flush`, `DROP`) sans demande explicite.
- Nom descriptif (`add_guest_quota_to_users`) ; migration commitée avec le modèle qui la produit.
