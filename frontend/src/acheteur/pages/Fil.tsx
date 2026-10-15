import { useEffect, useRef, useState } from "react";
import Bouton from "../../ui/Bouton";
import CompteurTemps from "../composants/CompteurTemps";
import JaugeParticipants from "../../composants/JaugeParticipants";
import EnTeteApplication from "../mise-en-page/EnTeteApplication";
import {
  IconeChevronHaut,
  IconePartager,
  IconeQuestion,
  IconeVerifie,
} from "../../ui/Icones";
import { type Groupage } from "../../domaine/groupage";
import { useCatalogue } from "../../api/CatalogueContexte";
import { useNotifications } from "../../api/NotificationsContexte";
import { ErreurReseau } from "../../ui/EtatReseau";
import { formaterFrancs } from "../../domaine/format";

/**
 * Ecran 1 — Accueil, le fil des groupages. SPEC_ECRANS_FIGMA.md, ecran 1.
 *
 * **Objectif : qu'un visiteur comprenne en trois secondes ce qu'il regarde, et
 * qu'il ait envie de faire defiler.** C'est l'ecran d'ouverture, sans aucun
 * compte (§1.5).
 *
 * Un groupage par ecran, defilement vertical : on glisse vers le haut pour le
 * suivant. C'est fait ici avec `scroll-snap`, pas avec une bibliotheque — le
 * navigateur le fait mieux et gratuitement, ce qui compte sur un telephone
 * d'entree de gamme.
 *
 * **C'est le seul ecran sombre de l'application** (§1.0) : media plein cadre,
 * texte blanc sur un voile. La rupture avec le reste — blanc, aere, orange —
 * est volontaire et doit etre nette.
 *
 * Le texte blanc n'est lisible que parce que le **voile** porte le contraste.
 * Le bouton reste en `primaire` `#CC4A00` : un bouton `marque` `#FF6A00` a
 * texte blanc ne tient qu'a 2,87:1, ici comme ailleurs.
 *
 * L'indice de defilement n'apparait que sur la premiere carte et disparait au
 * premier geste : sans lui, quelqu'un qui n'a jamais vu ce type d'interface
 * reste bloque sur le premier ecran.
 */
export default function Fil({
  onOuvrirGroupage,
  onRechercher,
  onQuestions,
  onPartager,
  onDemanderProduit,
}: {
  onOuvrirGroupage: (groupage: Groupage) => void;
  onRechercher: () => void;
  /**
   * Vers l'ecran 10.
   *
   * ⚠️ **L'ecran plein, et pas le panneau de la fiche.** Le fil occupe tout
   * l'ecran d'un telephone : il n'y a pas de coin ou poser un panneau, et le
   * fil n'existe pas sur ordinateur (§ecran 1).
   */
  onQuestions: (groupage: Groupage) => void;
  onPartager: (groupage: Groupage) => void;
  /** Vers l'ecran 11, depuis la fin du fil. */
  onDemanderProduit: () => void;
}) {
  const { groupages, chargement, erreur, recharger } = useCatalogue();
  /* La cloche vit dans la coquille ; cet ecran n'en lit que le
     compteur et de quoi l'ouvrir. */
  const cloche = useNotifications();
  const [aDefile, setADefile] = useState(false);
  const conteneur = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = conteneur.current;
    if (!element) {
      return;
    }
    const auDefilement = () => {
      if (element.scrollTop > 40) {
        setADefile(true);
      }
    };
    element.addEventListener("scroll", auDefilement, { passive: true });
    return () => element.removeEventListener("scroll", auDefilement);
  }, []);

  /**
   * ⚠️ **L'attente du fil est noire, pas blanche.**
   *
   * Le fil est un plein ecran sur fond noir derriere des photos ; y poser le
   * squelette gris clair des listes ferait un flash blanc a chaque ouverture
   * de l'application, puis un second quand les images arrivent. Sur un reseau
   * lent, ce flash dure une seconde et donne l'impression que l'application
   * se recharge.
   *
   * Pas de texte « chargement » non plus : il serait lu par-dessus la
   * premiere photo qui apparait. `aria-busy` suffit pour un lecteur d'ecran.
   */
  if (chargement) {
    return (
      <div className="relative h-dvh bg-black" aria-busy="true">
        <EnTeteApplication
          surMedia
          onActiverRecherche={onRechercher}
          notifications={cloche.nonLues}
          onNotifications={cloche.ouvrir}
        />
      </div>
    );
  }

  if (erreur) {
    return (
      <div className="relative flex h-dvh flex-col bg-white">
        <EnTeteApplication
          onActiverRecherche={onRechercher}
          notifications={cloche.nonLues}
          onNotifications={cloche.ouvrir}
        />
        <div className="flex flex-1 items-center justify-center">
          <ErreurReseau erreur={erreur} onReessayer={recharger} />
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-dvh bg-black">
      <EnTeteApplication
        surMedia
        onActiverRecherche={onRechercher}
        notifications={cloche.nonLues}
        onNotifications={cloche.ouvrir}
      />

      <div
        ref={conteneur}
        className="h-full snap-y snap-mandatory overflow-y-auto overscroll-contain"
      >
        {groupages.map((groupage, indice) => (
          <CarteFil
            key={groupage.id}
            groupage={groupage}
            premiere={indice === 0}
            indiceVisible={indice === 0 && !aDefile}
            onOuvrir={() => onOuvrirGroupage(groupage)}
            onQuestions={() => onQuestions(groupage)}
            onPartager={() => onPartager(groupage)}
          />
        ))}

        {/* Fin du fil (etats de l'ecran 1). */}
        <section className="flex h-full snap-start flex-col items-center justify-center bg-white px-8 text-center">
          <p className="text-lg font-semibold text-texte">
            Vous avez vu tous les groupages ouverts
          </p>
          <p className="mt-2 text-texte-secondaire">
            Dites-nous ce que vous cherchez : un groupeur peut le lancer.
          </p>
          <div className="mt-6 w-full max-w-72">
            <Bouton style="secondaire" onClick={onDemanderProduit}>
              Demander un produit
            </Bouton>
          </div>
        </section>
      </div>
    </div>
  );
}

/**
 * `CarteFil` (§2.1) — la carte plein ecran. Le composant le plus important de
 * l'application.
 */
function CarteFil({
  groupage,
  premiere,
  indiceVisible,
  onOuvrir,
  onQuestions,
  onPartager,
}: {
  groupage: Groupage;
  premiere: boolean;
  indiceVisible: boolean;
  onOuvrir: () => void;
  /* Le rail d'actions vit ici, donc ses deux gestes descendent jusqu'ici. */
  onQuestions: () => void;
  onPartager: () => void;
}) {
  return (
    <section className="relative h-full w-full snap-start overflow-hidden bg-surface-douce">
      {groupage.photo ? (
        <img
          src={groupage.photo}
          alt={groupage.photoAlt ?? groupage.produit}
          /* La premiere carte est visible d'emblee : elle ne doit pas etre
             differee, les suivantes si. */
          loading={premiere ? "eager" : "lazy"}
          fetchPriority={premiere ? "high" : "auto"}
          decoding="async"
          className="absolute inset-0 size-full object-cover"
        />
      ) : null}

      {/* Les deux voiles. Sans eux, aucun texte blanc n'est lisible sur une
          photo claire (§1.3). */}
      <div
        aria-hidden="true"
        className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-black/45 to-transparent"
      />
      <div
        aria-hidden="true"
        className="absolute inset-x-0 bottom-0 h-96 bg-gradient-to-t from-black/85 via-black/50 to-transparent"
      />

      {/* Rail d'actions vertical a droite. */}
      <div className="absolute right-3 bottom-80 flex flex-col items-center gap-4 text-white">
        <button
          type="button"
          onClick={onQuestions}
          className="flex flex-col items-center gap-0.5"
          aria-label={`Voir les ${groupage.questions} questions`}
        >
          <span className="flex size-12 items-center justify-center rounded-full bg-black/35">
            <IconeQuestion taille={24} />
          </span>
          <span className="text-xs font-medium">{groupage.questions}</span>
        </button>

        <button
          type="button"
          onClick={onPartager}
          className="flex flex-col items-center gap-0.5"
          aria-label="Partager ce groupage"
        >
          <span className="flex size-12 items-center justify-center rounded-full bg-black/35">
            <IconePartager taille={24} />
          </span>
          <span className="text-xs font-medium">Partager</span>
        </button>
      </div>

      {/* Bloc d'information en bas a gauche. */}
      {/* pb-24 : le bloc passe au-dessus de la barre de navigation de 72 px. */}
      <div className="absolute inset-x-0 bottom-0 px-4 pb-24">
        <CompteurTemps heuresRestantes={groupage.heuresRestantes} surMedia />

        <h2 className="mt-2 text-xl font-bold text-white">
          {groupage.produit}
        </h2>

        {/* Le prix seul. Aucun prix barre, aucune pastille de reduction (§3). */}
        <p className="mt-1 text-prix font-bold text-white">
          {formaterFrancs(groupage.prixPart)}
        </p>
        <p className="text-xs text-white/85">la part</p>

        {/* Variante `sombre` : texte blanc, gouttiere blanc transparent,
            remplissage `marque`. L'orange vif n'est ici qu'un **bloc plein**
            sur un aplat fonce, jamais du texte (§1.2). */}
        <div className="mt-2.5">
          <JaugeParticipants
            acheteursConfirmes={groupage.acheteursConfirmes}
            objectif={groupage.objectifParticipants}
            progression={groupage.progression}
            fond="sombre"
          />
        </div>

        <p className="mt-2 flex flex-wrap items-center gap-x-2 text-sm text-white">
          {/* Non cliquable : le pseudonyme est tout ce que l'acheteur voit, et
              il ne doit pas suggerer une fiche a ouvrir (§1.7, §3). */}
          <span className="inline-flex items-center gap-1">
            Par <strong className="font-semibold">{groupage.groupeur}</strong>
            <IconeVerifie taille={14} className="text-marque" />
          </span>
        </p>

        <div className="mt-4">
          <Bouton onClick={onOuvrir}>Voir le groupage</Bouton>
        </div>

        {indiceVisible ? (
          <p className="mt-2 flex items-center justify-center gap-1 text-xs text-white/80">
            <IconeChevronHaut taille={14} />
            Glisser vers le haut pour le groupage suivant
          </p>
        ) : (
          <div className="mt-2 h-5" />
        )}
      </div>
    </section>
  );
}
