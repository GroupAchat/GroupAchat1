import { useState } from "react";
import CodeLivraison from "../composants/CodeLivraison";
import Vignette from "../../composants/Vignette";
import type { Commande, StatutCommande } from "../../domaine/commande";
import { formaterDateCourte, formaterFrancs } from "../../domaine/format";
import { LIBELLE_QUARTIER } from "../../domaine/groupage";
import EnTeteEcran from "../mise-en-page/EnTeteEcran";
import PiedPage from "../mise-en-page/PiedPage";
import Bouton from "../../ui/Bouton";
import FeuilleRefusColis from "../composants/FeuilleRefusColis";
import Encart from "../../ui/Encart";
import FriseEtapes from "../../ui/FriseEtapes";
import { IconeQuestion, IconeRetour } from "../../ui/Icones";
import Statut from "../../ui/Statut";

/**
 * Ecran 9 — Detail d'une commande et suivi. SPEC_ECRANS_FIGMA.md, ecran 9.
 *
 * **Objectif : porter le suivi et le code de livraison.**
 *
 * **Aucun contact du groupeur** (§1.7) : ni numero, ni bouton d'appel, nulle
 * part. A la place, « Une question ? » renvoie vers les questions publiques de
 * l'ecran 10. C'est cette absence qui rend l'anonymat tenable des deux cotes,
 * et c'est elle qui protege le modele.
 *
 * **Les six etats racontent tout le circuit**, et chacun change ce que l'ecran
 * promet. Deux formulations a ne pas melanger :
 *
 * - tant que le groupage n'est pas cloture, c'est la **detention des fonds**
 *   qui rassure : « vos 5 000 F sont detenus par Group Achat » ;
 * - une fois cloture, **le groupeur a deja ete paye**. Ce n'est donc plus la
 *   detention qui porte, c'est la **garantie** : « Group Achat garantit votre
 *   livraison ». Ecrire « votre argent est bloque jusqu'a la livraison » a ce
 *   stade serait faux (§1.7).
 *
 * Le bouton « Refuser le colis » n'apparait **que** pendant la livraison : une
 * fois le colis accepte, la contestation n'est plus possible, et c'est annonce
 * depuis l'ecran 3.
 */
export default function DetailCommande({
  commande,
  estBureau,
  onRetour,
  onQuestions,
  onRefuse,
}: {
  commande: Commande;
  estBureau: boolean;
  onRetour: () => void;
  onQuestions: () => void;
  /**
   * Appele apres un refus accepte par le serveur.
   *
   * ⚠️ **La commande vient en propriete, donc l'ecran ne peut pas la mettre a
   * jour lui-meme.** Sans ce rappel, le statut afficherait encore « en cours
   * de livraison » apres un refus enregistre, et le bouton « Refuser le
   * colis » resterait la — on croirait que rien n'a ete pris.
   */
  onRefuse: () => void;
}) {
  const { groupage, quantite, position, statut, total } = commande;

  /** La feuille « Refuser le colis » de l'ecran 9. */
  const [refusOuvert, setRefusOuvert] = useState(false);

  const corps = (
    <div className="space-y-6">
      <div>
        <Statut statut={statut} />
      </div>

      {/* Chaque etat dit ce qui se passe, et ce qu'on promet a ce stade. */}
      <MessageDEtat statut={statut} commande={commande} />

      {/* Le code n'existe que pendant la livraison. */}
      {statut === "en-livraison" ? (
        <div>
          <CodeLivraison code={commande.codeLivraison} />
          <button
            type="button"
            onClick={() => {
              /* En plein soleil, un ecran sombre ne se scanne pas. L'API
                 d'ecran n'existe pas sur le web : le bouton est la pour que la
                 maquette porte l'intention, et il sera branche cote mobile. */
            }}
            className="mx-auto mt-2 block min-h-12 text-sm font-medium text-primaire"
          >
            Augmenter la luminosité
          </button>
        </div>
      ) : null}

      <section>
        <h2 className="text-lg font-semibold text-texte">Suivi</h2>
        <div className="mt-3">
          <FriseEtapes
            indiceEnCours={etapeAtteinte(statut)}
            etapes={[
              {
                libelle: "Paiement reçu",
                detail: `${formaterFrancs(total)} le ${formaterDateCourte(commande.passeeLe)}`,
              },
              {
                libelle: "Clôture du groupage",
                detail: formaterDateCourte(groupage.clotureLe),
              },
              {
                libelle: "Commande chez le fournisseur",
                detail: `par ${groupage.groupeur}`,
              },
              { libelle: "Livraison à domicile", detail: "sous 3 à 5 jours" },
            ]}
          />
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-texte">Récapitulatif</h2>
        <div className="mt-3 flex items-start gap-3">
          <Vignette photo={groupage.photo} alt={groupage.photoAlt} />
          <div className="min-w-0">
            <p className="font-medium text-texte">{groupage.produit}</p>
            <p className="text-sm text-texte-secondaire">
              {quantite} part{quantite > 1 ? "s" : ""}
              {commande.variante ? ` · ${commande.variante}` : ""}
            </p>
          </div>
        </div>

        <dl className="mt-3">
          <div className="flex justify-between gap-4 py-1.5">
            <dt className="text-texte-secondaire">
              {quantite} part{quantite > 1 ? "s" : ""}
            </dt>
            <dd className="text-texte">
              {formaterFrancs(commande.montantParts)}
            </dd>
          </div>
          {/* Masquee a zero — voir l'ecran de commande. */}
          {commande.fraisLivraison > 0 ? (
            <div className="flex justify-between gap-4 py-1.5">
              <dt className="text-texte-secondaire">
                Livraison à {LIBELLE_QUARTIER[position.quartier]}
              </dt>
              <dd className="text-texte">
                {formaterFrancs(commande.fraisLivraison)}
              </dd>
            </div>
          ) : null}
          <div className="mt-2 flex justify-between gap-4 border-t border-filet pt-3">
            <dt className="font-semibold text-texte">Total payé</dt>
            <dd className="text-prix font-bold text-texte">
              {formaterFrancs(total)}
            </dd>
          </div>
        </dl>
        <p className="mt-1 text-xs text-texte-secondaire">
          Payée le {formaterDateCourte(commande.passeeLe)}
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-texte">Livraison</h2>
        <p className="mt-2 text-texte">
          {LIBELLE_QUARTIER[position.quartier]} — {position.repere}
        </p>
        <p className="text-texte-secondaire">+228 {commande.telephone}</p>

        {/* Aucun contact du groupeur (§1.7). La question passe par le fil
            public, qui est le seul canal entre les deux. */}
        <div className="mt-4 max-w-sm">
          <Bouton style="secondaire" onClick={onQuestions}>
            <IconeQuestion taille={18} />
            Une question ?
          </Bouton>
        </div>
      </section>

      {statut !== "livree" &&
      statut !== "remboursee" &&
      statut !== "annulee" ? (
        <Encart
          variante="attention"
          titre="Vérifiez votre commande devant le livreur"
        >
          Vous pouvez refuser le colis s&apos;il ne correspond pas à votre
          commande.
        </Encart>
      ) : null}

      {/* Visible uniquement pendant la livraison.

          ⚠️ **Et refusable pendant la livraison seulement.** Avant, il n'y a
          rien a refuser : le colis n'est pas parti. Apres, le code a ete
          donne au livreur, donc contester n'est plus un refus de colis mais
          une reclamation apres reception — le serveur refuse les deux cas. */}
      {statut === "en-livraison" ? (
        <div className="max-w-sm">
          <Bouton style="danger-texte" onClick={() => setRefusOuvert(true)}>
            Refuser le colis
          </Bouton>
        </div>
      ) : null}

      {refusOuvert ? (
        <FeuilleRefusColis
          commande={commande.id}
          onFermer={() => setRefusOuvert(false)}
          onRefuse={onRefuse}
        />
      ) : null}
    </div>
  );

  if (estBureau) {
    return (
      <>
        <div className="mx-auto max-w-3xl px-4 py-6 lg:px-8">
          <nav aria-label="Fil d'Ariane" className="mb-5">
            <button
              type="button"
              onClick={onRetour}
              className="inline-flex min-h-12 items-center gap-1 text-sm font-medium text-texte-secondaire hover:text-primaire"
            >
              <IconeRetour taille={18} />
              Mes commandes
            </button>
          </nav>
          <h1 className="mb-6 text-2xl font-semibold text-texte lg:text-3xl">
            Ma commande
          </h1>
          {corps}
        </div>
        <PiedPage />
      </>
    );
  }

  return (
    <div className="pb-10">
      <EnTeteEcran titre="Ma commande" onRetour={onRetour} />
      <div className="px-4 pt-5">{corps}</div>
    </div>
  );
}

/** L'etape de la frise atteinte par ce statut. */
function etapeAtteinte(statut: StatutCommande): number {
  switch (statut) {
    case "payee":
      return 0;
    case "cloturee":
      return 1;
    case "chez-le-groupeur":
      return 2;
    case "en-livraison":
      return 3;
    case "livree":
      return 4;
    default:
      return 0;
  }
}

/**
 * Le message propre a chaque etat. C'est lui qui porte la promesse du moment,
 * et les formulations sont contraintes par le §1.7.
 */
function MessageDEtat({
  statut,
  commande,
}: {
  statut: StatutCommande;
  commande: Commande;
}) {
  const montant = formaterFrancs(commande.total);

  switch (statut) {
    case "payee":
      return (
        <Encart variante="info">
          Votre code apparaîtra ici quand la livraison sera lancée. Vos{" "}
          {montant} sont au portefeuille du groupeur, qui ne peut les retirer
          qu&apos;à la clôture du groupage.
        </Encart>
      );

    case "cloturee":
      /* Le groupeur a recu les fonds : ce n'est plus la detention qui
         rassure, c'est la garantie (§1.7). */
      return (
        <Encart variante="info">
          Le groupeur a reçu les fonds et prépare votre commande.{" "}
          <strong className="font-semibold">
            Group Achat garantit votre livraison.
          </strong>
        </Encart>
      );

    case "chez-le-groupeur":
      return (
        <Encart variante="info">
          Le groupeur a passé commande chez son fournisseur.
        </Encart>
      );

    case "livree":
      return (
        <Encart variante="succes">
          Livrée le {formaterDateCourte(commande.groupage.remiseLe)}.
        </Encart>
      );

    case "remboursee":
    case "annulee":
      return (
        <Encart variante="danger">
          Ce groupage n&apos;a pas abouti.{" "}
          <strong className="font-semibold">
            Vos {montant} vous ont été remboursés
          </strong>
          , livraison comprise.
        </Encart>
      );

    default:
      return null;
  }
}
