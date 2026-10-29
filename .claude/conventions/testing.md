# Tests

Règles communes à toutes les stacks. Outils et emplacements propres à la stack : `testing-stack.md`.

## Ce qui doit être testé
- Chaque endpoint : au moins un cas nominal et un cas d'erreur.
- Chaque règle métier (garde, plafond, transition de statut, calcul de montant) : un test par règle, y compris sa limite (pile au plafond, juste au-dessus).
- Chaque refus de sécurité : sans authentification, mauvais rôle, ressource d'un autre utilisateur, jeton expiré ou forgé.
- Ce qu'une réponse ne doit **pas** contenir : vérifier l'absence des données privées (téléphone, adresse, hash, notes internes).
- Ce qui ne doit **pas** se produire : un refus n'appelle pas le service externe, n'écrit rien en base (`assert_not_awaited`, total inchangé).
- Chaque bug corrigé : un test de régression qui échoue sans le correctif. Sa docstring (ou son commentaire) donne le symptôme, la date et la référence (`[[Bugs-Detectes]]`, `F33`).

## Comment tester
- Par l'interface publique : une route par un client HTTP de test, un service par ses méthodes publiques. Jamais les détails internes (fonctions privées, ordre des appels sans conséquence).
- Aucun accès réel au réseau, à la base de production, à Redis, à un LLM ou à un fournisseur de paiement dans les tests unitaires : ces dépendances sont remplacées à la frontière (repository, client externe).
- La base de test de Django est la norme (pas de mock de l'ORM). Un mock ne sert qu'à couper un service externe (Cloudinary, passerelle SMS) ou à vérifier un appel précis (« le remboursement n'a pas été exécuté »).
- Garde-fous globaux (fixture automatique, setup commun) qui coupent par défaut les accès externes ; un test qui en a besoin les réactive explicitement.
- Tests déterministes : horloge figée ou date injectée, aléa avec graine, aucune dépendance à l'ordre d'exécution. Chaque test construit son propre contexte.
- Tests d'intégration (vraie base, vrai Redis, flux complet) séparés des tests unitaires et lancés par une commande dédiée.

## Écriture
- Nom du test = phrase **en français** qui décrit le comportement attendu : `test_on_ne_repond_pas_a_une_reponse`, `test_un_numero_non_verifie_n_ecrit_pas`.
- Organisation par thème : sections `# ── Rejets ──` ou blocs `describe('POST /orders')`.
- Construction des données par des helpers en tête de fichier ou dans un module partagé (`_user()`, `createTestContext()`) ; pas de setup copié-collé.
- Une assertion d'erreur vérifie le code applicatif et le statut, pas seulement le type d'exception.

## Interdit
- Affaiblir un test pour le faire passer : le supprimer, le passer en `skip`, assouplir une assertion, changer la valeur attendue sans que la demande le justifie. Un test qui semble faux est signalé, pas modifié en silence.
- Tester le framework ou une librairie à la place de notre code.

## Avant de déclarer « terminé »
- La commande « Vérifier » de `CLAUDE.md` passe en entier ; la sortie réelle est lue, pas supposée.
