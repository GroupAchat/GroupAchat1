import { LIBELLE_QUARTIER, type Quartier } from "./groupage";

/**
 * Frais de livraison — §11.1 du cahier des charges.
 *
 * **Le calcul reel n'existe pas encore : la fonction renvoie 1 000 F pour
 * toute position.** C'est volontaire et ecrit tel quel dans la spec. Ce qui
 * compte des aujourd'hui, c'est la forme du contrat :
 *
 * - les frais sont une **ligne distincte** du prix de la part, jamais fondus
 *   dedans — la part est la meme pour tous, les frais varient ;
 * - ils dependent de la **position**, qui est conservee sur la commande ;
 * - il n'y a que **deux reponses possibles** : un montant, ou « zone non
 *   desservie ». Pas de troisieme cas « tarif calcule plus tard » — on ne
 *   demande jamais a quelqu'un de payer un total qu'on completera apres
 *   (ecran 5, point 6).
 *
 * La position precise ne remonte **jamais** au groupeur (§1.7) : elle ne sort
 * qu'une fois, vers le livreur, le jour de la tournee (ecran 22).
 */

export interface Position {
  /** Comment la position a ete obtenue — les deux chemins sont normaux. */
  source: "gps" | "lieu";
  quartier: Quartier;
  /** Repere en texte libre. Obligatoire, meme avec le GPS. */
  repere: string;
}

export type ResultatFrais =
  | { desservi: true; montant: number; lieu: string }
  | { desservi: false; lieu: string };

/**
 * Les frais factures a l'acheteur. **Zero.**
 *
 * ⚠️ **Cette constante valait 1 000 F.** Le seul revenu de la plateforme est
 * desormais de **1 500 F preleves sur chaque groupage abouti**, a la charge du
 * groupeur et retenus au retrait : l'acheteur ne paie que sa part.
 *
 * Elle reste une constante plutot qu'un zero ecrit en dur partout, pour la
 * meme raison qu'avant : **c'est le seul endroit a changer** le jour d'un vrai
 * calcul par position. Les recapitulatifs masquent la ligne tant qu'elle vaut
 * zero, et la reaffichent d'eux-memes sinon.
 */
export const FRAIS_PROVISOIRES = 0;

/**
 * Ce qu'il faut dire a l'acheteur, et qui ne se devine pas du total.
 *
 * ⚠️ **Une seule phrase, a un seul endroit.** Elle apparait sur l'ecran de
 * commande, celui du paiement et la confirmation : trois formulations
 * differentes de la meme promesse n'en font plus une. La centraliser est la
 * seule facon de garantir qu'elles ne divergent pas au fil des retouches.
 *
 * ⚠️ **Aucun montant, et c'est voulu.** Le tarif de l'agence partenaire n'a
 * jamais ete negocie — `LIVRAISON.md`, le dossier qui devait le porter, a ete
 * supprime du depot. On ecrit qu'on ne le connait pas plutot que de
 * l'inventer. Le jour ou il existe, c'est ici qu'il s'ecrit, une fois.
 */
export const MENTION_LIVRAISON =
  "Les frais de livraison se règlent directement au livreur, au moment de la remise.";

export function calculerFraisLivraison(position: Position): ResultatFrais {
  const lieu = LIBELLE_QUARTIER[position.quartier];
  return { desservi: true, montant: FRAIS_PROVISOIRES, lieu };
}

/**
 * Code de livraison de la commande.
 *
 * C1 renvoie `K7M-4PQ`, le code du fil rouge de la demonstration (§3) : c'est
 * celui que le jury retrouve sur la confirmation, le suivi, l'ecran du
 * groupeur et la tournee du livreur. Les autres groupages recoivent un code de
 * la meme forme, tire au sort. Cote Django, ce sera un champ genere a la
 * creation de la commande.
 */
export function genererCodeLivraison(idGroupage: string): string {
  if (idGroupage === "C1") {
    return "K7M-4PQ";
  }
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const tirer = (longueur: number) =>
    Array.from(
      { length: longueur },
      () => alphabet[Math.floor(Math.random() * alphabet.length)],
    ).join("");
  return `${tirer(3)}-${tirer(3)}`;
}
