import Bouton from "../../ui/Bouton";
import CodeLivraison from "../composants/CodeLivraison";
import Encart from "../../ui/Encart";
import FriseEtapes from "../../ui/FriseEtapes";
import { IconeBouclier, IconeCoche, IconeFermer } from "../../ui/Icones";
import { LIBELLE_QUARTIER } from "../../domaine/groupage";
import { formaterDateCourte, formaterFrancs } from "../../domaine/format";
import type { Commande } from "../../domaine/commande";

/**
 * Ecran 7 — Confirmation de commande. SPEC_ECRANS_FIGMA.md, ecran 7.
 *
 * **L'ecran qui transforme un paiement en confiance.**
 *
 * Pas de fleche de retour : on ne revient pas sur un paiement (§1.0, « simple »
 * regle 6, et sa seule exception assumee). Une croix de fermeture, c'est tout.
 *
 * Le `BandeauConfiance` y est dans sa version la plus developpee, et sa
 * formulation est contrainte (§1.7) : « detenus par Group Achat », « verses au
 * groupeur a la cloture ». **Surtout pas « bloques jusqu'a la livraison »** —
 * le groupeur est paye a la cloture, et promettre l'inverse serait faux.
 */
export default function Confirmation({
  commande,
  estBureau,
  onSuivre,
  onFermer,
  onModifierAdresse,
}: {
  commande: Commande;
  estBureau: boolean;
  onSuivre: () => void;
  onFermer: () => void;
  /** Vers le suivi de la commande, ou l'adresse se corrige (ecran 9). */
  onModifierAdresse: () => void;
}) {
  const { groupage, quantite, total, position } = commande;

  return (
    <div className="mx-auto max-w-2xl pb-10 lg:px-8 lg:pb-16">
      {/* Pas de fleche de retour : on ne revient pas sur un paiement
          (§1.0, « simple » regle 6, et sa seule exception assumee). Une croix,
          c'est tout. Sur grand ecran elle est a la meme place. */}
      <header
        className={`flex h-14 items-center justify-end px-2 ${estBureau ? "lg:px-0" : ""}`}
      >
        <button
          type="button"
          onClick={onFermer}
          aria-label="Fermer"
          className="flex size-12 items-center justify-center text-texte-secondaire"
        >
          <IconeFermer />
        </button>
      </header>

      <div className="space-y-6 px-4">
        {/* 2, 3, 4 — Pastille de succes, titre, sous-titre */}
        <div className="text-center">
          <span className="mx-auto flex size-18 items-center justify-center rounded-full bg-succes-fond text-succes">
            <IconeCoche taille={40} />
          </span>
          <h1 className="mt-4 text-2xl font-semibold text-texte">
            Commande confirmée
          </h1>
          <p className="mt-1 text-texte-secondaire">
            Vous êtes la {groupage.acheteursConfirmes + 1}
            <sup>e</sup> personne à commander ce groupage.
          </p>
          <p className="mt-3 text-prix font-bold text-texte">
            {formaterFrancs(total)} payés
          </p>
          <p className="text-texte-secondaire">
            {groupage.produit} — {quantite} part{quantite > 1 ? "s" : ""}
            {commande.variante ? ` · ${commande.variante}` : ""}
          </p>
        </div>

        {/* 5 — Ce que devient l'argent, en texte simple.

            ⚠️ **C'etait un encart bleu, retire sur demande** — et son titre
            etait faux : *« Vos N F sont detenus par Group Achat »*. Ils ne le
            sont pas. Ils vont au **portefeuille du groupeur** des le paiement ;
            ce que la plateforme tient, c'est son compte, pas les fonds pour
            son propre compte. Voir le §9.1 du cahier des charges. */}
        <div className="flex items-start gap-2 rounded-xl border border-bordure px-3 py-3">
          <span className="mt-0.5 shrink-0 text-primaire">
            <IconeBouclier taille={20} />
          </span>
          <div className="text-sm text-texte-secondaire">
            <p className="font-semibold text-texte">
              Vos {formaterFrancs(total)} vont au portefeuille du groupeur
            </p>
            <p className="mt-1">
              Il ne peut les retirer qu&apos;à la clôture du groupage, pour
              commander chez le fournisseur. Si celui-ci n&apos;aboutit pas,
              vous êtes remboursé intégralement.
            </p>
          </div>
        </div>

        {/* Le code de livraison (§2.10). */}
        <CodeLivraison code={commande.codeLivraison} />

        {/* 6 — La frise, premiere etape active */}
        <section>
          <h2 className="text-lg font-semibold text-texte">
            Ce qui se passe maintenant
          </h2>
          <div className="mt-3">
            <FriseEtapes
              indiceEnCours={0}
              etapes={[
                {
                  libelle: "Paiement reçu",
                  detail: `${formaterFrancs(total)} au portefeuille du groupeur`,
                },
                {
                  libelle: "Clôture du groupage",
                  detail: formaterDateCourte(groupage.clotureLe),
                },
                {
                  libelle: "Commande chez le fournisseur",
                  detail: `par ${groupage.groupeur}`,
                },
                {
                  libelle: "Livraison à domicile",
                  detail: "sous 3 à 5 jours",
                },
              ]}
            />
          </div>
        </section>

        {/* 7 — L'encart a ne pas omettre : la fenetre de contestation se ferme
            a l'acceptation du colis, et ca doit etre annonce avant. */}
        <Encart variante="attention" titre="Vérifiez votre commande devant le livreur">
          Vous pourrez refuser le colis s&apos;il ne correspond pas, mais plus
          après l&apos;avoir accepté.
        </Encart>

        {/* 8 — Rappel de l'adresse, modifiable tant que le groupage n'est pas
            cloture. */}
        <section>
          <h2 className="text-lg font-semibold text-texte">Livraison</h2>
          <p className="mt-2 text-texte">
            {LIBELLE_QUARTIER[position.quartier]} — {position.repere}
          </p>
          <button
            type="button"
            onClick={onModifierAdresse}
            className="mt-1 text-sm font-medium text-primaire"
          >
            Modifier
          </button>
        </section>

        {/* 9 — Deux boutons */}
        <div className="space-y-3 pt-2">
          <Bouton onClick={onSuivre}>Suivre ma commande</Bouton>
          <Bouton style="secondaire" onClick={onFermer}>
            Voir d&apos;autres groupages
          </Bouton>
        </div>
      </div>
    </div>
  );
}
