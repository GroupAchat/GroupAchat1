import { motion } from "framer-motion";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { parametres } from "@/api/client";
import type { CampagneResume, Categorie, Page } from "@/api/types";
import { CarteCampagne, SqueletteCarte } from "@/composants/CarteCampagne";
import { EtatVide, fusionner } from "@/composants/ui";
import { useRequete } from "@/outils/requetes";

const TRIS = [
  { cle: "recent", libelle: "Récentes" },
  { cle: "fin_proche", libelle: "Fin proche" },
  { cle: "prix", libelle: "Prix croissant" },
  { cle: "populaire", libelle: "Populaires" },
];

/** Le catalogue complet : recherche, rayons, tri. */
export default function Catalogue() {
  const [params, setParams] = useSearchParams();
  const [recherche, setRecherche] = useState(params.get("recherche") ?? "");
  const [differee, setDifferee] = useState(recherche);
  const [filtresOuverts, setFiltresOuverts] = useState(false);
  const champ = useRef<HTMLInputElement>(null);

  const categorie = params.get("categorie") ?? "";
  const tri = params.get("tri") ?? "recent";

  // On attend une pause de frappe avant d'interroger l'API : une requête par
  // lettre saturerait le réseau pour rien, surtout sur une connexion mobile.
  useEffect(() => {
    const minuteur = setTimeout(() => setDifferee(recherche), 320);
    return () => clearTimeout(minuteur);
  }, [recherche]);

  useEffect(() => {
    if (params.get("focus")) champ.current?.focus();
  }, [params]);

  const { donnees, chargement } = useRequete<Page<CampagneResume>>(
    `/catalogue/campagnes/${parametres({
      recherche: differee,
      categorie,
      tri,
      page_size: 24,
    })}`,
    [differee, categorie, tri],
  );
  const { donnees: rayons } = useRequete<Categorie[]>("/catalogue/categories/");

  const definir = (cle: string, valeur: string) => {
    const suivants = new URLSearchParams(params);
    if (valeur) suivants.set(cle, valeur);
    else suivants.delete(cle);
    suivants.delete("focus");
    setParams(suivants, { replace: true });
  };

  const campagnes = donnees?.results ?? [];
  const rayonsPlats = (rayons ?? []).flatMap((rayon) => [rayon, ...rayon.sous_categories]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <div className="verre sticky top-16 z-30 -mx-4 space-y-3 px-4 py-3">
        <div className="flex gap-2">
          <div className="surface flex h-12 flex-1 items-center gap-2 rounded-2xl px-4 focus-within:border-[color:var(--color-accent)]">
            <Search className="texte-doux size-4 shrink-0" />
            <input
              ref={champ}
              value={recherche}
              onChange={(evenement) => setRecherche(evenement.target.value)}
              placeholder="Riz, smartphone, ciment…"
              className="w-full bg-transparent text-[0.95rem] outline-none"
              aria-label="Rechercher une campagne"
            />
            {recherche && (
              <button onClick={() => setRecherche("")} aria-label="Effacer">
                <X className="texte-doux size-4" />
              </button>
            )}
          </div>
          <button
            onClick={() => setFiltresOuverts((ouvert) => !ouvert)}
            className={fusionner(
              "grid size-12 shrink-0 place-items-center rounded-2xl transition-colors sm:hidden",
              filtresOuverts
                ? "degrade-accent text-white"
                : "surface",
            )}
            aria-label="Filtres"
          >
            <SlidersHorizontal className="size-4" />
          </button>
        </div>

        <div
          className={fusionner(
            "sans-barre flex gap-2 overflow-x-auto pb-1",
            !filtresOuverts && "hidden sm:flex",
          )}
        >
          <Pastille actif={!categorie} surClic={() => definir("categorie", "")}>
            Tous
          </Pastille>
          {rayonsPlats.map((rayon) => (
            <Pastille
              key={rayon.id}
              actif={categorie === rayon.slug}
              surClic={() => definir("categorie", rayon.slug)}
            >
              {rayon.nom}
            </Pastille>
          ))}
        </div>

        <div
          className={fusionner(
            "sans-barre flex gap-2 overflow-x-auto",
            !filtresOuverts && "hidden sm:flex",
          )}
        >
          {TRIS.map((option) => (
            <button
              key={option.cle}
              onClick={() => definir("tri", option.cle)}
              className={fusionner(
                "shrink-0 rounded-full px-3 py-1 text-xs font-semibold transition-colors",
                tri === option.cle
                  ? "bg-accent-doux text-[color:var(--color-accent-fort)]"
                  : "texte-doux",
              )}
            >
              {option.libelle}
            </button>
          ))}
        </div>
      </div>

      <p className="texte-doux mt-4 text-sm">
        {chargement
          ? "Recherche…"
          : `${donnees?.count ?? 0} campagne${(donnees?.count ?? 0) > 1 ? "s" : ""}`}
      </p>

      <motion.div layout className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {chargement
          ? Array.from({ length: 6 }, (_, rang) => <SqueletteCarte key={rang} />)
          : campagnes.map((campagne, rang) => (
              <CarteCampagne key={campagne.id} campagne={campagne} index={rang} />
            ))}
      </motion.div>

      {!chargement && campagnes.length === 0 && (
        <EtatVide
          icone={<Search className="size-7" />}
          titre="Rien ne correspond"
          texte="Essayez un autre mot, ou publiez une demande : un groupeur peut s'en saisir."
        />
      )}
    </div>
  );
}

function Pastille({
  actif,
  surClic,
  children,
}: {
  actif: boolean;
  surClic: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={surClic}
      className={fusionner(
        "shrink-0 rounded-full px-4 py-2 text-sm font-semibold transition-all",
        actif
          ? "degrade-accent text-white shadow-md"
          : "surface hover:border-[color:var(--color-accent)]",
      )}
    >
      {children}
    </button>
  );
}
