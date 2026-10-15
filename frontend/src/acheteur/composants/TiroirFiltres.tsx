import { useEffect, useRef } from "react";
import type { Categorie } from "../../domaine/groupage";
import type { Filtres } from "../../domaine/filtres";
import PanneauFiltres from "./PanneauFiltres";
import Bouton from "../../ui/Bouton";
import { IconeFermer } from "../../ui/Icones";

/**
 * Les filtres dans un tiroir lateral, ouvert par un bouton.
 *
 * ## ⚠️ C'est un ecart assume a la spec
 *
 * Le §2 ecrit, a propos de la colonne de filtres : « **Jamais derriere un
 * bouton "Filtres"** — ce serait un menu cache (§1.0, simple 5). » La raison
 * est bonne : un filtre qu'on ne voit pas est un filtre qu'on n'utilise pas,
 * et surtout un filtre dont on **oublie qu'il est actif** — on croit alors
 * voir tout le catalogue alors qu'on en voit un quart.
 *
 * La demande de l'utilisateur est explicite et posterieure, donc elle
 * s'applique. Mais la raison du §2 reste vraie, et deux choses la ramenent a
 * peu de chose :
 *
 * - **les filtres actifs restent affiches en dehors du tiroir**, en puces, a
 *   cote du bouton (`PucesFiltresActifs`). Rien n'est donc cache : ce qui est
 *   range, c'est le **choix** des filtres, pas leur **etat** ;
 * - **le bouton porte le nombre de filtres actifs**, visible sans ouvrir.
 *
 * Si l'une de ces deux choses saute, le tiroir redevient le menu cache que le
 * §2 interdit.
 *
 * ## Le tiroir se referme apres le filtrage
 *
 * C'est la demande, et c'est aussi le bon comportement : on vient filtrer pour
 * **voir des resultats**, pas pour rester dans le panneau. Le bouton de bas de
 * tiroir annonce donc le nombre de resultats qui attendent — « Voir les 3
 * groupages » — ce qui transforme la fermeture en recompense plutot qu'en
 * geste supplementaire.
 *
 * ⚠️ **Il ne se ferme pas tout seul au premier clic sur une case.** Choisir
 * une categorie *puis* un prix demande deux gestes : fermer apres le premier
 * obligerait a rouvrir. On ferme sur une action explicite.
 */
export default function TiroirFiltres({
  ouvert,
  onFermer,
  filtres,
  onChanger,
  comptesCategories,
  total,
  nombreResultats,
}: {
  ouvert: boolean;
  onFermer: () => void;
  filtres: Filtres;
  onChanger: (filtres: Filtres) => void;
  comptesCategories: Record<Categorie, number>;
  total: number;
  /** Ce que le filtrage en cours laisse voir — annonce sur le bouton. */
  nombreResultats: number;
}) {
  const panneau = useRef<HTMLDivElement>(null);

  /**
   * Echap ferme, et le defilement de la page est bloque pendant l'ouverture.
   *
   * Sans le blocage, la molette fait defiler la page **derriere** le tiroir :
   * on le referme et on a perdu sa place dans le catalogue.
   */
  useEffect(() => {
    if (!ouvert) {
      return;
    }
    const auClavier = (evenement: KeyboardEvent) => {
      if (evenement.key === "Escape") {
        onFermer();
      }
    };
    const debordementInitial = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", auClavier);

    /* Le focus entre dans le tiroir : sans cela, la tabulation continue dans
       la page derriere, et un utilisateur au clavier se retrouve a parcourir
       un contenu qu'il ne voit plus. */
    panneau.current?.focus();

    return () => {
      document.body.style.overflow = debordementInitial;
      window.removeEventListener("keydown", auClavier);
    };
  }, [ouvert, onFermer]);

  if (!ouvert) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Le voile. Cliquer a cote ferme — c'est le geste qu'on tente en
          premier, et ne pas le servir donne l'impression d'etre coince. */}
      <button
        type="button"
        aria-label="Fermer les filtres"
        onClick={onFermer}
        className="absolute inset-0 bg-texte/40"
      />

      <div
        ref={panneau}
        role="dialog"
        aria-modal="true"
        aria-label="Filtrer les groupages"
        tabIndex={-1}
        className="relative flex h-full w-full max-w-sm flex-col bg-white shadow-[-8px_0_32px_rgba(29,25,22,0.18)] outline-none"
      >
        <div className="flex items-center justify-between border-b border-filet px-5 py-4">
          <h2 className="text-lg font-semibold text-texte">Filtrer</h2>
          <button
            type="button"
            onClick={onFermer}
            aria-label="Fermer"
            className="flex size-10 items-center justify-center rounded-full text-texte-secondaire hover:bg-surface-douce"
          >
            <IconeFermer taille={20} />
          </button>
        </div>

        {/* `overflow-y-auto` : la liste des categories peut depasser la hauteur
            d'un portable en paysage. */}
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <PanneauFiltres
            filtres={filtres}
            onChanger={onChanger}
            comptesCategories={comptesCategories}
            total={total}
          />
        </div>

        <div className="border-t border-filet p-4">
          {/* Le nombre est dans le libelle : on sait ce qu'on va trouver avant
              de fermer, donc on n'ouvre pas le tiroir deux fois pour verifier. */}
          <Bouton onClick={onFermer}>
            {nombreResultats === 0
              ? "Aucun groupage — revoir les filtres"
              : `Voir ${nombreResultats} groupage${nombreResultats > 1 ? "s" : ""}`}
          </Bouton>
        </div>
      </div>
    </div>
  );
}
