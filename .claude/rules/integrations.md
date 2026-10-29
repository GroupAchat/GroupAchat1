---
paths:
  - "backend/groupachat/noyau/hebergement.py"
  - "frontend/commun/src/outils/televersement.ts"
  - "**/*webhook*"
---

# Intégrations externes (API tierces, webhooks, stockage)

- Un client par fournisseur, seul endroit du code qui appelle son API.
- Timeout explicite sur chaque appel (connexion et lecture) ; jamais d'attente infinie.
- Retry avec backoff seulement sur erreur réseau ou 5xx, et seulement pour un appel idempotent (lecture, ou écriture avec clé d'idempotence). Jamais sur une 4xx.
- Réponse du fournisseur convertie en type interne à la frontière ; échec converti en erreur `external` du projet (503) avec la raison, sans renvoyer la réponse brute au client.
- Webhook entrant : vérifier la signature ou le secret avant de traiter le corps ; répondre vite en 2xx, traiter en tâche si c'est long ; un même événement reçu deux fois ne produit qu'un effet.
- Jamais de clé, token, code PIN ou corps de requête sensible dans les logs : l'identifiant de l'opération et le statut suffisent.
- Identifiants et URL du fournisseur dans la configuration ; environnement sandbox en développement et en test.
- Tests : client remplacé par un faux, aucun appel réseau réel ; cas timeout, 5xx, réponse invalide.
