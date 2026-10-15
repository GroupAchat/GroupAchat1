import { useEffect, useMemo, useState } from "react";
import Vignette from "../../composants/Vignette";
import { type Commande, estEnCours } from "../../domaine/commande";
import { formaterFrancs } from "../../domaine/format";
import {
  adapterCommande,
  listerMesCommandes,
  lireUnGroupage,
} from "../../api/campagnes";
import type { Groupage } from "../../domaine/groupage";
import { useCatalogue } from "../../api/CatalogueContexte";
import { useRequete } from "../../api/useRequete";
import { ErreurReseau, ListeEnChargement } from "../../ui/EtatReseau";
import EnTeteEcran from "../mise-en-page/EnTeteEcran";
import PiedPage from "../mise-en-page/PiedPage";
import EtatVide from "../../ui/EtatVide";
import Statut from "../../ui/Statut";

/**
 * Ecran 8 — Mes commandes. SPEC_ECRANS_FIGMA.md, ecran 8.
 *
 * **Les montants sont des totaux payes, livraison comprise.** C'est ce que
 * l'acheteur a ete debite, donc c'est ce qu'il doit retrouver ici — pas le
 * prix de la part.
 *
 * **Le code de livraison est accessible sans ouvrir le detail** quand la
 * livraison est en cours. C'est le geste fait debout devant le livreur, un
 * telephone dans une main et un colis dans l'autre : lui demander une
 * navigation de plus serait une erreur.
 *
 * **Deux etats vides a distinguer** (§1.5) : non connecte → l'etat pedagogique
 * qui explique a quoi sert l'onglet, jamais un mur de connexion ; connecte
 * sans commande → « Vous n'avez pas encore commande ».
 */
type Onglet = "en-cours" | "terminees";

export default function MesCommandes({
  estBureau,
  connecte,
  telephone,
  onOuvrirCommande,
  onVoirGroupages,
  onSeConnecter,
}: {
  estBureau: boolean;
  connecte: boolean;
  /** Le numero du compte : c'est lui qui identifie l'acheteur (§1.5). */
  telephone?: string;
  onOuvrirCommande: (commande: Commande) => void;
  onVoirGroupages: () => void;
  onSeConnecter: () => void;
}) {
  const [onglet, setOnglet] = useState<Onglet>("en-cours");
  const { groupages } = useCatalogue();

  /* L'appel ne part **que si un numero est connu** : sans compte, l'ecran
     montre son etat vide et n'a rien a demander au serveur. */
  const requete = useRequete(
    (signal) => listerMesCommandes(signal),
    [telephone],
    connecte,
  );

  /**
   * Les groupages de ses commandes **qui ne sont plus au catalogue**.
   *
   * ⚠️ **Sans eux, une commande disparaissait de cet ecran des que son
   * groupage se cloturait** — et c'etait un vrai defaut, pas un detail
   * d'affichage. Le catalogue ne sert que de l'ouvert (regle produit), donc
   * `adapterCommande` ne trouvait plus le groupage et la ligne etait ecartee.
   * Elle disparaissait precisement au mauvais moment : apres la cloture
   * viennent la commande chez le groupeur, la livraison et le **code de
   * livraison**, c'est-a-dire tout ce pour quoi on ouvre cet ecran. On payait,
   * et sa commande s'evaporait.
   *
   * Le commentaire d'origine disait qu'elles reapparaitraient « quand l'API
   * saura servir les campagnes closes ». Elle le sait : `retrieve` repond sur
   * un groupage cloture, c'est `list` seul qui filtre. Il manquait l'appel.
   */
  const [complement, setComplement] = useState<readonly Groupage[]>([]);

  const manquants = useMemo(() => {
    const connus = new Set([
      ...groupages.map((groupage) => groupage.id),
      ...complement.map((groupage) => groupage.id),
    ]);
    return [
      ...new Set(
        (requete.donnees ?? [])
          .map((brute) => String(brute.campagne))
          .filter((identifiant) => !connus.has(identifiant)),
      ),
    ];
  }, [requete.donnees, groupages, complement]);

  useEffect(() => {
    if (manquants.length === 0) {
      return;
    }
    const abandon = new AbortController();
    /* `allSettled` : un groupage supprime ne doit pas faire disparaitre les
       autres commandes avec lui. */
    Promise.allSettled(
      manquants.map((identifiant) => lireUnGroupage(identifiant, abandon.signal)),
    ).then((resultats) => {
      const trouves = resultats
        .filter(
          (resultat): resultat is PromiseFulfilledResult<Groupage> =>
            resultat.status === "fulfilled",
        )
        .map((resultat) => resultat.value);
      if (trouves.length > 0) {
        setComplement((avant) => [...avant, ...trouves]);
      }
    });
    return () => abandon.abort();
  }, [manquants]);

  const commandes = useMemo(
    () =>
      (requete.donnees ?? [])
        .map((brute) => adapterCommande(brute, [...groupages, ...complement]))
        /* Reste le cas d'un groupage vraiment introuvable — supprime, ou dont
           la relecture n'est pas encore revenue. On l'ecarte plutot que de le
           dessiner a moitie, et il apparaitra au tour suivant. */
        .filter((commande): commande is Commande => commande !== undefined),
    [requete.donnees, groupages, complement],
  );

  const enCours = commandes.filter((c) => estEnCours(c.statut));
  const terminees = commandes.filter((c) => !estEnCours(c.statut));
  const listee = onglet === "en-cours" ? enCours : terminees;

  /* Non connecte : un onglet protege n'affiche pas un mur mais un etat vide
     qui explique a quoi il sert (§1.5). */
  const contenu = !connecte ? (
    <EtatVide
      titre="Vos commandes apparaîtront ici"
      explication="Commandez une part dans un groupage pour suivre votre livraison."
      actionLibelle="Voir les groupages"
      onAction={onVoirGroupages}
      lienSecondaire={{
        libelle: "J'ai déjà un compte — me connecter",
        onClick: onSeConnecter,
      }}
    />
  ) : requete.chargement ? (
    /* L'attente prend la forme des lignes a venir : rien ne saute quand les
       commandes arrivent. */
    <ListeEnChargement nombre={3} />
  ) : requete.erreur ? (
    /* ⚠️ Un echec reseau n'est **pas** un etat vide. Afficher « aucune
       commande » parce que la requete a echoue ferait croire a quelqu'un qui
       vient de payer que sa commande a disparu — c'est le pire message
       possible a cet endroit. */
    <ErreurReseau erreur={requete.erreur} onReessayer={requete.recharger} />
  ) : listee.length === 0 ? (
    <EtatVide
      titre={
        onglet === "en-cours"
          ? "Aucune commande en cours"
          : "Aucune commande terminée"
      }
      explication="Vous n'avez pas encore commandé de part dans un groupage."
      actionLibelle="Voir les groupages"
      onAction={onVoirGroupages}
    />
  ) : (
    <ul className={estBureau ? "grid grid-cols-1 gap-4 xl:grid-cols-2" : ""}>
      {listee.map((commande) => (
        <LigneCommande
          key={commande.id}
          commande={commande}
          encadree={estBureau}
          onOuvrir={() => onOuvrirCommande(commande)}
        />
      ))}
    </ul>
  );

  const onglets = (
    <div
      role="tablist"
      aria-label="Filtrer mes commandes"
      className="flex gap-1 border-b border-filet"
    >
      {(
        [
          ["en-cours", "En cours", enCours.length],
          ["terminees", "Terminées", terminees.length],
        ] as const
      ).map(([cle, libelle, compte]) => (
        <button
          key={cle}
          type="button"
          role="tab"
          aria-selected={onglet === cle}
          onClick={() => setOnglet(cle)}
          className={`-mb-px min-h-12 border-b-2 px-4 font-medium transition-colors ${
            onglet === cle
              ? "border-primaire text-primaire"
              : "border-transparent text-texte-secondaire"
          }`}
        >
          {libelle}
          {connecte ? ` (${compte})` : ""}
        </button>
      ))}
    </div>
  );

  if (estBureau) {
    return (
      <>
        <div className="largeur-page py-8">
          <h1 className="text-2xl font-semibold text-texte lg:text-3xl">
            Mes commandes
          </h1>
          <div className="mt-6 max-w-4xl">
            {onglets}
            <div className="mt-6">{contenu}</div>
          </div>
        </div>
        <PiedPage />
      </>
    );
  }

  return (
    <div className="pb-18">
      <EnTeteEcran titre="Mes commandes" />
      <div className="px-4 pt-2">{onglets}</div>
      <div className="px-4">{contenu}</div>
    </div>
  );
}

/** Une ligne de la liste. Encadree sur grand ecran, nue sur telephone (§2.3). */
function LigneCommande({
  commande,
  encadree,
  onOuvrir,
}: {
  commande: Commande;
  encadree: boolean;
  onOuvrir: () => void;
}) {
  const { groupage, total, statut, codeLivraison, quantite } = commande;

  return (
    <li
      className={
        encadree
          ? "rounded-xl border border-bordure"
          : "border-b border-filet last:border-b-0"
      }
    >
      <button
        type="button"
        onClick={onOuvrir}
        className={`flex w-full items-start gap-3 text-left active:bg-surface-douce ${
          encadree ? "p-4" : "py-4"
        }`}
      >
        <Vignette photo={groupage.photo} alt={groupage.photoAlt} />

        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-texte">{groupage.produit}</h3>
          <p className="text-sm text-texte-secondaire">
            {groupage.groupeur}
            <span aria-hidden="true"> · </span>
            {quantite} part{quantite > 1 ? "s" : ""}
          </p>

          {/* Le total paye, livraison comprise. */}
          <p className="mt-1 font-bold text-texte">{formaterFrancs(total)}</p>

          <div className="mt-2">
            <Statut statut={statut} />
          </div>

          {/* Le code, sans ouvrir le detail : c'est le geste fait debout
              devant le livreur. */}
          {statut === "en-livraison" ? (
            <p className="mt-2 text-sm text-texte-secondaire">
              Votre code :{" "}
              <strong className="font-bold tracking-wider text-texte">
                {codeLivraison}
              </strong>
            </p>
          ) : null}
        </div>
      </button>
    </li>
  );
}
