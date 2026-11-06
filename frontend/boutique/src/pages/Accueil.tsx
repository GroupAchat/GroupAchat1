import { useState } from "react";
import type { CampagneResume, Categorie, Page } from "@commun/api/types";
import { FilCampagnes } from "@/composants/FilCampagnes";
import { useRequete } from "@commun/outils/requetes";
import { Squelette } from "@commun/composants/ui";

/**
 * Accueil Acheteur : Fil vidéo vertical immersif (Format Reels / TikTok).
 * Défilement naturel, vidéos de démonstration et boutons d'adhésion immédiats.
 */
export default function Accueil() {
  const [categorieActive, setCategorieActive] = useState("tous");

  const requeteCampagnes =
    categorieActive && categorieActive !== "tous"
      ? `/catalogue/campagnes/?categorie=${categorieActive}&tri=recent&page_size=50`
      : `/catalogue/campagnes/?tri=recent&page_size=50`;

  const { donnees, chargement } = useRequete<Page<CampagneResume>>(requeteCampagnes);
  const { donnees: categories } = useRequete<Categorie[]>("/catalogue/categories/");

  const campagnes = donnees?.results ?? [];

  if (chargement) {
    return (
      <div className="relative h-[calc(100dvh-4rem)] w-full overflow-hidden bg-slate-950 p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between pt-3">
          <Squelette className="h-8 w-32 rounded-xl bg-slate-800" />
          <Squelette className="h-8 w-16 rounded-full bg-slate-800" />
        </div>
        <div className="space-y-3 pb-8">
          <Squelette className="h-6 w-24 rounded-full bg-slate-800" />
          <Squelette className="h-8 w-4/5 rounded-xl bg-slate-800" />
          <Squelette className="h-6 w-1/3 rounded-xl bg-slate-800" />
          <Squelette className="h-12 w-full rounded-2xl bg-slate-800" />
        </div>
      </div>
    );
  }

  return (
    <FilCampagnes
      campagnes={campagnes}
      categories={categories ?? []}
      categorieActive={categorieActive}
      surChangerCategorie={(slug) => setCategorieActive(slug)}
    />
  );
}
