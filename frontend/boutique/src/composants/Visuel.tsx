import { Package } from "lucide-react";

import { fusionner } from "@commun/composants/ui";

/**
 * L'image d'un produit, ou son remplacement quand il n'y en a pas.
 *
 * Le remplacement n'est pas un carré gris : c'est un dégradé **déterminé par
 * le nom du produit**, donc toujours le même pour un produit donné, avec son
 * initiale en grand. Un catalogue sans photos reste ainsi lisible et varié —
 * ce qui compte, puisque les OAG photographient leur stock au
 * téléphone et que certaines fiches partiront sans image.
 */

function degradeDe(graine: string): string {
  let somme = 0;
  for (const caractere of graine) somme = (somme * 31 + caractere.charCodeAt(0)) % 360;
  const complement = (somme + 38) % 360;
  return `linear-gradient(140deg, hsl(${somme} 68% 56%), hsl(${complement} 72% 42%))`;
}

const IMAGES_PAR_DEFAUT: Array<{ motif: RegExp; url: string }> = [
  {
    motif: /riz/i,
    url: "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=800&q=80",
  },
  {
    motif: /smartphone|téléphone|itel|infinix|tecno|iphone/i,
    url: "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=800&q=80",
  },
  {
    motif: /écouteur|ecouteur|audio|casque|oraimo/i,
    url: "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=800&q=80",
  },
  {
    motif: /matelas|dolidol|lit|chambre/i,
    url: "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80",
  },
  {
    motif: /huile|dinor|végétale/i,
    url: "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=800&q=80",
  },
  {
    motif: /pagne|wax|vlisco|tissu|mode/i,
    url: "https://images.unsplash.com/photo-1528459801416-a9e53bbf4e17?auto=format&fit=crop&w=800&q=80",
  },
  {
    motif: /congélateur|congelateur|réfrigérateur|frigo|hisense|électromén/i,
    url: "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?auto=format&fit=crop&w=800&q=80",
  },
  {
    motif: /solaire|chargeur|panneau|batterie/i,
    url: "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=800&q=80",
  },
  {
    motif: /ciment|fortis|batiment|construction/i,
    url: "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=800&q=80",
  },
];

function trouverImageRepli(nom: string): string | null {
  for (const item of IMAGES_PAR_DEFAUT) {
    if (item.motif.test(nom)) return item.url;
  }
  return null;
}

export function Visuel({
  source,
  nom,
  className,
  rond,
  mode = "contain",
}: {
  source?: string | null;
  nom: string;
  className?: string;
  rond?: boolean;
  mode?: "contain" | "cover";
}) {
  const imageEffective = source || trouverImageRepli(nom);

  if (imageEffective) {
    return (
      <img
        src={imageEffective}
        alt={nom}
        loading="lazy"
        className={fusionner(
          "size-full",
          mode === "contain" ? "object-contain p-1" : "object-cover",
          rond && "rounded-full",
          className,
        )}
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
