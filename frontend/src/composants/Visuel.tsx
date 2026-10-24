import { Package } from "lucide-react";

import { fusionner } from "@commun/composants/ui";

/**
 * L'image d'un produit, ou son remplacement quand il n'y en a pas.
 *
 * Le remplacement n'est pas un carré gris : c'est un dégradé **déterminé par
 * le nom du produit**, donc toujours le même pour un produit donné, avec son
 * initiale en grand. Un catalogue sans photos reste ainsi lisible et varié —
 * ce qui compte, puisque les groupeurs photographient leur stock au
 * téléphone et que certaines fiches partiront sans image.
 */

function degradeDe(graine: string): string {
  let somme = 0;
  for (const caractere of graine) somme = (somme * 31 + caractere.charCodeAt(0)) % 360;
  const complement = (somme + 38) % 360;
  return `linear-gradient(140deg, hsl(${somme} 68% 56%), hsl(${complement} 72% 42%))`;
}

export function Visuel({
  source,
  nom,
  className,
  rond,
}: {
  source?: string | null;
  nom: string;
  className?: string;
  rond?: boolean;
}) {
  if (source) {
    return (
      <img
        src={source}
        alt={nom}
        loading="lazy"
        className={fusionner("size-full object-cover", rond && "rounded-full", className)}
      />
    );
  }

  return (
    <div
      className={fusionner(
        "relative grid size-full place-items-center overflow-hidden",
        rond && "rounded-full",
        className,
      )}
      style={{ background: degradeDe(nom) }}
      aria-label={nom}
      role="img"
    >
      {/* Deux voiles clairs donnent du relief au dégradé et l'empêchent de
          paraître plat derrière un texte blanc. */}
      <span className="absolute -left-10 -top-12 size-44 rounded-full bg-white/18 blur-2xl" />
      <span className="absolute -bottom-16 -right-8 size-52 rounded-full bg-black/15 blur-2xl" />
      <span className="relative flex flex-col items-center gap-1 text-white/90">
        <Package className="size-8" strokeWidth={1.5} />
        <span className="text-4xl font-extrabold tracking-tight drop-shadow-sm">
          {nom.trim()[0]?.toUpperCase() ?? "?"}
        </span>
      </span>
    </div>
  );
}
