# admin — la console d'administration

Port **5174**. Réservée à l'équipe : vérification des dossiers KYC,
supervision du séquestre, libération des décaissements, modération du fil.

```bash
npm run dev:admin        # depuis la racine
```

Un dossier à part, et non une page de plus dans la boutique : la frontière
entre les deux est réelle. Ce n'est pas pour autant une mesure de sécurité —
**c'est l'API qui garde ses routes** derrière `EstAdministrateur`. La
séparation sert à ce que personne ne se fie à une frontière qui n'existerait
que dans le routage du navigateur.

Le socle partagé vit dans [`../commun/`](../commun/README.md) : la console
n'a sa propre copie ni du client API, ni de la session.
