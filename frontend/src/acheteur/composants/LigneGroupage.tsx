import { type Groupage } from "../../domaine/groupage";
import { formaterFrancs } from "../../domaine/format";
import CompteurTemps from "./CompteurTemps";
import JaugeParticipants from "../../composants/JaugeParticipants";
import { IconeVerifie } from "../../ui/Icones";
import Vignette from "../../composants/Vignette";

/**
 * `LigneGroupage` — SPEC_ECRANS_FIGMA.md §2.3 (`LigneCampagne`, version liste),
 * mis en forme d'apres la maquette de l'ecran 2.
 *
 * **Ce n'est pas une carte.** Sur fond blanc, une carte blanche n'existe pas :
 * c'est une ligne, separee de la suivante par un filet de 1 px et par du vide.
 * Rien ne l'encadre, et seule la photo a des coins arrondis. Ce choix allege
 * aussi le rendu — une liste de lignes defile mieux qu'une liste de cartes
 * ombrees sur un telephone d'entree de gamme.
 *
 * Le prix est en `primaire` d'apres la maquette : orange sur blanc tient a
 * 4,62:1. Aucun prix barre, aucune pastille de reduction, aucun « au lieu
 * de » (§3).
 *
 * Le contenu d'une part n'est pas repris ici : c'est le point 8 de l'ecran 3,
 * et une ligne de liste ne porte que deux niveaux de hierarchie (§1.0,
 * regle 6).
 */
export default function LigneGroupage({
  groupage,
  onOuvrir,
}: {
  groupage: Groupage;
  onOuvrir: (groupage: Groupage) => void;
}) {
  const {
    produit,
    prixPart,
    acheteursConfirmes,
    objectifParticipants,
    progression,
    groupeur,
    heuresRestantes,
    photo,
    photoAlt,
  } = groupage;

  return (
    <li className="border-b border-filet last:border-b-0">
      <button
        type="button"
        onClick={() => onOuvrir(groupage)}
        className="flex w-full items-start gap-3 py-4 text-left active:bg-surface-douce"
      >
        <Vignette photo={photo} alt={photoAlt} />

        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-texte">{produit}</h3>

          {/* Le prix de la part, seul. Les frais de livraison sont une ligne
              distincte du recapitulatif de commande, jamais annonces ici. */}
          <p className="mt-1 text-xl font-bold text-primaire">
            {formaterFrancs(prixPart)}
          </p>

          <div className="mt-1.5">
            <CompteurTemps heuresRestantes={heuresRestantes} />
          </div>

          {/* « Par Mama Gro » — sobre, et ca ne suggere pas une fiche a ouvrir
              (§3). Le pseudonyme est tout ce que l'acheteur voit (§1.7). */}
          <p className="mt-1.5 flex items-center gap-1 text-sm text-texte-secondaire">
            <span className="truncate font-medium text-texte">{groupeur}</span>
            <IconeVerifie taille={13} className="shrink-0 text-confiance" />
          </p>
          {/* Version `compacte` : la ligne de liste est dense, et une barre
              de 8 px y prendrait la place d'un texte. */}
          <div className="mt-1.5">
            <JaugeParticipants
              acheteursConfirmes={acheteursConfirmes}
              objectif={objectifParticipants}
              progression={progression}
              taille="compacte"
            />
          </div>
        </div>
      </button>
    </li>
  );
}
