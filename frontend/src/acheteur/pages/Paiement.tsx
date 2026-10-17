import { useEffect, useState } from "react";
import Bouton, { BoutonAncre } from "../../ui/Bouton";
import Champ from "../../ui/Champ";
import Encart from "../../ui/Encart";
import EnTeteEcran from "../mise-en-page/EnTeteEcran";
import { IconeRetour } from "../../ui/Icones";
import { LIBELLE_QUARTIER } from "../../domaine/groupage";
import { formaterFrancs } from "../../domaine/format";
import type { BrouillonPaiement } from "./Commander";
import { MENTION_LIVRAISON } from "../../domaine/livraison";

/**
 * Ecran 6 — Paiement Mobile Money (simule). SPEC_ECRANS_FIGMA.md, ecran 6.
 *
 * **Objectif : reproduire un paiement Mobile Money avec assez de fidelite pour
 * qu'il soit credible, tout en disant honnetement qu'il est simule.**
 *
 * Le bandeau de demonstration est en haut, et il ne se cache pas. Notre
 * argument est la securite de l'argent : nous nous jugeons d'abord sur notre
 * franchise. Un jury qui decouvre seul que le paiement est faux le prend bien
 * plus mal que s'il l'a lu. Il disparaitra au branchement de l'agregateur
 * agree (§18.2 du cahier des charges).
 *
 * **L'etape « validez sur votre telephone » n'est pas une fiction destinee a
 * la demo** : c'est le deroulement reel d'un paiement Mobile Money. L'omettre
 * rendrait la maquette fausse et obligerait a redessiner le parcours le jour
 * du branchement. L'ecran est identique en paiement reel, au bandeau pres.
 *
 * La phrase « Aucun montant n'a ete debite » accompagne **tous** les echecs :
 * c'est elle qui evite la panique.
 */

type Operateur = "t-money" | "flooz";
type EtatPaiement = "saisie" | "attente" | "echec";

/** Duree de l'attente simulee, le temps de lire la superposition. */
const DUREE_ATTENTE_MS = 2600;

export default function Paiement({
  brouillon: commande,
  estBureau,
  telephoneCompte,
  onRetour,
  onPaye,
}: {
  brouillon: BrouillonPaiement;
  estBureau: boolean;
  /** Le numero du compte, connu des que la connexion a eu lieu. */
  telephoneCompte?: string;
  onRetour: () => void;
  /**
   * Encaisse, et rend un message d'erreur si ca n'a pas marche.
   *
   * ⚠️ **Elle est asynchrone, et c'est tout l'interet.** L'ecran reste sur
   * « validez sur votre telephone » pendant l'appel, puis n'avance que si le
   * serveur a confirme. Avant le branchement, il avancait apres un simple
   * minuteur : la confirmation etait une animation, et une commande refusee
   * — groupage cloture entre-temps, quartier non desservi — aurait quand meme
   * affiche « c'est paye ».
   */
  onPaye: () => Promise<string | undefined>;
}) {
  const [operateur, setOperateur] = useState<Operateur>("t-money");
  /**
   * §6 point 5 : le champ est **pre-rempli**, et modifiable.
   *
   * Deux sources, dans cet ordre : le numero de livraison saisi a l'ecran 5,
   * puis celui du compte. La seconde est indispensable — quand la connexion
   * est declenchee par « Payer », l'acheteur vient de donner son numero a la
   * feuille de l'ecran 4, et le lui redemander deux ecrans plus loin est le
   * genre de friction qui fait abandonner un paiement.
   *
   * Il reste modifiable : le numero Mobile Money peut differer de celui du
   * compte.
   */
  const [numero, setNumero] = useState(
    commande.telephone || telephoneCompte || "",
  );
  const [etat, setEtat] = useState<EtatPaiement>("saisie");
  const [detailDeplie, setDetailDeplie] = useState(false);
  const [echec, setEchec] = useState<string>();

  /**
   * L'attente couvre **l'appel reel**, pas un minuteur.
   *
   * Le delai minimum reste : sur une bonne connexion, l'API repond en 80 ms,
   * et passer de « validez sur votre telephone » a « c'est paye » en un
   * clignement donne l'impression que rien n'a ete demande au telephone. Le
   * `Promise.all` attend donc **le plus lent des deux** — l'appel ou le delai
   * — ce qui preserve l'explication sans jamais la raccourcir au detriment de
   * la verite.
   */
  useEffect(() => {
    if (etat !== "attente") {
      return;
    }
    let abandonne = false;

    const delai = new Promise((resoudre) =>
      window.setTimeout(resoudre, DUREE_ATTENTE_MS),
    );

    void Promise.all([onPaye(), delai]).then(([probleme]) => {
      if (abandonne) {
        return;
      }
      if (probleme) {
        /* On revient a la saisie : le numero Mobile Money, le quartier ou la
           quantite sont peut-etre a corriger, et rester bloque sur un ecran
           d'attente ne laisserait que le bouton « retour » du navigateur. */
        setEchec(probleme);
        setEtat("saisie");
      }
    });

    return () => {
      abandonne = true;
    };
  }, [etat, onPaye]);

  return (
    <div className="mx-auto max-w-2xl pb-28 lg:px-8 lg:pb-16">
      {estBureau ? (
        <nav aria-label="Fil d'Ariane" className="px-4 pt-6 lg:px-0">
          <button
            type="button"
            onClick={onRetour}
            className="inline-flex min-h-12 items-center gap-1 text-sm font-medium text-texte-secondaire hover:text-primaire"
          >
            <IconeRetour taille={18} />
            Retour
          </button>
          <h1 className="mt-1 text-2xl font-semibold text-texte">
            Paiement
          </h1>
        </nav>
      ) : (
        <EnTeteEcran titre="Paiement" onRetour={onRetour} />
      )}

      <div className="space-y-6 px-4 pt-5">
        {/* 2 — Le bandeau de demonstration, tout en haut, jamais cache. */}
        <Encart variante="info" titre="Démonstration">
          Aucun paiement réel n&apos;est effectué.
        </Encart>

        {/* 3 — Le montant au centre */}
        <div className="text-center">
          <p className="text-code leading-none font-bold text-texte">
            {formaterFrancs(commande.total)}
          </p>
          <p className="mt-2 text-texte-secondaire">
            {commande.groupage.produit} — {commande.quantite} part
            {commande.quantite > 1 ? "s" : ""} + livraison
          </p>
          <button
            type="button"
            onClick={() => setDetailDeplie(!detailDeplie)}
            className="mt-2 text-sm font-medium text-primaire"
          >
            {detailDeplie ? "Masquer le détail" : "Détail"}
          </button>
          {detailDeplie ? (
            <dl className="mx-auto mt-3 max-w-64 text-sm">
              <div className="flex justify-between py-1">
                <dt className="text-texte-secondaire">
                  {commande.quantite} part{commande.quantite > 1 ? "s" : ""}
                </dt>
                <dd className="text-texte">
                  {formaterFrancs(commande.montantParts)}
                </dd>
              </div>
              {/* Masquee a zero — voir l'ecran de commande. */}
              {commande.fraisLivraison > 0 ? (
                <div className="flex justify-between py-1">
                  <dt className="text-texte-secondaire">
                    Livraison à {LIBELLE_QUARTIER[commande.position.quartier]}
                  </dt>
                  <dd className="text-texte">
                    {formaterFrancs(commande.fraisLivraison)}
                  </dd>
                </div>
              ) : null}
            </dl>
          ) : null}
        </div>

        {/* 4 — Deux moyens de paiement */}
        <section>
          <h2 className="text-lg font-semibold text-texte">
            Choisissez votre opérateur
          </h2>
          <div className="mt-3 grid grid-cols-2 gap-3">
            {(
              [
                { cle: "t-money", nom: "T-Money" },
                { cle: "flooz", nom: "Flooz" },
              ] as const
            ).map(({ cle, nom }) => (
              <button
                key={cle}
                type="button"
                aria-pressed={operateur === cle}
                onClick={() => setOperateur(cle)}
                className={`flex h-20 items-center justify-center rounded-xl border font-semibold ${
                  operateur === cle
                    ? "border-2 border-primaire bg-primaire-fond text-primaire-texte-sur-fond"
                    : "border-bordure text-texte"
                }`}
              >
                {nom}
              </button>
            ))}
          </div>
        </section>

        {/* 5 — Le numero de paiement peut differer du numero du compte. */}
        <Champ
          libelle="Numéro Mobile Money"
          valeur={numero}
          onChanger={setNumero}
          type="tel"
          inputMode="tel"
          prefixe="+228"
          exemple="90 12 34 56"
          aide="Il peut être différent du numéro de votre compte."
        />

        {/* 6 — ⚠️ **Cette phrase disait : « Votre paiement est détenu par
            Group Achat jusqu'à la clôture du groupage. »** C'est faux : les
            fonds vont au **portefeuille du groupeur** dès le paiement (§9.1 du
            cahier des charges). Group Achat tient son compte, pas les fonds
            pour son propre compte.

            La contrainte du §1.7 tient toujours sur l'autre moitié : jamais
            « bloqué jusqu'à la livraison » — le groupeur est payé à la
            clôture, avant qu'on livre. */}
        <p className="text-sm text-texte-secondaire">
          Votre paiement va au portefeuille du groupeur, qui ne peut le retirer
          qu&apos;à la clôture du groupage.
        </p>

        <p className="mt-2 text-sm text-texte-secondaire">
          {MENTION_LIVRAISON}
        </p>

        {etat === "echec" ? (
          <div className="space-y-3">
            <Encart variante="danger">
              Le paiement n&apos;a pas abouti.{" "}
              <strong className="font-semibold">
                Aucun montant n&apos;a été débité.
              </strong>
            </Encart>
            <Bouton style="secondaire" onClick={() => setEtat("saisie")}>
              Changer de moyen de paiement
            </Bouton>
          </div>
        ) : null}
      </div>

      {/* 7 — Bouton ancre */}
      <BoutonAncre>
        {/* ⚠️ Le refus du serveur s'affiche **ici**, collé au bouton, et non
            en haut de l'ecran : sur un telephone, le haut de cet ecran est
            hors champ au moment ou l'on appuie, et un message qu'on ne voit
            pas est un message qui n'existe pas. */}
        {echec ? (
          <p role="alert" className="mb-2 text-sm font-medium text-danger">
            {echec}
          </p>
        ) : null}
        <Bouton
          desactive={numero.trim() === ""}
          onClick={() => {
            setEchec(undefined);
            setEtat("attente");
          }}
        >
          {etat === "echec" || echec
            ? "Réessayer"
            : "Confirmer le paiement"}
        </Bouton>
      </BoutonAncre>

      {/* L'etape reelle d'un paiement Mobile Money : l'application attend
          pendant que l'operateur demande son code a l'utilisateur. */}
      {etat === "attente" ? (
        <div
          role="status"
          aria-live="assertive"
          className="fixed inset-0 z-30 mx-auto flex max-w-[430px] flex-col items-center justify-center bg-black/70 px-8 text-center text-white"
        >
          <span
            aria-hidden="true"
            className="size-10 animate-spin rounded-full border-[3px] border-white/40 border-t-white"
          />
          <p className="mt-6 text-lg font-semibold">
            Validez le paiement sur votre téléphone
          </p>
          <p className="mt-2 text-sm text-white/90">
            Saisissez votre code {operateur === "t-money" ? "T-Money" : "Flooz"}{" "}
            quand il s&apos;affiche.
          </p>
          <p className="mt-4 text-sm font-medium">Ne fermez pas cette page.</p>
        </div>
      ) : null}
    </div>
  );
}
