import type { Categorie, Quartier } from "./groupage";

/**
 * Le modele du cote groupeur — ecrans 13 a 21.
 *
 * **La regle d'anonymat tient ici aussi, et c'est elle qui protege le modele
 * economique** (§1.7). Le groupeur voit des **codes et des quartiers**, jamais
 * un nom, un numero ou une adresse. Un groupeur qui pourrait se constituer un
 * fichier de clients les servirait hors plateforme, au meme prix, et sans
 * nous. Aucun type de ce fichier ne porte donc d'identite d'acheteur — et ce
 * n'est pas un oubli a combler.
 *
 * Les identites ne sortent qu'une fois, vers le livreur, le jour de la tournee
 * (`domaine/livreur.ts`).
 */

/**
 * Les frais de la plateforme : **1 500 F par groupage abouti**.
 *
 * ⚠️ **Un montant fixe, pas un taux.** L'argent de l'acheteur est inscrit au
 * portefeuille du groupeur des son paiement ; la plateforme ne verse plus rien
 * et ne prend plus de pourcentage — elle retient 1 500 F sur chaque groupage
 * abouti, au moment du retrait. Voir §9.2 du cahier des charges.
 */
export const FRAIS_PLATEFORME = 1500;

/**
 * Ce que le groupeur retire sur un montant collecte.
 *
 * **Les frais ne portent jamais sur les frais de livraison** : ceux-ci sont
 * payes par l'acheteur et vont au transporteur. Les melanger ferait payer au
 * groupeur des frais sur de l'argent qui ne passe pas par lui.
 *
 * ⚠️ **Jamais de net negatif** : sur un groupage plus petit que les frais, les
 * frais sont ramenes a la collecte. Le serveur applique la meme regle, et
 * **c'est lui qui fait foi** — ce calcul-ci ne sert qu'a afficher.
 */
export function calculerRetrait(collecteSurLesParts: number): {
  collecte: number;
  frais: number;
  net: number;
} {
  const frais = Math.min(FRAIS_PLATEFORME, collecteSurLesParts);
  return {
    collecte: collecteSurLesParts,
    frais,
    net: collecteSurLesParts - frais,
  };
}

export type StatutCampagne =
  | "ouverte"
  | "a-decider"
  | "en-cours"
  | "livree"
  | "annulee";

export const LIBELLE_CAMPAGNE: Record<StatutCampagne, string> = {
  ouverte: "Ouverte",
  "a-decider": "À décider",
  "en-cours": "Commande en cours",
  livree: "Livrée",
  annulee: "Annulée",
};

/** Une campagne vue par son groupeur. */
export interface Campagne {
  id: string;
  produit: string;
  categorie: Categorie;
  prixPart: number;
  commandes: number;
  /** Collecte sur les parts, hors frais de livraison. */
  collecte: number;
  /**
   * Combien de personnes il voulait reunir — ce qu'il a declare a la creation.
   *
   * ⚠️ **Ni plafond ni minimum** : a la cloture il decide, objectif atteint
   * ou non (§7 du cahier des charges). Voir `JaugeParticipants`.
   */
  objectifParticipants: number;
  /** Le remplissage en pourcentage, **calcule par le serveur**, plafonne a 100. */
  progression: number;
  heuresRestantes: number;
  statut: StatutCampagne;
  /**
   * Quand le groupeur a annonce que le produit etait arrive, s'il l'a fait.
   *
   * ⚠️ **Ce n'est pas une date a afficher**, c'est ce qui eteint le bouton
   * d'annonce de l'ecran 15 : l'arrivee est un fait unique.
   */
  arriveeAnnonceeLe?: string;
  photo?: string;
}

/**
 * Une commande vue par le groupeur : **un code, pas une personne**.
 *
 * Il n'y a volontairement ni nom, ni telephone, ni adresse — seulement le
 * quartier, qui lui sert a organiser ses tournees et qui n'identifie personne.
 */
export interface CommandeGroupeur {
  codeLivraison: string;
  quantite: number;
  variante?: string;
  montant: number;
  quartier: Quartier;
}

/** Une entree de « A faire aujourd'hui » (ecran 13). */
export interface Tache {
  id: string;
  /** `urgent` passe la pastille en `danger`, les autres en `marque`. */
  urgence: "urgent" | "normal";
  libelle: string;
  /** Vers quel ecran la tache mene. */
  destination: "decision" | "justificatif" | "questions" | "demandes";
}

/** Une ligne du portefeuille (ecran 18). */
export interface MouvementPortefeuille {
  id: string;
  date: string;
  libelle: string;
  /** Positif pour une entree, negatif pour une retenue. */
  montant?: number;
  /** Remplace le montant quand la ligne n'en porte pas. */
  mention?: string;
}

/** Une demande agregee, cote groupeur (ecran 19). */
export interface DemandeAgregee {
  id: string;
  produit: string;
  personnes: number;
  quartier: Quartier;
  /** Depuis combien de jours la demande s'accumule. */
  joursEcoules: number;
  budgetMoyen: number;
  volumeEstime: string;
}

/** Une ligne de l'histogramme des revenus par campagne (ecran 21). */
export interface RevenuParCampagne {
  campagne: string;
  /** Absent quand la campagne a ete annulee : elle reste visible, sans barre. */
  verse?: number;
}

/** Les statistiques du groupeur (ecran 21). */
export interface Statistiques {
  /**
   * **Ce qu'il a touche, pas ce qu'il a encaisse.** Le collecte inclut
   * l'argent qui n'est pas encore a lui ; mettre en avant un chiffre plus
   * flatteur que la realite detruit la credibilite du tableau de bord au
   * premier versement.
   */
  verse: number;
  variationVerse: number;
  campagnesAbouties: { reussies: number; total: number };
  participants: number;
  variationParticipants: number;
  panierMoyen: number;
  variationPanier: number;
  /**
   * Campagnes allees jusqu'a la livraison sur campagnes lancees.
   *
   * **Le lui montrer est un acte de loyaute** : c'est le chiffre qui
   * conditionne ses plafonds d'exposition (§10.4 du cahier des charges), donc
   * il doit savoir sur quoi il est juge.
   */
  tauxReussite: number;
  revenusParCampagne: RevenuParCampagne[];
  parCategorie: { categorie: string; part: number }[];
  parQuartier: { quartier: Quartier; commandes: number; part: number }[];
  /**
   * Les constats de « Ce que ca vous dit ».
   *
   * **Un constat, jamais un conseil.** « Votre panier moyen baisse » est un
   * fait ; « augmentez vos prix » est un conseil commercial dont nous ne
   * sommes pas responsables, et qui nous rendrait comptables de ses pertes.
   */
  constats: { ton: "info" | "attention" | "succes"; texte: string }[];
}
