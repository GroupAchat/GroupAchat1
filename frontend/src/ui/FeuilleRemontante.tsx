import { useEffect } from "react";
import { IconeFermer } from "./Icones";

/**
 * La feuille qui monte par-dessus l'ecran en cours — le modele decrit a
 * l'ecran 4 et repris partout ou l'on demande quelque chose sans quitter sa
 * page : connexion, question a poser, choix d'une option.
 *
 * **C'est une feuille, pas une page**, et la nuance porte toute la promesse du
 * §1.5 : l'ecran d'origine **reste visible derriere** sous un voile a 50 %,
 * donc l'utilisateur voit qu'il n'a pas quitte son parcours. La fermer le
 * ramene a son ecran **intact** — a condition que l'appelant n'ait pas demonte
 * cet ecran, ce qui est la seule chose a ne pas oublier en s'en servant.
 *
 * Coins superieurs 20, poignee de glissement, croix a droite, et **pas de
 * fleche de retour** : on superpose, on ne navigue pas.
 *
 * La touche Echap ferme, et le defilement de la page en dessous est bloque
 * pendant l'ouverture — sans quoi un geste destine a la feuille fait defiler
 * l'arriere-plan.
 *
 * Sur grand ecran elle se centre et se limite en largeur : une feuille qui
 * traverse 1 900 px ne ressemble plus a rien.
 */
export default function FeuilleRemontante({
  titre,
  onFermer,
  children,
}: {
  /** Nom accessible de la boite de dialogue. */
  titre: string;
  onFermer: () => void;
  children: React.ReactNode;
}) {
  useEffect(() => {
    const auClavier = (evenement: KeyboardEvent) => {
      if (evenement.key === "Escape") {
        onFermer();
      }
    };
    const defilementInitial = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", auClavier);
    return () => {
      document.body.style.overflow = defilementInitial;
      window.removeEventListener("keydown", auClavier);
    };
  }, [onFermer]);

  return (
    <div className="fixed inset-0 z-30">
      {/* L'ecran d'origine reste visible derriere, sous un voile a 50 %. */}
      <button
        type="button"
        aria-label="Fermer"
        onClick={onFermer}
        className="absolute inset-0 bg-black/50"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label={titre}
        className="absolute inset-x-0 bottom-0 mx-auto max-h-[92dvh] max-w-[430px] overflow-y-auto rounded-t-[20px] bg-white px-4 pt-3 pb-6 lg:bottom-auto lg:top-1/2 lg:max-h-[86dvh] lg:-translate-y-1/2 lg:rounded-xl"
      >
        <div className="flex items-center">
          <span
            aria-hidden="true"
            className="mx-auto h-1 w-10 rounded-full bg-bordure lg:hidden"
          />
          <button
            type="button"
            onClick={onFermer}
            aria-label="Fermer"
            className="absolute right-2 flex size-12 items-center justify-center text-texte-secondaire"
          >
            <IconeFermer />
          </button>
        </div>

        {children}
      </div>
    </div>
  );
}
