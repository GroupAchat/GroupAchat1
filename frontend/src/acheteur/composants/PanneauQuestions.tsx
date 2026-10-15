import { useEffect, useRef } from "react";
import Questions from "../pages/Questions";
import { type Groupage } from "../../domaine/groupage";
import { IconeFermer, IconeQuestion } from "../../ui/Icones";

/**
 * Les questions d'un groupage, dans un panneau pose sur la page.
 *
 * ## Pourquoi un panneau plutot qu'un ecran
 *
 * Poser une question fait quitter la fiche, et c'est precisement le mauvais
 * moment : on pose une question **parce qu'on hesite a commander**. Un ecran
 * plein remplace le produit par un formulaire, et il faut revenir en arriere
 * pour retrouver le prix dont on voulait parler. Le panneau laisse la fiche
 * derriere lui.
 *
 * ## ⚠️ Il ne reecrit pas le formulaire
 *
 * Il monte `Questions` en variante `panneau`, qui rend le meme corps que
 * l'ecran. Tout ce qui est delicat — le filtre de moderation du §15, la
 * connexion demandee au bouton et non a l'ouverture (§1.5), le refus du
 * serveur affiche sous le champ — n'existe qu'une fois. Un panneau qui
 * dupliquerait ce formulaire finirait par laisser passer un numero de
 * telephone que l'ecran, lui, bloque encore.
 *
 * ## Les regles du §1.7 valent ici aussi
 *
 * **Ce n'est pas une messagerie privee.** Les questions sont publiques et
 * filtrees avant publication, et l'encart qui le dit fait partie du corps :
 * il n'y a donc aucun moyen de l'oublier en passant par le panneau.
 */
export default function PanneauQuestions({
  groupage,
  telephone,
  onFermer,
  onSeConnecter,
}: {
  groupage: Groupage;
  telephone?: string;
  onFermer: () => void;
  onSeConnecter: () => void;
}) {
  const panneau = useRef<HTMLDivElement>(null);

  /* Echap ferme. C'est le geste attendu de tout ce qui se pose par-dessus une
     page, et son absence se remarque surtout au clavier : sans lui, il faut
     retrouver la croix a la souris. */
  useEffect(() => {
    const auClavier = (evenement: KeyboardEvent) => {
      if (evenement.key === "Escape") onFermer();
    };
    document.addEventListener("keydown", auClavier);
    return () => document.removeEventListener("keydown", auClavier);
  }, [onFermer]);

  /* Le focus entre dans le panneau a l'ouverture : sinon il reste sur le
     bouton flottant, derriere, et la premiere tabulation repart dans la page
     au lieu d'aller au champ de saisie. */
  useEffect(() => {
    panneau.current?.focus();
  }, []);

  return (
    <div
      ref={panneau}
      tabIndex={-1}
      role="dialog"
      aria-modal="false"
      aria-label={`Questions sur ${groupage.produit}`}
      /*
       * ⚠️ **`aria-modal="false"` et aucun voile**, a la difference d'une
       * feuille de connexion. Le panneau ne bloque pas la page : on doit
       * pouvoir relire la fiche pendant qu'on ecrit sa question, c'est tout
       * l'interet de ne pas avoir change d'ecran.
       *
       * Sur telephone il occupe le bas de l'ecran sur toute la largeur — un
       * panneau de 384 px dans un coin de 390 px n'est pas un coin. A partir
       * de `sm`, il se range dans l'angle.
       */
      className="fixed inset-x-0 bottom-0 z-30 flex max-h-[80dvh] flex-col rounded-t-2xl border border-bordure bg-white shadow-[0_-4px_24px_rgba(29,25,22,0.18)] sm:inset-x-auto sm:right-6 sm:bottom-6 sm:max-h-[min(34rem,80dvh)] sm:w-96 sm:rounded-2xl sm:shadow-[0_8px_32px_rgba(29,25,22,0.22)]"
    >
      <header className="flex shrink-0 items-center gap-2 border-b border-filet px-4 py-3">
        <IconeQuestion taille={18} className="shrink-0 text-primaire" />
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold text-texte">Questions</h2>
          {/* Sur quel produit on parle : le panneau peut rester ouvert alors
              qu'on a fait defiler la fiche loin du titre. */}
          <p className="truncate text-xs text-texte-secondaire">
            {groupage.produit}
          </p>
        </div>
        <button
          type="button"
          onClick={onFermer}
          aria-label="Fermer les questions"
          className="flex size-10 shrink-0 items-center justify-center rounded-full text-texte-secondaire hover:bg-surface-douce"
        >
          <IconeFermer taille={18} />
        </button>
      </header>

      {/* Le corps defile a l'interieur du panneau, pas la page derriere. */}
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        <Questions
          groupage={groupage}
          estBureau={false}
          telephone={telephone}
          onRetour={onFermer}
          onSeConnecter={onSeConnecter}
          variante="panneau"
        />
      </div>
    </div>
  );
}
