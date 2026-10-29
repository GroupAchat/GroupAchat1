# Style de code — Django / DRF et React / Vite, tels que ce dépôt les écrit

## Django / DRF
- **Modèles** : `TextChoices` pour les statuts (`Campagne.Statut.EN_COURS`), contraintes en base (`CheckConstraint`, `UniqueConstraint`) pour toute règle d'argent ou d'unicité — le code seul ne suffit pas. Montants : `PositiveIntegerField` en FCFA.
- **Migrations** : `python manage.py makemigrations <sujet>`, relues avant d'être gardées ; jamais modifier une migration existante.
- **Sérialiseurs** (`serialiseurs.py`) : forme et validation ; pas d'écriture métier dans `create()` / `update()` quand une règle s'applique — c'est le service qui écrit.
- **Vues** (`vues.py`, `espaces/*.py`) : `ViewSet` ou `APIView`, permission explicite (défaut du projet : `IsAuthenticatedOrReadOnly`, permissions de rôle dans `noyau/permissions.py`), queryset filtré par propriétaire, `select_related` / `prefetch_related` sur les listes, `@action` pour une transition (`publier`, `cloturer`, `maintenir`, `annuler`, `retrait`).
- **Services** (`services.py`) : fonctions nommées par l'action (`encaisser`, `rembourser`, `cloturer`, `valider_retrait`), `@transaction.atomic`, `select_for_update()` sur la ligne disputée, exception métier nommée (`ErreurPaiement`).
- **Limitation de débit** : les portes d'entrée du compte sont limitées par numéro (`noyau/limitation.py`, `DEFAULT_THROTTLE_RATES`) ; une nouvelle route sensible (code, connexion, paiement) reçoit sa limite.
- **Authentification** : `SessionAuthentication` + CSRF. Pas de JWT.
- **Configuration** : `settings.py` lit `.env` racine par `python-dotenv` ; une nouvelle variable va aussi dans `.env.exemple`.
- **Jeu de démonstration** : `charger_demo` porte un `VERSION_DEMO` — **à incrémenter dès qu'on touche au jeu**, sinon les ajouts n'apparaissent jamais sur un serveur déjà démarré.
- Typage : annotations sur les fonctions de service et les fixtures ; `from __future__ import annotations` comme le reste du dépôt.

## React / Vite / TypeScript
- React 19, TypeScript strict, React Router 7, Tailwind CSS v4, `framer-motion`, `lucide-react`.
- Composants en `PascalCase.tsx` et **noms français** (`CarteCampagne`, `Jauge`, `FicheCampagne`) ; un composant principal par fichier.
- Couleurs, animations et thème sombre viennent de `commun/src/index.css` : pas de couleur en dur dans une page.
- Données : crochets de `commun/src/outils/requetes.ts` et client `@commun/api/client` ; états chargement / erreur / vide gérés à chaque écran.
- Formats d'affichage (FCFA, dates, numéros) par `commun/src/outils/formats.ts`, jamais refaits à la main.
- Mobile d'abord : chaque écran se vérifie à 390 px de large.
- Aucun secret côté client ; la seule variable publique utile est `VITE_API_URL`, **vide**.
