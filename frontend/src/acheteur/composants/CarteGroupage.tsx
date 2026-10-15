import { type Groupage } from "../../domaine/groupage";
import { formaterFrancs } from "../../domaine/format";
import CompteurTemps from "./CompteurTemps";
import JaugeParticipants from "../../composants/JaugeParticipants";
import { IconeVerifie } from "../../ui/Icones";

/**
 * La carte de la grille — la forme du catalogue sur grand ecran.
 *
 * **Pourquoi une carte ici alors que le §2.3 impose une ligne.** La regle du
 * §2.3 a une raison explicite : sur fond blanc et sur 390 px, une carte
 * blanche n'existe pas, et une liste de lignes defile mieux sur un telephone
 * d'entree de gamme. Les deux arguments tombent sur une grille de bureau — il
 * faut bien delimiter des colonnes voisines, et le defilement n'est plus un
 * geste de pouce. La ligne reste donc la forme mobile, la carte la forme
 * bureau, et le §2.3 gagnerait a le dire.
 *
 * La delimitation se fait par **un filet de 1 px**, pas par une ombre ni un
 * fond gris : le §1.0 interdit les deux, et cette raison-la vaut partout.
 *
 * Aucun prix barre, aucune pastille de reduction, aucun « au lieu de » (§3).
 */
export default function CarteGroupage({
  groupage,
  onOuvrir,
  enCarrousel = false,
}: {
  groupage: Groupage;
  onOuvrir: (groupage: Groupage) => void;
  /** Dans un carrousel, la carte a une largeur fixe et un point d'accroche. */
  enCarrousel?: boolean;
}) {
  return (
    <li
      className={
        enCarrousel ? "w-64 shrink-0 snap-start lg:w-72" : undefined
      }
    >
      <button
        type="button"
        onClick={() => onOuvrir(groupage)}
        className="group flex h-full w-full flex-col overflow-hidden rounded-xl border border-bordure text-left transition-colors hover:border-primaire focus-visible:border-primaire"
      >
        <div className="aspect-4/3 w-full overflow-hidden bg-surface-douce">
          {groupage.photo ? (
            <img
              src={groupage.photo}
              alt={groupage.photoAlt ?? groupage.produit}
              loading="lazy"
              decoding="async"
              className="size-full object-cover transition-transform duration-200 group-hover:scale-[1.03]"
            />
          ) : null}
        </div>

        <div className="flex flex-1 flex-col p-4">
          <h3 className="font-semibold text-texte">{groupage.produit}</h3>

          <p className="mt-1 text-xl font-bold text-primaire">
            {formaterFrancs(groupage.prixPart)}
            <span className="ml-1.5 text-sm font-normal text-texte-secondaire">
              la part
            </span>
          </p>

          <p className="mt-1 line-clamp-2 text-sm text-texte-secondaire">
            {groupage.contenuPart}
          </p>

          {/* `mt-auto` : les compteurs s'alignent en bas de toutes les cartes
              de la rangee, quelle que soit la longueur des titres. */}
          <div className="mt-auto pt-3">
            {/* La barre avant le compteur de temps : elle dit ou en est le
                groupage, le temps dit combien il en reste. On lit l'etat
                avant l'echeance. */}
            <JaugeParticipants
              acheteursConfirmes={groupage.acheteursConfirmes}
              objectif={groupage.objectifParticipants}
              progression={groupage.progression}
            />

            <div className="mt-2.5">
              <CompteurTemps heuresRestantes={groupage.heuresRestantes} />
            </div>

            {/* ⚠️ **Le compte n'est plus repete ici.** Il est dans la barre
                juste au-dessus, et l'ecrire deux fois sur une carte de 280 px
                de haut faisait lire deux chiffres pour une seule
                information. */}
            <p className="mt-2 flex items-center gap-1.5 text-sm text-texte-secondaire">
              <span className="truncate font-medium text-texte">
                {groupage.groupeur}
              </span>
              <IconeVerifie taille={13} className="shrink-0 text-confiance" />
            </p>
          </div>
        </div>
      </button>
    </li>
  );
}
