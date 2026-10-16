import { useState } from "react";
import Bouton, { BoutonAncre } from "../../ui/Bouton";
import Champ from "../../ui/Champ";
import Encart from "../../ui/Encart";
import EnTeteEcran from "../mise-en-page/EnTeteEcran";
import { IconeCoche, IconeLieu, IconeRetour } from "../../ui/Icones";
import Vignette from "../../composants/Vignette";
import { type Groupage, LIBELLE_QUARTIER, QUARTIERS, type Quartier } from "../../domaine/groupage";
import { formaterFrancs } from "../../domaine/format";
import type { BrouillonCommande } from "../../domaine/commande";
import { calculerFraisLivraison } from "../../domaine/livraison";

/**
 * Ecran 5 — Commander : quantite, position, recapitulatif.
 * SPEC_ECRANS_FIGMA.md, ecran 5.
 *
 * **Aucun compte n'est encore demande** (§1.5) : choisir une quantite et
 * saisir une adresse n'engage rien. C'est le bouton « Payer » qui declenche la
 * connexion (ecran 4), et seulement si l'utilisateur n'a pas de compte.
 *
 * Trois regles de la spec qui se perdent facilement :
 *
 * - **Pas de plafond de quantite.** Il n'y a ni places limitees ni minimum
 *   (§7 du cahier des charges), donc aucune mention « places disponibles ».
 * - **Le bloc « Ou livrer » vient AVANT le recapitulatif**, parce que c'est
 *   lui qui determine les frais.
 * - **Un total ne s'affiche jamais faux en attendant une saisie.** Tant que la
 *   position est inconnue, la ligne de livraison dit « selon votre position »,
 *   le total affiche « — » et le bouton reste desactive.
 *
 * Le refus du GPS n'est pas une erreur : `Encart` `info`, jamais `danger`.
 * Beaucoup de gens refusent la geolocalisation, et indiquer le nom du lieu
 * doit rester un chemin normal, pas un rattrapage honteux.
 */

/**
 * Ce que l'ecran 5 produit : une commande complete **sauf** ce que seul le
 * paiement peut fixer — son identifiant, son code de livraison, son statut et
 * sa date. Le type vit dans `domaine/commande.ts`, et le nom local dit a quel
 * moment du parcours on se trouve.
 */
export type BrouillonPaiement = BrouillonCommande;

/**
 * Le quartier que la demonstration associe a une position GPS.
 *
 * Il n'y a **pas de geocodage inverse** branche : aucune fonction ne sait
 * traduire des coordonnees en quartier de Lome. La demo renvoie donc Tokoin,
 * le quartier de l'acheteuse du fil rouge (§3), et l'acheteur peut corriger.
 * Mentir sur ce point se verrait au premier essai depuis un autre quartier.
 */
const QUARTIER_PAR_DEFAUT_GPS: Quartier = "Tokoin";

export default function Commander({
  groupage,
  telephoneConnu,
  adresseConnue,
  estBureau,
  onRetour,
  onPayer,
}: {
  groupage: Groupage;
  estBureau: boolean;
  /** Pre-rempli si l'utilisateur est deja connecte. */
  telephoneConnu?: string;
  /**
   * La derniere adresse de livraison du compte.
   *
   * ⚠️ **Pre-remplie, et modifiable.** On se fait livrer ailleurs un jour sur
   * dix — chez sa sœur, au bureau — et une adresse figee obligerait a la
   * reecrire en entier a chaque fois, ou pire, ferait livrer au mauvais
   * endroit celui qui ne l'a pas vue.
   *
   * La commande garde ensuite **sa propre copie** de la position (§6 du PRD) :
   * le livreur doit voir l'adresse qui valait au moment de la commande, pas
   * celle du compte si l'acheteur demenage entre-temps.
   */
  adresseConnue?: { quartier: string; repere: string };
  onRetour: () => void;
  onPayer: (brouillon: BrouillonPaiement) => void;
}) {
  const [quantite, setQuantite] = useState(1);
  const [variante, setVariante] = useState<string | undefined>();
  const [quartier, setQuartier] = useState<Quartier | undefined>(
    adresseConnue?.quartier as Quartier | undefined,
  );
  const [sourcePosition, setSourcePosition] = useState<"gps" | "lieu">("lieu");
  const [gpsRefuse, setGpsRefuse] = useState(false);
  const [gpsEnCours, setGpsEnCours] = useState(false);
  const [repere, setRepere] = useState(adresseConnue?.repere ?? "");
  const [telephone, setTelephone] = useState(telephoneConnu ?? "");
  const [conditionsAcceptees, setConditionsAcceptees] = useState(false);

  const montantParts = groupage.prixPart * quantite;
  const frais = quartier
    ? calculerFraisLivraison({ source: sourcePosition, quartier, repere })
    : undefined;
  const total =
    frais && frais.desservi ? montantParts + frais.montant : undefined;

  const varianteManquante = groupage.variante !== undefined && !variante;
  const peutPayer =
    total !== undefined &&
    !varianteManquante &&
    repere.trim() !== "" &&
    conditionsAcceptees;

  function partagerPosition() {
    setGpsEnCours(true);
    setGpsRefuse(false);

    if (!("geolocation" in navigator)) {
      setGpsEnCours(false);
      setGpsRefuse(true);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      () => {
        setGpsEnCours(false);
        setSourcePosition("gps");
        setQuartier(QUARTIER_PAR_DEFAUT_GPS);
      },
      () => {
        // Un refus de permission n'est pas une erreur : on bascule simplement
        // sur l'autre chemin, qui est tout aussi normal.
        setGpsEnCours(false);
        setGpsRefuse(true);
      },
      { timeout: 8000 },
    );
  }

  return (
    /* Sur grand ecran, le tunnel reste une colonne etroite et centree :
       un formulaire de paiement etale sur 1 280 px se lit mal, et toutes
       les boutiques le resserrent. */
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
            Commander
          </h1>
        </nav>
      ) : (
        <EnTeteEcran titre="Commander" onRetour={onRetour} />
      )}

      <div className="space-y-6 px-4 pt-5">
        {/* 2 — Rappel compact */}
        <div className="flex items-center gap-3">
          <Vignette photo={groupage.photo} alt={groupage.photoAlt} taille={64} />
          <div className="min-w-0">
            <p className="font-semibold text-texte">{groupage.produit}</p>
            <p className="text-texte-secondaire">
              {formaterFrancs(groupage.prixPart)} la part
            </p>
          </div>
        </div>

        {/* 3 — Quantite. Aucun plafond, aucune mention de places disponibles. */}
        <section>
          <h2 className="text-lg font-semibold text-texte">Quantité</h2>
          <div className="mt-3 flex items-center gap-4">
            <button
              type="button"
              aria-label="Retirer une part"
              disabled={quantite <= 1}
              onClick={() => setQuantite(Math.max(1, quantite - 1))}
              className="flex size-12 items-center justify-center rounded-[10px] border border-bordure text-2xl text-texte disabled:text-texte-secondaire"
            >
              −
            </button>
            <output className="min-w-10 text-center text-2xl font-semibold text-texte">
              {quantite}
            </output>
            <button
              type="button"
              aria-label="Ajouter une part"
              onClick={() => setQuantite(quantite + 1)}
              className="flex size-12 items-center justify-center rounded-[10px] border border-bordure text-2xl text-texte"
            >
              +
            </button>
          </div>
        </section>

        {/* 4 — Variante, obligatoire avant de continuer */}
        {groupage.variante ? (
          <section>
            <h2 className="text-lg font-semibold text-texte">
              {groupage.variante.libelle}
            </h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {groupage.variante.options.map((option) => (
                <button
                  key={option}
                  type="button"
                  aria-pressed={variante === option}
                  onClick={() => setVariante(option)}
                  className={`inline-flex min-h-12 min-w-14 items-center justify-center rounded-full px-4 font-medium ${
                    variante === option
                      ? "bg-primaire text-white"
                      : "bg-surface-douce text-texte"
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {/* 5 — Ou livrer. Deux chemins equivalents vers le meme resultat. */}
        <section>
          <h2 className="text-lg font-semibold text-texte">Où livrer</h2>

          {quartier ? (
            <div className="mt-3 flex items-start gap-2 rounded-xl bg-succes-fond px-3 py-2.5 text-sm text-succes">
              <IconeCoche taille={18} className="mt-0.5 shrink-0" />
              <div className="flex-1">
                <p className="font-semibold">Position enregistrée</p>
                <p className="mt-0.5">{LIBELLE_QUARTIER[quartier]}</p>
              </div>
              <button
                type="button"
                onClick={() => setQuartier(undefined)}
                className="shrink-0 font-medium underline"
              >
                Modifier
              </button>
            </div>
          ) : (
            <div className="mt-3 space-y-3">
              <Bouton
                style="secondaire"
                chargement={gpsEnCours}
                onClick={partagerPosition}
              >
                <IconeLieu taille={20} />
                Partager ma position
              </Bouton>

              {gpsRefuse ? (
                <Encart variante="info">
                  Pas de problème : indiquez le nom du lieu ci-dessous.
                </Encart>
              ) : null}

              <p className="text-center text-sm text-texte-secondaire">ou</p>

              <div>
                <p className="text-sm font-medium text-texte">
                  Indiquer le nom du lieu
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {QUARTIERS.map((unQuartier) => (
                    <button
                      key={unQuartier}
                      type="button"
                      onClick={() => {
                        setSourcePosition("lieu");
                        setQuartier(unQuartier);
                      }}
                      className="inline-flex min-h-12 items-center rounded-full bg-surface-douce px-4 text-sm font-medium text-texte"
                    >
                      {LIBELLE_QUARTIER[unQuartier]}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="mt-4 space-y-4">
            {/* Obligatoire meme avec le GPS : a Lome le repere vaut plus que
                la coordonnee, et un livreur avec un point sur une carte mais
                sans repere tourne quand meme. */}
            <Champ
              libelle="Repère"
              valeur={repere}
              onChanger={setRepere}
              exemple="rue des Cocotiers, près de la pharmacie Sodji"
              aide="Obligatoire, même si vous avez partagé votre position."
            />
            <Champ
              libelle="Numéro à joindre à la livraison"
              valeur={telephone}
              onChanger={setTelephone}
              type="tel"
              inputMode="tel"
              prefixe="+228"
              exemple="90 12 34 56"
            />
          </div>
        </section>

        {/* 6 — Recapitulatif. La ligne de livraison est distincte et visible,
            jamais fondue dans le prix de la part. */}
        <section>
          <h2 className="text-lg font-semibold text-texte">Récapitulatif</h2>
          <dl className="mt-3">
            <div className="flex justify-between gap-4 py-1.5">
              <dt className="text-texte">
                {quantite} part{quantite > 1 ? "s" : ""} ×{" "}
                {formaterFrancs(groupage.prixPart)}
              </dt>
              <dd className="font-medium text-texte">
                {formaterFrancs(montantParts)}
              </dd>
            </div>

            <div className="flex justify-between gap-4 py-1.5">
              <dt className="text-texte">
                {frais?.desservi ? `Livraison à ${frais.lieu}` : "Livraison"}
              </dt>
              <dd
                className={
                  frais?.desservi
                    ? "font-medium text-texte"
                    : "text-texte-secondaire italic"
                }
              >
                {frais?.desservi
                  ? formaterFrancs(frais.montant)
                  : "selon votre position"}
              </dd>
            </div>

            <div className="mt-2 flex justify-between gap-4 border-t border-filet pt-3">
              <dt className="font-semibold text-texte">Total à payer</dt>
              <dd className="text-prix font-bold text-texte">
                {total === undefined ? "—" : formaterFrancs(total)}
              </dd>
            </div>
          </dl>
        </section>

        {/* 8 — Conditions de vente, non cochees par defaut */}
        <label className="flex min-h-12 items-start gap-3 text-texte">
          <input
            type="checkbox"
            checked={conditionsAcceptees}
            onChange={(evenement) =>
              setConditionsAcceptees(evenement.target.checked)
            }
            className="mt-1 size-5 shrink-0 accent-[#CC4A00]"
          />
          <span>
            J&apos;accepte les{" "}
            <span className="font-medium text-primaire underline">
              conditions de vente
            </span>
          </span>
        </label>
      </div>

      {/* 9 — Bouton ancre. Son montant est le TOTAL, livraison comprise — pas
          le prix de la part. C'est l'erreur la plus facile a commettre. */}
      <BoutonAncre>
        <Bouton
          desactive={!peutPayer}
          onClick={() => {
            if (!peutPayer || total === undefined || !frais?.desservi) {
              return;
            }
            onPayer({
              groupage,
              quantite,
              variante,
              /* Generee ici, **avant** l'appel de paiement : c'est tout son
                 interet. Deux appuis sur « Confirmer » portent la meme cle, et
                 le serveur n'encaisse qu'une fois (§6 du PRD). */
              cleIdempotence: `idem-${groupage.id}-${Date.now()}`,
              position: {
                source: sourcePosition,
                quartier: quartier as Quartier,
                repere: repere.trim(),
              },
              telephone: telephone.trim(),
              montantParts,
              fraisLivraison: frais.montant,
              total,
            });
          }}
        >
          {total === undefined
            ? "Indiquez où livrer"
            : `Payer ${formaterFrancs(total)}`}
        </Bouton>
      </BoutonAncre>
    </div>
  );
}
