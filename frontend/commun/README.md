# commun — le socle partagé

Ce que la boutique et la console utilisent toutes les deux. Rien d'autre.

| Dossier | Contenu |
|---|---|
| `src/api/` | client HTTP (jeton CSRF, erreurs lisibles) et types de l'API |
| `src/composants/` | boutons, champs, étiquettes, feuille, logo |
| `src/contexte/` | session, et la teinte qui suit le profil |
| `src/outils/` | formats (FCFA, dates, numéros) et crochets de requête |
| `src/index.css` | le système de design — couleurs, animations, thème sombre |
| `public/logos/` | la marque, déposée une seule fois |

**Ce dossier ne contient aucune page et aucune route.** Dès qu'un composant
ne sert qu'à une seule des deux applications, sa place est dans celle-là —
sinon le socle enfle et les deux interfaces se retrouvent couplées par des
choses qu'elles ne partagent pas vraiment.

On importe par chemin : `@commun/api/client`, jamais par le dossier.
