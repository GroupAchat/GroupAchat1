/**
 * Les chemins de la marque, au même endroit.
 *
 * Les fichiers vivent dans `public/logos/` : Vite les sert tels quels, sans
 * les passer par la construction. **Remplacer un fichier par le vôtre suffit
 * donc à changer le logo partout**, sans toucher à une seule ligne de code —
 * à condition de garder le nom.
 *
 * Si vous fournissez un format différent du SVG (PNG, WebP), c'est ici, et
 * nulle part ailleurs, qu'il faut corriger l'extension.
 *
 * Voir `public/logos/LISEZ-MOI.md` pour ce qu'attend chaque emplacement.
 */
export const LOGOS = {
  /** Marque + texte, sur fond clair. Barre du haut, écrans d'entrée. */
  horizontal: "/logos/logo-horizontal.svg",

  /** La même, en blanc, pour les fonds colorés ou sombres. Facultatif. */
  horizontalBlanc: "/logos/logo-horizontal-blanc.svg",

  /** La marque seule, sans texte. Barre compacte, favicon, pastilles. */
  marque: "/logos/marque.svg",

  /** Le verrouillage complet, pour une page de présentation. Facultatif. */
  complet: "/logos/logo-complet.svg",
} as const;

export type NomLogo = keyof typeof LOGOS;
