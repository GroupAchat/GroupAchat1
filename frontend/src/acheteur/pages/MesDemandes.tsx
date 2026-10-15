import {
  type Demande,
  LIBELLE_DEMANDE,
  type StatutDemande,
} from "../../domaine/demande";
import { formaterDateCourte, formaterFrancs } from "../../domaine/format";
import { type Groupage, LIBELLE_QUARTIER } from "../../domaine/groupage";
import { listerMesDemandes } from "../../api/campagnes";
import { useRequete } from "../../api/useRequete";
import { ErreurReseau, ListeEnChargement } from "../../ui/EtatReseau";
import { useCatalogue } from "../../api/CatalogueContexte";
import EnTeteEcran from "../mise-en-page/EnTeteEcran";
import PiedPage from "../mise-en-page/PiedPage";
import Bouton from "../../ui/Bouton";
import EtatVide from "../../ui/EtatVide";

/**
 * Ecran 12 — Mes demandes. SPEC_ECRANS_FIGMA.md, ecran 12.
 *
 * **La premiere ligne ferme la boucle du produit** : une demande devient un
 * groupage qu'on peut commander, avec le bouton pour le faire. C'est la ligne
 * a montrer au jury, parce que c'est elle qui demontre le modele — la demande
 * cree l'offre.
 *
 * **La derniere est honnete et doit exister.** Une demande peut ne rien
 * donner, et l'acheteur doit l'apprendre plutot que d'attendre indefiniment
 * (§8 du cahier des charges). Une liste ou tout aboutit serait une maquette,
 * pas un produit.
 *
 * **Deux etats vides** (§1.5) : non connecte → l'etat pedagogique, jamais un
 * mur ; connecte sans demande → une invitation a en deposer une.
 */

/** Les couleurs des statuts de demande, sur le meme principe que le §2.8. */
const STYLES: Record<StatutDemande, string> = {
  /* Vert : quelque chose a abouti. */
  "campagne-lancee": "bg-succes-fond text-succes",
  /* Orange : ca avance. */
  "prise-en-charge": "bg-primaire-fond text-primaire-texte-sur-fond",
  /* Bleu : information neutre, rien ne presse. */
  "en-attente": "bg-confiance-fond text-confiance",
  /* Gris : clos sans suite. Pas rouge — ce n'est l'echec de personne. */
  "non-aboutie": "bg-surface-douce text-texte-secondaire",
};

export default function MesDemandes({
  estBureau,
  connecte,
  telephone,
  onDemanderProduit,
  onOuvrirGroupage,
  onSeConnecter,
}: {
  estBureau: boolean;
  connecte: boolean;
  /** Le numero du compte : c'est lui qui identifie l'acheteur (§1.5). */
  telephone?: string;
  onDemanderProduit: () => void;
  onOuvrirGroupage: (groupageId: string) => void;
  onSeConnecter: () => void;
}) {
  const { groupages } = useCatalogue();

  const requete = useRequete(
    (signal) => listerMesDemandes(signal),
    [telephone],
    connecte,
  );
  const demandes = requete.donnees ?? [];

  const contenu = !connecte ? (
    <EtatVide
      titre="Vos demandes apparaîtront ici"
      explication="Dites-nous ce que vous cherchez : nos groupeurs le verront et pourront lancer un groupage."
      actionLibelle="Demander un produit"
      registre="attente"
      onAction={onDemanderProduit}
      lienSecondaire={{
        libelle: "J'ai déjà un compte — me connecter",
        onClick: onSeConnecter,
      }}
    />
  ) : requete.chargement ? (
    <ListeEnChargement nombre={3} />
  ) : requete.erreur ? (
    /* Un echec reseau n'est pas un etat vide : afficher « aucune demande »
       parce que la requete a echoue ferait croire qu'elles ont ete perdues. */
    <ErreurReseau erreur={requete.erreur} onReessayer={requete.recharger} />
  ) : demandes.length === 0 ? (
    <EtatVide
      titre="Aucune demande pour l'instant"
      explication="Un produit que vous ne trouvez pas ? Demandez-le, un groupeur peut le lancer."
      actionLibelle="Demander un produit"
      registre="attente"
      onAction={onDemanderProduit}
    />
  ) : (
    <ul className={estBureau ? "grid grid-cols-1 gap-4 xl:grid-cols-2" : ""}>
      {demandes.map((demande) => (
        <LigneDemande
          key={demande.id}
          demande={demande}
          encadree={estBureau}
          groupages={groupages}
          onCommander={onOuvrirGroupage}
        />
      ))}
    </ul>
  );

  if (estBureau) {
    return (
      <>
        <div className="largeur-page py-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h1 className="text-2xl font-semibold text-texte lg:text-3xl">
              Mes demandes
            </h1>
            <div className="w-full max-w-xs">
              <Bouton onClick={onDemanderProduit}>Demander un produit</Bouton>
            </div>
          </div>
          <div className="mt-6 max-w-4xl">{contenu}</div>
        </div>
        <PiedPage />
      </>
    );
  }

  return (
    <div className="pb-18">
      <EnTeteEcran titre="Mes demandes" />
      <div className="px-4">{contenu}</div>
      {connecte && demandes.length > 0 ? (
        <div className="px-4 pb-6">
          <Bouton style="secondaire" onClick={onDemanderProduit}>
            Demander un produit
          </Bouton>
        </div>
      ) : null}
    </div>
  );
}

function LigneDemande({
  demande,
  encadree,
  groupages,
  onCommander,
}: {
  demande: Demande;
  encadree: boolean;
  /* Passe en parametre plutot que lu par `useCatalogue` ici : ce composant
     est appele en boucle, et un abonnement au contexte par ligne n'apporte
     rien de plus qu'une lecture dans le parent. */
  groupages: readonly Groupage[];
  onCommander: (groupageId: string) => void;
}) {
  const groupage = demande.groupageId
    ? groupages.find((g) => g.id === demande.groupageId)
    : undefined;

  return (
    <li
      className={
        encadree
          ? "rounded-xl border border-bordure p-4"
          : "border-b border-filet py-4 last:border-b-0"
      }
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex min-w-0 gap-3">
          {/* ⚠️ `loading="lazy"` : une liste de trente demandes ne doit pas
              televerser trente images avant d'etre lisible. Le serveur ne
              sert les octets que si le navigateur les demande, et il ne les
              demande que pour ce qui approche du cadre (§18.1). */}
          {demande.photoUrl ? (
            <img
              src={demande.photoUrl}
              alt={`Photo du produit demandé : ${demande.produit}`}
              loading="lazy"
              className="size-14 shrink-0 rounded-[10px] border border-bordure object-cover"
            />
          ) : null}
          <div className="min-w-0">
            <h3 className="font-semibold text-texte">
              {demande.produit}, {demande.quantite}
            </h3>
            <p className="text-sm text-texte-secondaire">
              {LIBELLE_QUARTIER[demande.quartier]}
              <span aria-hidden="true"> · </span>
              demandé le {formaterDateCourte(demande.deposeeLe)}
              {demande.budgetMaximum
                ? ` · jusqu'à ${formaterFrancs(demande.budgetMaximum)}`
                : ""}
            </p>
          </div>
        </div>

        <span
          className={`inline-flex h-6 shrink-0 items-center rounded-full px-2.5 text-xs font-medium whitespace-nowrap ${STYLES[demande.statut]}`}
        >
          {LIBELLE_DEMANDE[demande.statut]}
        </span>
      </div>

      <p className="mt-2 text-sm text-texte-secondaire">{demande.detail}</p>

      {/* La boucle se ferme : la demande est devenue un groupage. */}
      {groupage ? (
        <div className="mt-3 max-w-xs">
          <Bouton onClick={() => onCommander(groupage.id)}>
            Voir le groupage
          </Bouton>
        </div>
      ) : null}
    </li>
  );
}
