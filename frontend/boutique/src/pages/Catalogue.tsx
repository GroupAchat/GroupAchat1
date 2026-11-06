import { motion } from "framer-motion";
import { Search, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { parametres } from "@commun/api/client";
import type { CampagneResume, Categorie, Page } from "@commun/api/types";
import { CarteCampagne, SqueletteCarte } from "@/composants/CarteCampagne";
import { EtatVide, fusionner } from "@commun/composants/ui";
import { useRequete } from "@commun/outils/requetes";

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
      page_size: 50,
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
    <div className="w-full space-y-4 px-4 py-4 pb-12">
      <div className="space-y-3">
        <div className="surface flex h-11 items-center gap-2 rounded-2xl border border-slate-200/90 px-3.5 focus-within:border-[color:var(--color-accent)] shadow-2xs">
          <Search className="texte-doux size-4 shrink-0 text-slate-400" />
          <input
            ref={champ}
            value={recherche}
            onChange={(evenement) => setRecherche(evenement.target.value)}
            placeholder="Rechercher (riz, ciment, smartphone…)"
            className="w-full bg-transparent text-xs outline-none"
            aria-label="Rechercher une campagne"
          />
          {recherche && (
            <button onClick={() => setRecherche("")} aria-label="Effacer">
              <X className="texte-doux size-4" />
            </button>
          )}
        </div>

        <div className="sans-barre -mx-4 flex gap-1.5 overflow-x-auto px-4 pb-1">
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

        <div className="sans-barre -mx-4 flex gap-1.5 overflow-x-auto px-4">
          {TRIS.map((option) => (
            <button
              key={option.cle}
              onClick={() => definir("tri", option.cle)}
              className={fusionner(
                "shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors",
                tri === option.cle
                  ? "bg-accent-doux text-[color:var(--color-accent-fort)]"
                  : "surface text-slate-500",
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

      <motion.div layout className="mt-4 grid gap-4 grid-cols-1">
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
          texte="Essayez un autre mot, ou publiez une demande : un OAG peut s'en saisir."
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
