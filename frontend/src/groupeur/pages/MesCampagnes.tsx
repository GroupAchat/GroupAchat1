import { useState } from "react";
import { useEspaceGroupeur } from "../../api/EspaceGroupeurContexte";
import { formaterFrancs } from "../../domaine/format";
import { LIBELLE_CAMPAGNE, type Campagne } from "../../domaine/groupeur";
import Vignette from "../../composants/Vignette";
import JaugeParticipants from "../../composants/JaugeParticipants";
import Bouton from "../../ui/Bouton";
import EtatVide from "../../ui/EtatVide";
import { ErreurReseau, ListeEnChargement } from "../../ui/EtatReseau";
import { EnTeteGroupeur } from "../mise-en-page/ChromeGroupeur";

/**
 * Ses groupages, **tous**, et c'est ce que l'onglet promet.
 *
 * ⚠️ **Cet ecran n'existait pas.** L'onglet « Mes campagnes » ouvrait
 * directement l'ecran 15 sur `campagnes[0]` — c'est-a-dire sur **la plus
 * recente**, qui se trouvait etre le groupage annule. On arrivait donc sur
 * « 0 commande, 0 F CFA collectes », un tableau de commandes vide et une
 * repartition par quartier vide : l'application avait l'air de n'avoir aucune
 * donnee, alors qu'elle en avait six groupages pleins.
 *
 * Un onglet au pluriel qui ouvre un seul element est un piege a lui seul :
 * on ne sait pas qu'il y en a d'autres, et on ne sait pas pourquoi celui-la.
 *
 * ## Le tri
 *
 * **Ce qui demande une action d'abord**, puis ce qui tourne, puis ce qui est
 * fini. Un groupage cloture qui attend une decision bloque l'argent de
 * dizaines d'acheteurs ; un groupage livre n'attend plus rien. Trier par date
 * mettrait les deux au hasard l'un a cote de l'autre.
 */
const RANG = {
  "a-decider": 0,
  ouverte: 1,
  "en-cours": 2,
  livree: 3,
  annulee: 4,
} as const;

type Filtre = "tous" | "en-cours" | "terminees";

const FILTRES: { cle: Filtre; libelle: string }[] = [
  { cle: "tous", libelle: "Tous" },
  { cle: "en-cours", libelle: "En cours" },
  { cle: "terminees", libelle: "Terminés" },
];

function priorite(campagne: Campagne): number {
  /* Un groupage ouvert dont le temps est ecoule attend une decision, meme si
     son statut dit encore « ouverte » : c'est la meme regle que le serveur
     applique pour fabriquer la tache du tableau de bord. */
  if (campagne.statut === "ouverte" && campagne.heuresRestantes === 0) {
    return RANG["a-decider"];
  }
  return RANG[campagne.statut as keyof typeof RANG] ?? 9;
}

export default function MesCampagnes({
  onCampagne,
  onCreer,
}: {
  onCampagne: (campagne: Campagne) => void;
  onCreer?: () => void;
}) {
  const espace = useEspaceGroupeur();
  const [filtre, setFiltre] = useState<Filtre>("tous");

  if (espace.chargement) {
    return (
      <div className="pb-18">
        <EnTeteGroupeur titre="Mes campagnes" />
        <ListeEnChargement nombre={4} className="px-4 pt-4 md:px-8" />
      </div>
    );
  }

  if (espace.erreur) {
    return (
      <div className="pb-18">
        <EnTeteGroupeur titre="Mes campagnes" />
        <ErreurReseau
          erreur={espace.erreur}
          onReessayer={espace.recharger}
          role="groupeur"
        />
      </div>
    );
  }

  const terminee = (c: Campagne) =>
    c.statut === "livree" || c.statut === "annulee";

  const visibles = [...espace.campagnes]
    .filter((c) =>
      filtre === "tous"
        ? true
        : filtre === "terminees"
          ? terminee(c)
          : !terminee(c),
    )
    .sort((a, b) => priorite(a) - priorite(b));

  return (
    <div className="pb-18">
      <EnTeteGroupeur
        titre="Mes campagnes"
        sousTitre={`${espace.campagnes.length} groupage${
          espace.campagnes.length > 1 ? "s" : ""
        }`}
      />

      <div className="flex gap-2 px-4 pt-4 md:px-8">
        {FILTRES.map(({ cle, libelle }) => (
          <button
            key={cle}
            type="button"
            onClick={() => setFiltre(cle)}
            aria-pressed={filtre === cle}
            className={`rounded-full border px-4 py-2 text-sm font-medium ${
              filtre === cle
                ? "border-confiance bg-confiance-fond text-confiance"
                : "border-bordure text-texte-secondaire"
            }`}
          >
            {libelle}
          </button>
        ))}
      </div>

      {visibles.length === 0 ? (
        <div className="px-4 pt-6 md:px-8">
          <EtatVide
            titre="Aucun groupage dans cet état"
            explication="Changez de filtre, ou lancez votre premier groupage."
            registre="attente"
            actionLibelle={onCreer ? "Créer une campagne" : undefined}
            onAction={onCreer}
          />
        </div>
      ) : (
        <ul className="mt-4 px-4 md:px-8 lg:grid lg:grid-cols-2 lg:gap-3">
          {visibles.map((campagne) => (
            <li
              key={campagne.id}
              className="border-b border-filet last:border-b-0 lg:rounded-xl lg:border lg:border-bordure"
            >
              <button
                type="button"
                onClick={() => onCampagne(campagne)}
                className="flex w-full items-center gap-3 py-3 text-left active:bg-surface-douce lg:px-3"
              >
                <Vignette
                  photo={campagne.photo}
                  taille={48}
                  /* Un groupage termine est attenue : il est la, il ne
                     demande plus rien. */
                  attenuee={terminee(campagne)}
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-texte">
                    {campagne.produit}
                  </p>
                  <p className="text-sm text-texte-secondaire">
                    {LIBELLE_CAMPAGNE[campagne.statut] ?? campagne.statut}
                  </p>
                  {/* ⚠️ **La barre seulement sur un groupage en cours.** Sur un
                      groupage livre ou annule, elle montrerait un objectif
                      qu'il n'y a plus rien a atteindre — et sur un annule,
                      elle ressemblerait a un reproche. */}
                  {terminee(campagne) ? null : (
                    <div className="mt-1">
                      <JaugeParticipants
                        acheteursConfirmes={campagne.commandes}
                        objectif={campagne.objectifParticipants}
                        progression={campagne.progression}
                        taille="compacte"
                      />
                    </div>
                  )}
                </div>
                <p className="shrink-0 font-semibold text-texte">
                  {formaterFrancs(campagne.collecte)}
                </p>
              </button>
            </li>
          ))}
        </ul>
      )}

      {onCreer ? (
        <div className="mt-6 px-4 md:px-8 lg:max-w-xs">
          <Bouton role="groupeur" style="secondaire" onClick={onCreer}>
            Lancer un nouveau groupage
          </Bouton>
        </div>
      ) : null}
    </div>
  );
}
