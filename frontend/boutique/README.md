# frontend — la boutique

Port **5173**. Acheteurs et groupeurs.

```bash
npm run dev              # depuis la racine
```

## Les choix d'interface

**Le fil vertical.** Sur téléphone, l'accueil est un fil aimanté : une
campagne par écran, qu'on parcourt au pouce. Sur ordinateur il cède la place
à une bannière et une grille — le geste du fil n'a pas de sens à la souris.
Voir [`src/composants/FilCampagnes.tsx`](src/composants/FilCampagnes.tsx).

**La couleur suit le profil.** L'acheteur vit dans l'orange, le groupeur dans
le bleu. Un seul attribut sur `<html>` (`data-profil`) redéfinit
`--teinte-accent` ; aucun composant n'a donc à savoir qui le regarde.

**Pas de photos ?** `Visuel` fabrique un dégradé déterminé par le nom du
produit, toujours le même pour un produit donné — un catalogue sans images
reste lisible et varié.

Le socle partagé vit dans [`../commun/`](../commun/README.md).
