# Style de code — Group Achat

Adapté du modèle `claude-template` : ce dépôt a ses propres conventions, écrites dans `CLAUDE.md` et le `README.md`. Elles priment. Ce qui suit les rend opérationnelles pour les agents. Les règles propres à Django et React sont dans `code-style-stack.md`.

## Langue
- **Tout en français** : identifiants (variables, fonctions, classes, modèles, champs, routes, fichiers), commentaires, docstrings, messages d'erreur, noms de tests. `Participation`, `date_limite`, `valider_retrait`, `test_on_ne_repond_pas_a_une_reponse`. Un fichier qui mélange `Participation` et `Order` coûte une traduction mentale à chaque lecture.
- Seuls restent en anglais les noms imposés par les bibliothèques (`get_queryset`, `useState`, `className`…).

## Taille et structure
- **Pas de limite de lignes imposée** : le dépôt a des fichiers de 400 à 900 lignes, et les découper n'est pas une tâche en soi. Mais un ajout **cohérent et séparable** de plus d'une centaine de lignes (une nouvelle règle métier, une tâche planifiée, un écran) va dans son propre module plutôt que d'allonger le plus gros fichier.
- Une fonction = une tâche ; retours anticipés plutôt qu'imbrication profonde.
- Pas de fichier fourre-tout `utils` / `helpers` : nommer par responsabilité (`hebergement.py`, `limitation.py`, `formats.ts`).
- Pas de valeur magique : constante nommée (`FRAIS_PLATEFORME_FCFA`, `DELAI_DECISION_JOURS`).

## Commentaires
- Ils expliquent **pourquoi**, pas quoi (`CLAUDE.md`, « Écrire du code ici »). Un commentaire qui paraphrase la ligne suivante est du bruit ; un commentaire qui dit « sans ça, deux acheteurs payaient la dernière place en même temps » sauve une heure.
- Docstring de module : ce que couvre le fichier et les choix non évidents.
- Pas de code commenté : git garde l'historique.

## Erreurs
- Côté API, suivre ce que fait déjà le dépôt : `ValidationError`, `PermissionDenied`, `NotFound` de DRF pour les cas HTTP ; une exception métier nommée dans le service (`ErreurPaiement`) convertie en réponse lisible dans la vue. Pas de `raise Exception` ni de `ValueError` pour un cas métier.
- Message d'erreur en français, compréhensible par l'utilisateur final : c'est lui qui le lit à l'écran (`ErreurApi.pourChamp` côté client).
- Échec toléré (notification, journal) : capturé et journalisé, jamais pour l'action principale (paiement, retrait, séquestre).

## Réponses API
- **Pas d'enveloppe** `{status, data}` : le dépôt renvoie les objets DRF tels quels, et la pagination par défaut est `PageNumberPagination` (20). Ne pas introduire d'enveloppe — le client `@commun/api/client` ne la lit pas.
- Erreurs de validation au format DRF (`{"champ": ["message"]}`), que `ErreurApi` sait lire.

## Données — décisions du projet (ne pas défaire)
- **Montants en entiers de FCFA** (`PositiveIntegerField`), jamais en décimal ni en flottant : le franc n'a pas de centime.
- **Téléphone normalisé à huit chiffres**, identifiant du compte.
- **Prix figé à la commande** : un palier franchi plus tard ne réécrit rien.
- **Séquestre par campagne**, contraintes en base contre une libération ou un remboursement supérieur au consigné.
- **Pièces KYC jamais publiques**, jamais chez Cloudinary.
- Dates stockées en UTC (`timezone.now()`), affichées dans le fuseau de l'utilisateur.

## Logs
- `logger = logging.getLogger(__name__)` ; jamais `print`. Jamais de mot de passe, code SMS, jeton ou numéro de pièce dans un log.

## Variables d'environnement
- **Un seul `.env`, à la racine**, lu par Django, Vite et Docker Compose. Pas de second fichier par dossier, ni `.env.production`, ni copie de sauvegarde.
- **`.env.exemple`** (en français) est le seul fichier d'environnement versionné : toute variable lue par le code y figure, avec une valeur factice.
- **`VITE_API_URL` reste vide** : le client retombe sur `/api`, même origine. Une adresse absolue rouvre le CORS.
- Claude ne lit ni ne modifie `.env` ; il peut seulement le créer en copiant `.env.exemple`.
