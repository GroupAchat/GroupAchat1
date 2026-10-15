import { useState } from "react";
import { formaterFrancs } from "../../domaine/format";
import { LIBELLE_QUARTIER } from "../../domaine/groupage";
import type { DemandeAgregee } from "../../domaine/groupeur";
import { useEspaceGroupeur } from "../../api/EspaceGroupeurContexte";
import { EnTeteGroupeur } from "../mise-en-page/ChromeGroupeur";
import Bouton from "../../ui/Bouton";
import Encart from "../../ui/Encart";
import { IconeGroupage } from "../../ui/Icones";

/**
 * Ecran 19 — Fil des demandes, cote groupeur. SPEC_ECRANS_FIGMA.md, ecran 19.
 *
 * **Objectif : transformer une masse de demandes en decision commerciale.**
 *
 * **Agrege, jamais une liste brute.** Trente-deux demandes identiques les unes
 * sous les autres ne sont pas une decision, c'est une file d'attente. Une
 * carte par produit, avec le nombre de personnes, le quartier, le budget moyen
 * et le volume estime : de quoi decider en trois secondes si ca vaut une
 * campagne.
 *
 * **« Lancer une campagne » ouvre l'ecran 14 pre-rempli** — produit, quantite
 * estimee, quartier. C'est tout l'interet de l'ecran : sans ce
 * pre-remplissage, il ne ferait que montrer une opportunite sans aider a la
 * saisir.
 */
type Filtre = "mon-quartier" | "toutes" | "cette-semaine";

export default function FilDemandes({
  onRetour,
  onLancerCampagne,
}: {
  onRetour: () => void;
  onLancerCampagne: (demande: DemandeAgregee) => void;
}) {
  const [filtre, setFiltre] = useState<Filtre>("toutes");

  const { demandes } = useEspaceGroupeur();

  const listees = demandes.filter((demande) => {
    if (filtre === "cette-semaine") {
      return demande.joursEcoules <= 7;
    }
    if (filtre === "mon-quartier") {
      return demande.quartier === "Agoe";
    }
    return true;
  });

  return (
    <div className="pb-18">
      <EnTeteGroupeur titre="Demandes" onRetour={onRetour} />

      <div
        role="group"
        aria-label="Filtrer les demandes"
        className="defilement-discret flex gap-2 overflow-x-auto px-4 pt-4"
      >
        {(
          [
            ["mon-quartier", "Mon quartier"],
            ["toutes", "Toutes"],
            ["cette-semaine", "Cette semaine"],
          ] as const
        ).map(([cle, libelle]) => (
          <button
            key={cle}
            type="button"
            aria-pressed={filtre === cle}
            onClick={() => setFiltre(cle)}
            className={`inline-flex min-h-12 shrink-0 items-center rounded-full border px-4 text-sm font-medium whitespace-nowrap ${
              filtre === cle
                ? "border-confiance bg-confiance-fond text-confiance"
                : "border-bordure text-texte"
            }`}
          >
            {libelle}
          </button>
        ))}
      </div>

      <ul className="mt-4 space-y-3 px-4">
        {listees.map((demande) => (
          <li
            key={demande.id}
            className="rounded-xl border border-bordure p-4"
          >
            <h2 className="font-semibold text-texte">{demande.produit}</h2>

            <p className="mt-1 flex flex-wrap items-center gap-x-1.5 text-sm text-texte-secondaire">
              <IconeGroupage taille={15} />
              <strong className="font-semibold text-texte">
                {demande.personnes} personnes
              </strong>
              <span aria-hidden="true">·</span>
              {LIBELLE_QUARTIER[demande.quartier]}
              <span aria-hidden="true">·</span>
              {demande.joursEcoules} jours
            </p>

            <dl className="mt-3 space-y-0.5 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-texte-secondaire">
                  Budget moyen indiqué
                </dt>
                <dd className="font-medium text-texte">
                  {formaterFrancs(demande.budgetMoyen)}
                </dd>
              </div>
              {/* La ligne ne s'affiche que s'il y a quelque chose a dire :
                  un libelle suivi d'une case vide laisse croire a une panne. */}
              {demande.volumeEstime ? (
                <div className="flex justify-between gap-4">
                  <dt className="text-texte-secondaire">Quantité demandée</dt>
                  <dd className="font-medium text-texte">
                    le plus souvent {demande.volumeEstime}
                  </dd>
                </div>
              ) : null}
            </dl>

            <div className="mt-4">
              <Bouton role="groupeur" onClick={() => onLancerCampagne(demande)}>
                Lancer une campagne
              </Bouton>
            </div>

            {/*
              ⚠️ **« Voir les N demandes » a été retiré, et il ne doit pas
              revenir.**

              Le bouton ne faisait rien, et le brancher aurait été une faute :
              il promettait la liste des demandes une par une, alors qu'une
              demande individuelle porte le numéro de celui qui l'a déposée.
              La servir au groupeur lui donnerait exactement le fichier de
              clients que l'anonymat lui refuse partout ailleurs — et c'est
              ce qui protège le modèle contre la désintermédiation.

              L'API s'y refuse d'ailleurs explicitement : la route `demandes`
              **n'agrège que par produit et quartier**. « 14 personnes à Agoè
              veulent du riz » est tout ce qu'il y a à savoir pour décider de
              lancer un groupage, et c'est déjà affiché sur cette carte.
            */}
          </li>
        ))}
      </ul>

      <div className="px-4 pt-4">
        <Encart variante="info" role="groupeur">
          Les produits les plus demandés sont ceux où vous avez le moins de
          concurrence.
        </Encart>
      </div>
    </div>
  );
}
