/**
 * Le modele d'un groupage — le vocabulaire commun a toute l'application.
 *
 * Ce fichier ne contient **que des types et des constantes de vocabulaire** :
 * aucune donnee, aucun composant, aucun appel reseau. C'est ce qui permet de
 * le lire en entier pour comprendre de quoi parle le produit, et de brancher
 * Django dessus sans rien toucher a l'interface.
 *
 * Les noms de champs suivent le §6 du PRD, pour que la bascule vers
 * `GET /api/campagnes/` soit un simple `fetch`.
 *
 * Trois champs a ne jamais perdre de vue, rappeles par le PRD :
 * les **frais de livraison separes de la part**, la **position conservee** sur
 * la commande, et la **cle d'idempotence** sur le paiement. Les deux derniers
 * vivent dans `commande.ts`.
 */

export type Categorie =
  | "alimentaire"
  | "vetements"
  | "chaussures"
  | "hygiene"
  | "maison"
  | "electronique";

export type Quartier =
  | "Agoe"
  | "Be"
  | "Tokoin"
  | "Adidogome"
  | "Nyekonakpoe"
  | "Hedzranawoe";

/** Une caracteristique du produit, telle que l'ecran 3 les presente en table. */
export interface Caracteristique {
  cle: string;
  valeur: string;
}

/** Variante obligatoire avant de commander — « Taille » pour C2 (ecran 5). */
export interface VarianteProduit {
  libelle: string;
  options: string[];
}

export interface Groupage {
  /** Identifiant interne, celui de la campagne cote Django. */
  id: string;
  /** Intitule visible. « un groupage », jamais « une campagne » (§3). */
  produit: string;
  /** Ce que contient une part — la premiere question de tout acheteur. */
  contenuPart: string;
  /** Description longue, repliee au-dela de 4 lignes sur l'ecran 3. */
  description: string;
  caracteristiques: Caracteristique[];
  /** Prix d'une part, en francs CFA. Les frais de livraison sont a part. */
  prixPart: number;
  /** Acheteurs ayant deja paye leur part. Pas de plafond, pas de minimum. */
  acheteursConfirmes: number;
  /**
   * Combien de personnes le groupeur veut reunir — le denominateur de la barre
   * de progression (§2.5).
   *
   * ⚠️ **Ni plafond ni minimum.** Depasser est permis, et un groupage
   * au-dessous de son objectif peut parfaitement aboutir : a la cloture, c'est
   * le groupeur qui decide (§7 du cahier des charges). Aucun ecran ne doit
   * s'en servir pour ecrire « places disponibles », « complet » ou « il manque
   * 6 personnes ».
   */
  objectifParticipants: number;
  /**
   * Le remplissage en pourcentage, **calcule par le serveur** et plafonne a
   * 100.
   *
   * Servi plutot que deduit des deux chiffres ci-dessus : le fil, la carte, la
   * ligne et le detail l'affichent tous, et quatre ecrans ne doivent pas
   * refaire le meme arrondi chacun a sa facon.
   */
  progression: number;
  /** Pseudonyme du groupeur (§1.7). */
  groupeur: string;
  categorie: Categorie;
  /**
   * Heures avant la cloture. Fixe plutot que calcule depuis l'horloge : la
   * demo doit afficher « Il reste 2 jours » sur C1 quel que soit le jour ou on la
   * montre.
   */
  heuresRestantes: number;
  /** Date de cloture affichee en toutes lettres sur l'ecran 3. */
  clotureLe: string;
  /** Nombre de questions publiques posees (ecran 10). */
  questions: number;
  /**
   * Les deux questions les plus recentes, affichees sur l'ecran 3.
   *
   * Elles sont **publiques** : il n'y a pas de messagerie privee dans cette
   * application, et toute question passe par un filtre avant publication.
   * L'auteur n'apparait que comme « Acheteur verifie » — jamais un nom (§1.7).
   */
  questionsRecentes?: { question: string; reponse: string }[];
  variante?: VarianteProduit;
  /** Quartier de remise. Un quartier n'identifie personne (§1.7). */
  quartier: Quartier;
  /** Repere public du point de remise. Jamais une adresse d'acheteur. */
  pointRemise: string;
  /** Date de remise prevue, au format ISO. */
  remiseLe: string;
  /**
   * Photo du produit.
   *
   * Ce sont des photos de banque d'images (Pexels), choisies faute de
   * `medias/` (§1.8) et **approchantes, pas exactes** : le bidon d'huile de
   * palme est une huile de cuisine, le carton de lait est un verre de lait.
   * Elles tiennent pour une demonstration, pas pour une mise en ligne — un
   * acheteur qui recoit autre chose que la photo a raison de se plaindre.
   * A remplacer par les photos reelles des groupeurs.
   */
  photo?: string;
  /** Texte alternatif : ce que la photo montre vraiment. */
  photoAlt?: string;
  /**
   * Tous les medias de la fiche, **dans l'ordre d'affichage** : jusqu'a
   * {@link MAX_IMAGES} images et {@link MAX_VIDEOS} videos.
   *
   * `photo` reste a cote et n'est pas une redite : c'est la **couverture**,
   * celle des cartes, des lignes de liste et du fil. Ces trois endroits n'ont
   * besoin que d'elle, et leur faire parcourir la liste pour retrouver la
   * premiere image reviendrait a repeter la meme regle dans cinq composants.
   */
  medias?: MediaProduit[];
}

/**
 * Un media de la fiche produit — une image, ou une video.
 *
 * ⚠️ **Une video porte toujours une affiche**, l'image qu'on voit avant de la
 * lancer. Sans elle, l'emplacement reste vide pendant le chargement, ce qui
 * est precisement ce que le §1.6 interdit : « une image d'abord, toujours ».
 */
export interface MediaProduit {
  type: "image" | "video";
  url: string;
  /** Ce que le media montre. Vide, l'interface retombe sur le nom du produit. */
  alt?: string;
  /** Video seulement : l'image montree avant la lecture. */
  affiche?: string;
}

/**
 * Combien de medias une fiche porte au plus.
 *
 * ⚠️ **Ces deux nombres sont aussi ecrits dans `catalogue/models.py`, et c'est
 * le serveur qui fait foi.** Ici, ils ne servent qu'a arreter le formulaire
 * avant l'aller-retour reseau — pas a garantir quoi que ce soit.
 *
 * Quatre images, parce qu'une seule photo ne vend pas. Deux videos, parce que
 * le public vise a un forfait de donnees limite (§18.1) et que c'est lui qui
 * paie le depassement.
 */
export const MAX_IMAGES = 4;
export const MAX_VIDEOS = 2;

/** Les six quartiers du jeu de demonstration (§3), dans l'ordre de la spec. */
export const QUARTIERS: readonly Quartier[] = [
  "Agoe",
  "Be",
  "Tokoin",
  "Adidogome",
  "Nyekonakpoe",
  "Hedzranawoe",
];

export const LIBELLE_QUARTIER: Record<Quartier, string> = {
  Agoe: "Agoè",
  Be: "Bè",
  Tokoin: "Tokoin",
  Adidogome: "Adidogomé",
  Nyekonakpoe: "Nyékonakpoè",
  Hedzranawoe: "Hédzranawoé",
};

/** Les six categories de l'ecran 2, point 2, dans l'ordre de la spec. */
export const CATEGORIES: readonly Categorie[] = [
  "alimentaire",
  "vetements",
  "chaussures",
  "hygiene",
  "maison",
  "electronique",
];

export const LIBELLE_CATEGORIE: Record<Categorie, string> = {
  alimentaire: "Alimentaire",
  vetements: "Vêtements",
  chaussures: "Chaussures",
  hygiene: "Hygiène",
  maison: "Maison",
  electronique: "Électronique",
};
