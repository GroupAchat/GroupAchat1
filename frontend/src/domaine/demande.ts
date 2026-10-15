import type { Quartier } from "./groupage";

/**
 * Le modele d'une question publique et d'une demande de produit.
 *
 * **Il n'y a pas de messagerie privee dans ce produit** (§1.7). Une question
 * est publique, filtree avant publication, et son auteur n'apparait que par un
 * prenom et une initiale — « Akosua D. ». Le groupeur repond sous son
 * pseudonyme. Ni l'un ni l'autre ne peut joindre l'autre autrement.
 */

export type EtatQuestion =
  /** Publiee, visible de tous. */
  | "publiee"
  /** Visible de son seul auteur, en attente du classifieur (ecran 10, b). */
  | "en-verification";

export interface Question {
  id: string;
  /** Le groupage sur lequel elle porte. */
  groupageId: string;
  texte: string;
  /** Prenom et initiale, jamais un nom complet (§1.7). */
  auteur: string;
  poseeLe: string;
  etat: EtatQuestion;
  reponse?: {
    /** Le pseudonyme du groupeur. */
    auteur: string;
    texte: string;
    repondueLe: string;
  };
}

/**
 * Les questions courantes, proposees avant le champ libre.
 *
 * **C'est une mesure de securite autant qu'un confort** (§14.2) : la plupart
 * des questions legitimes n'ont alors aucun texte libre, et le texte libre
 * redevient l'exception plutot que la regle.
 */
export const QUESTIONS_COURANTES: readonly string[] = [
  "Quelle marque ?",
  "Quelle origine ?",
  "Quand la livraison ?",
  "Quelles variantes ?",
];

/* ── Les demandes de produit (ecrans 11 et 12) ───────────────────────────── */

/**
 * Les statuts d'une demande.
 *
 * `non-aboutie` doit exister et doit etre montre : une demande peut ne rien
 * donner, et l'acheteur doit l'apprendre plutot que de rester en attente
 * indefiniment (§8 du cahier des charges).
 */
export type StatutDemande =
  | "en-attente"
  | "prise-en-charge"
  | "campagne-lancee"
  | "non-aboutie";

export const LIBELLE_DEMANDE: Record<StatutDemande, string> = {
  "en-attente": "En attente",
  "prise-en-charge": "Prise en charge",
  "campagne-lancee": "Groupage lancé !",
  "non-aboutie": "Non aboutie",
};

export interface Demande {
  id: string;
  produit: string;
  /** Texte court et libre : « 20 litres », « 2 paires ». */
  quantite: string;
  quartier: Quartier;
  /** Facultatif, en francs CFA. */
  budgetMaximum?: number;
  precisions?: string;
  /**
   * L'adresse de la photo jointe, s'il y en a une.
   *
   * ⚠️ **Une adresse, jamais les octets.** Le serveur ne sert la photo que
   * sur demande, par une route authentifiee : c'est ce qui permet a l'ecran 12
   * de lister trente demandes sans telecharger trente images sur un forfait
   * limite (§18.1). L'image ne part que si le navigateur l'affiche.
   */
  photoUrl?: string;
  deposeeLe: string;
  statut: StatutDemande;
  /** Explication montree sous le statut, variable selon celui-ci. */
  detail: string;
  /** Renseigne quand un groupeur a lance le groupage : on peut commander. */
  groupageId?: string;
}
