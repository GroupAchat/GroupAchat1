/** Les formes que rend l'API, telles que l'interface les consomme. */

export type Role = "acheteur" | "groupeur" | "administrateur";

export type StatutCampagne =
  | "brouillon"
  | "en_cours"
  /** Délai passé sans le minimum : le groupeur doit dire s'il maintient. */
  | "minimum_non_atteint"
  | "financee"
  | "decaissee"
  | "approvisionnement"
  | "distribution"
  | "terminee"
  | "annulee";

export type StatutParticipation =
  | "en_attente_paiement"
  | "payee"
  | "prete"
  | "retiree"
  | "remboursee"
  | "annulee";

export type StatutKYC = "en_attente" | "valide" | "rejete";

export interface Utilisateur {
  id: number;
  telephone: string;
  nom: string;
  prenom: string;
  nom_complet: string;
  email: string;
  role: Role;
  telephone_verifie: boolean;
  est_groupeur_valide: boolean;
  statut_kyc: StatutKYC | null;
  est_equipe: boolean;
  date_inscription: string;
}

export interface Reputation {
  note: string;
  campagnes_terminees: number;
  campagnes_annulees: number;
  avis_recus: number;
  participants_servis: number;
}

export interface GroupeurPublic {
  id: number;
  nom_complet: string;
  badge_confiance: boolean;
  reputation: Reputation | null;
  nom_commerce: string;
  date_inscription: string;
}

export interface Categorie {
  id: number;
  nom: string;
  slug: string;
  description: string;
  icone: string;
  ordre: number;
  sous_categories: Categorie[];
  nombre_campagnes: number;
}

/** Une photo ou une vidéo de produit — jusqu'à 3 photos et 2 vidéos. */
export interface MediaProduit {
  id: number;
  genre: "image" | "video";
  /**
   * Où aller chercher le média lui-même. Des adresses, et non des chemins :
   * selon que le fichier est hébergé chez Cloudinary ou posé sur le disque
   * du serveur, ce n'est pas la même chose à construire — et l'interface
   * n'a pas à le savoir.
   */
  adresse: string | null;
  /** Ce qu'il faut afficher dans la bande de vignettes, genre compris. */
  vignette: string | null;
  legende: string;
  ordre: number;
}

/** Photo du lot réellement proposé par le groupeur, sur une campagne. */
/** Photo du lot réellement proposé par le groupeur, sur sa campagne. */
export interface MediaCampagne {
  id: number;
  adresse: string | null;
  vignette: string | null;
  legende: string;
  ordre: number;
}

export interface ProduitResume {
  id: number;
  nom: string;
  slug: string;
  marque: string;
  image: string | null;
  categorie: number;
  categorie_nom: string;
  categorie_slug: string;
}

export interface Produit extends Omit<ProduitResume, "image"> {
  description: string;
  caracteristiques: Record<string, string>;
  medias: MediaProduit[];
  campagnes_en_cours: number;
  cree_le: string;
}

export interface PalierPrix {
  id: number;
  quantite_min: number;
  prix_unitaire: number;
}

export interface CampagneResume {
  id: number;
  titre: string;
  produit: ProduitResume;
  groupeur: GroupeurPublic;
  prix_unitaire: number;
  prix_courant: number;
  quantite_minimale: number;
  quantite_reservee: number;
  nombre_participants: number;
  pourcentage: number;
  minimum_atteint: boolean;
  date_limite: string;
  jours_restants: number;
  point_remise: string;
  statut: StatutCampagne;
  publiee_le: string | null;
}

export interface Campagne extends Omit<CampagneResume, "produit"> {
  produit: Produit;
  description: string;
  caracteristiques_offre: Record<string, string>;
  quantite_maximale: number | null;
  objectif_participants: number | null;
  paliers: PalierPrix[];
  medias: MediaCampagne[];
  montant_collecte: number;
  collecte_ouverte: boolean;
  mise_a_disposition_le: string | null;
  motif_annulation: string;
  nombre_commentaires: number;
  cree_le: string;
}

export interface Participation {
  id: number;
  campagne: CampagneResume;
  quantite: number;
  prix_unitaire_applique: number;
  montant_total: number;
  statut: StatutParticipation;
  statut_libelle: string;
  code_retrait: string | null;
  charge_qr: string | null;
  cree_le: string;
  payee_le: string | null;
  retiree_le: string | null;
  peut_etre_notee: boolean;
  avis: Avis | null;
}

/**
 * La note qu'un acheteur laisse à son groupeur.
 *
 * Group Achat met en relation, elle n'arbitre pas : c'est cette note — et la
 * discussion publique sous la campagne — qui sanctionne un mauvais groupeur.
 */
export interface Avis {
  id: number;
  participation: number;
  campagne: number;
  campagne_titre: string;
  auteur: { nom_affiche: string };
  note: number;
  commentaire: string;
  reponse: string;
  repondu_le: string | null;
  cree_le: string;
  modifie_le: string | null;
}

export interface Participant {
  id: number;
  nom_complet: string;
  telephone: string;
  quantite: number;
  montant_total: number;
  statut: StatutParticipation;
  statut_libelle: string;
  payee_le: string | null;
  retiree_le: string | null;
}

export interface AuteurPublic {
  id: number;
  nom_affiche: string;
}

export interface Commentaire {
  id: number;
  campagne: number;
  auteur: AuteurPublic;
  texte: string;
  reponse_a: number | null;
  reponses: Commentaire[];
  nombre_jaime: number;
  jaime_par_moi: boolean;
  est_du_groupeur: boolean;
  cree_le: string;
}

export interface DemandeProduit {
  id: number;
  auteur: AuteurPublic;
  titre: string;
  description: string;
  categorie: number | null;
  categorie_nom: string | null;
  budget_indicatif: number | null;
  statut: "ouverte" | "prise_en_charge" | "satisfaite" | "fermee";
  nombre_interets: number;
  interesse: boolean;
  campagne_issue: number | null;
  cree_le: string;
}

export interface Notification {
  id: number;
  genre: string;
  genre_libelle: string;
  titre: string;
  message: string;
  lien: string;
  campagne: number | null;
  cree_le: string;
  lue_le: string | null;
}

export interface DossierKYC {
  id: number;
  utilisateur: Utilisateur;
  type_piece: "cni" | "passeport" | "carte_consulaire";
  numero_piece: string;
  /** Adresses protégées, servies par une vue qui vérifie qui demande.
   *  Les champs `piece_recto`/`piece_verso` sont en écriture seule côté API. */
  lien_recto: string | null;
  lien_verso: string | null;
  numero_mobile_money: string;
  nom_commerce: string;
  statut: StatutKYC;
  motif_rejet: string;
  depose_le: string;
  decide_le: string | null;
  decide_par: string | null;
}

export interface Decaissement {
  id: number;
  campagne: number;
  campagne_titre: string;
  groupeur: string;
  montant_brut: number;
  frais: number;
  montant_net: number;
  numero_mobile_money: string;
  operateur: string;
  statut: "demande" | "approuve" | "execute" | "refuse";
  demande_le: string;
  execute_le: string | null;
  reference: string;
  motif_refus: string;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TableauDeBordGroupeur {
  campagnes: { total: number; en_cours: number; a_distribuer: number; terminees: number };
  collecte: { montant_consigne: number; pieces: number; participants: number };
  decaissements: { montant_recu: number; frais_payes: number };
  reputation: { note: string; campagnes_terminees: number; participants_servis: number };
}

export interface TableauDeBordAdmin {
  comptes: { acheteurs: number; groupeurs: number; groupeurs_valides: number };
  a_traiter: { dossiers_kyc: number; decaissements: number };
  campagnes: { en_cours: number; financees: number; terminees: number; annulees: number };
  sequestre: {
    montant_detenu: number;
    total_consigne: number;
    total_libere: number;
    total_rembourse: number;
  };
  revenus: { frais_encaisses: number };
  transactions_simulees: number;
  participations: number;
}

export interface EtatGroupeur {
  acces: boolean;
  raison: "non_connecte" | "aucun_dossier" | StatutKYC;
  motif_rejet?: string;
  depose_le?: string;
  decide_le?: string | null;
}
