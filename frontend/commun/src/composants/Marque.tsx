import { LOGOS } from "@commun/composants/logos";
import { fusionner } from "@commun/composants/ui";

/**
 * Le logo Group Achat complet : l'emblème et la typographie de marque.
 * Utilise directement les fichiers SVG vectoriels du dossier public/logos/
 * (logo-horizontal.svg en couleur et logo-horizontal-blanc.svg sur fond sombre).
 */

const TAILLES = {
  /** Barres compactes. */
  compacte: "h-7",
  /** La barre du haut : optimisée mobile. */
  moyenne: "h-8",
  /** Écrans d'entrée, pages de présentation. */
  grande: "h-11",
} as const;

export function Marque({
  className,
  taille = "moyenne",
  variante = "couleur",
}: {
  className?: string;
  taille?: keyof typeof TAILLES;
  /** « blanc » pour les fonds colorés ou sombres. */
  variante?: "couleur" | "blanc";
}) {
  const blanc = variante === "blanc";
  const source = blanc ? LOGOS.horizontalBlanc : LOGOS.horizontal;
  const hauteur = TAILLES[taille];

  return (
    <img
      src={source}
      alt="Group Achat"
      className={fusionner("shrink-0 w-auto select-none", hauteur, className)}
      draggable={false}
    />
  );
}

/** L'emblème seul, sans le nom : favicon, pastilles, barres très étroites. */
export function Embleme({
  taille = 32,
  className,
}: {
  taille?: number;
  className?: string;
}) {
  return (
    <img
      src={LOGOS.marque}
      alt=""
      width={taille}
      height={taille}
      className={fusionner("shrink-0 select-none", className)}
      draggable={false}
      aria-hidden
    />
  );
}
