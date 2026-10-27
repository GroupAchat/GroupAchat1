---
paths:
  - "*/ai/**"
  - "**/prompts/**"
  - "**/*llm*"
  - "**/*embedding*"
---

# Code IA (LLM, agents, RAG)

- Prompts dans des fichiers dédiés et versionnés (`prompts/`), jamais en chaîne au milieu de la logique.
- Sortie structurée validée par un schéma (Pydantic, zod) ; échec de validation → nouvelle tentative limitée, puis repli explicite.
- Timeout, nombre maximal de tentatives et d'itérations (`recursion_limit`) sur chaque appel ; modèle de repli si le fournisseur tombe.
- Le LLM ne déclenche jamais seul une action sensible (paiement, envoi, suppression) : validation par le code ou par l'utilisateur.
- Données personnelles envoyées au modèle réduites au nécessaire ; pas de numéro, adresse ou token dans un prompt sans besoin.
- Coût et latence journalisés par appel (modèle, tokens, durée).
- Modification d'un prompt ou d'un nœud de graphe : relancer le jeu d'évaluation (`evals/`) et noter le résultat dans `mapper/`.
- Tests unitaires : LLM remplacé (réponse JSON fixe, ou échec) ; le texte de secours est testé.
