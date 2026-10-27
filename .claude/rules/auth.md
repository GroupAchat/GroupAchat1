---
paths:
  - "backend/groupachat/comptes/**"
  - "backend/groupachat/noyau/permissions.py"
  - "backend/groupachat/noyau/limitation.py"
  - "backend/config/service/fichiers.py"
  - "backend/config/settings.py"
  - "frontend/commun/src/contexte/Session.tsx"
  - "frontend/commun/src/api/client.ts"
  - "frontend/boutique/src/pages/Authentification.tsx"
---

# Authentification et autorisations

- Mots de passe hachés par les hacheurs de Django (`set_password`), jamais de hachage maison.
- Même message pour un identifiant inconnu et un mot de passe faux : pas d'énumération de comptes.
- Blocage après échecs par couple (identifiant, adresse IP), compteur incrémenté de façon atomique avant la vérification.
- Group Achat n'a **pas de JWT** : session Django + jeton CSRF (`SessionAuthentication`), une seule origine. Ne pas en introduire.
- Autorisation vérifiée côté serveur sur chaque route : le rôle **et** la propriété de la ressource (un client ne lit pas la commande d'un autre).
- Jamais de token, mot de passe ou hash dans les logs ni dans les réponses.
- Tests : jeton expiré, forgé, de mauvais type ; mauvais rôle ; ressource d'un autre utilisateur ; blocage après échecs.

## Dans ce dépôt
- Le **téléphone normalisé à huit chiffres** est l'identifiant ; il est vérifié par code SMS (simulé : affiché à l'écran) avant d'écrire, de commander ou de poster.
- Portes d'entrée limitées **par numéro** (`noyau/limitation.py`, `DEFAULT_THROTTLE_RATES`) ; une nouvelle route sensible reçoit sa limite.
- **Espace groupeur fermé tant que le dossier KYC n'est pas validé** ; console d'administration réservée aux comptes créés en interne.
- **Pièces KYC jamais servies publiquement** (`/medias/` refuse `kyc/`, vue dédiée `config/service/fichiers.py`) et jamais envoyées chez Cloudinary.
- Dans le fil public, l'auteur n'est pas identifiable par son numéro.
