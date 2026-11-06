/** Les formes que rend l'API, telles que l'interface les consomme. */

/** `livreur` : le partenaire qui porte les colis et scanne les codes. */
export type Role = "acheteur" | "groupeur" | "livreur" | "administrateur";

export type Transporteur = "poste" | "gozem" | "autre";

export type StatutCampagne =
  | "brouillon"
  /** Mise en ligne demandée, relue avant la vitrine — selon le grade. */
  | "en_verification"
  | "en_cours"
  /** Délai passé sans le minimum : l'OAG doit dire s'il maintient. */
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

export type Grade = "nouveau" | "bronze" | "argent" | "or";

/**
 * Les deux compteurs de points, et ce qu'ils ouvrent.
 *
 * `cumules` ne descend jamais et décide du grade ; `solde` est la monnaie.
 * Les confondre à l'affichage induirait en erreur : « il vous reste 120
 * points » et « vous avez gagné 120 points » ne disent pas la même chose.
 */
export interface Points {
  cumules: number;
  solde: number;
  grade: Grade;
  /** En centièmes de pour-cent : 350 pour 3,5 %. */
  commission_centiemes: number;
  prochain_palier: { grade: Grade; points_restants: number } | null;
}

export type StatutKYC = "en_attente" | "valide" | "rejete";

export interface Utilisateur {
  id: number;
  telephone: string;
  nom: string;
  prenom: string;
  nom_complet: string;
  /** Choisi par l'utilisateur ; obligatoire pour un OAG. */
  nom_utilisateur: string | null;
  /** Ce sous quoi les autres le voient — repli sur « Prénom I. ». */
  nom_public: string;
  email: string;
  role: Role;
  /** Rempli pour les seuls livreurs : « La Poste », « Gozem ». */
  transporteur: Transporteur | "";
  telephone_verifie: boolean;
  est_groupeur_valide: boolean;
  statut_kyc: StatutKYC | null;
  points: Points;
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

/**
 * Tout ce qu'un acheteur sait de son vendeur.
 *
 * Ni nom civil, ni numéro, ni enseigne : l'acheteur et l'OAG ne se
 * connaissent pas, et seul l'abonnement Contact Privé ouvre le pont. Ce bloc
 * est donc *tout* ce dont l'acheteur dispose pour décider — raison pour
 * laquelle aucun de ses éléments ne s'achète.
 */
export interface GroupeurPublic {
  id: number;
  nom_utilisateur: string;
  badge_confiance: boolean;
  /** Visible : c'est un des rares repères dont dispose l'acheteur. */
  grade: Grade;
  reputation: Reputation | null;
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

/** Photo du lot réellement proposé par l'OAG, sur une campagne. */
/** Photo du lot réellement proposé par l'OAG, sur sa campagne. */
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
  video?: string | null;
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

/**
 * Une case du barème : une tranche, un seuil de participants, un prix.
 *
 * Deux axes à ne pas confondre. `quantite_min` est ce que prend **un seul**
 * acheteur — c'est lui qui décide de monter à douze pièces pour payer moins.
 * `participants_min` est la chute collective : passé ce nombre de
 * participants, le prix descend **pour tout le monde, y compris ceux qui ont
 * déjà payé**. C'est ce qui donne à chacun une raison de partager la
 * campagne.
 */
export interface PalierPrix {
  id: number;
  quantite_min: number;
  participants_min: number;
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
  cree_le: string;
}

/**
 * Un colis de la tournée, tel que le voit **celui qui le porte**.
 *
 * Il a l'adresse et le numéro — on ne livre pas un pseudonyme, il faut
 * sonner et appeler. Il n'a ni l'OAG ni les montants : porter un colis n'a
 * pas besoin de savoir qui l'a groupé, ni ce qu'il a coûté.
 */
export interface Colis {
  id: number;
  produit: string;
  groupage: string;
  quantite: number;
  destinataire: string;
  telephone: string;
  mode_retrait: ModeRetrait;
  mode_retrait_libelle: string;
  bureau_poste: string;
  adresse_livraison: string;
  destination: string;
}

/**
 * Le bilan du parrain : son code, ses filleuls, ses points.
 *
 * **Les filleuls ne sont pas nommés** — qui a accepté l'invitation ne
 * regarde que l'invité. Le parrain a droit au nombre, pas à la liste.
 */
export interface Parrainage {
  code: string;
  filleuls: number;
  filleuls_valides: number;
  en_attente: number;
  points_gagnes: number;
  points_par_filleul: number;
}

/**
 * Le droit de publier : abonnement au mois, ou packs de cinq.
 *
 * Les deux compteurs sont **indépendants** — un OAG dont l'abonnement expire
 * garde les publications de ses packs, qui n'expirent pas.
 */
export interface DroitDePublier {
  abonnement_actif: boolean;
  expire_le: string | null;
  publications_restantes: number;
  peut_publier: boolean;
  /** En francs entiers. */
  prix_abonnement: number;
  duree_jours: number;
  prix_pack: number;
  publications_par_pack: number;
}

/**
 * Comment l'acheteur récupère son colis. **C'est lui qui choisit**, part par
 * part : le bureau de poste le plus proche de chez lui, ou sa porte.
 *
 * Les frais de livraison ne passent pas par la plateforme — l'agence les fixe
 * et les encaisse à la remise.
 */
export type ModeRetrait = "poste" | "livraison";

export interface Participation {
  id: number;
  campagne: CampagneResume;
  quantite: number;
  prix_unitaire_applique: number;
  montant_total: number;
  statut: StatutParticipation;
  statut_libelle: string;
  code_retrait: string | null;
  code_otp_sms: string | null;
  charge_qr: string | null;
  /** Choisi par l'acheteur à la commande : bureau de poste ou livraison. */
  mode_retrait: ModeRetrait;
  mode_retrait_libelle: string;
  bureau_poste: string;
  adresse_livraison: string;
  /** La destination en une ligne, telle que le serveur la rédige. */
  destination: string;
  cree_le: string;
  payee_le: string | null;
  retiree_le: string | null;
  peut_etre_notee: boolean;
  avis: Avis | null;
}

/**
 * La note qu'un acheteur laisse à son OAG.
 *
 * Group Achat met en relation, elle n'arbitre pas : c'est cette note — et la
 * discussion publique sous la campagne — qui sanctionne un mauvais OAG.
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
  nom_utilisateur: string;
  nom_complet?: string;
  quantite: number;
  montant_total: number;
  statut: StatutParticipation;
  statut_libelle: string;
  mode_retrait: ModeRetrait;
  /** Sans l'adresse : l'OAG ne sait pas où dort son acheteur. */
  destination: string;
  /** Le transporteur qui a scanné le code, vide tant que rien n'est remis. */
  remis_par: string;
  payee_le: string | null;
  retiree_le: string | null;
}

export interface AuteurPublic {
  id: number;
  nom_affiche: string;
}

/**
 * Le Contact Privé : le seul pont entre un acheteur et un OAG.
 *
 * Il n'existe **aucune discussion publique**. Un fil ouvert sous une
 * campagne laissait convenir d'un arrangement direct à la vue de tous, et
 * hors de la plateforme ni le séquestre ni l'assurance ne jouent.
 */
export interface EtatContactPrive {
  actif: boolean;
  expire_le: string | null;
  /** En francs entiers. */
  prix: number;
  duree_jours: number;
  /** Ce que rapporte le mois payé : l'abonnement ne coûte aucun point. */
  points_par_mois: number;
}

export interface AbonnementContactPrive {
  id: number;
  montant: number;
  debute_le: string;
  expire_le: string;
  actif: boolean;
  reference_paiement: string;
}

export interface MessagePrive {
  id: number;
  auteur: number;
  auteur_nom: string;
  de_moi: boolean;
  texte: string;
  envoye_le: string;
  lu_le: string | null;
  signale_le: string | null;
}

/**
 * L'autre partie du fil.
 *
 * `nom_complet` et `telephone` ne sont remplis que pour un abonné en cours,
 * et seulement de l'OAG vers l'acheteur : c'est ce que l'abonnement achète,
 * et il ne l'achète que dans ce sens.
 */
export interface Interlocuteur {
  id: number;
  nom_utilisateur: string;
  nom_complet: string | null;
  telephone: string | null;
}

export interface Conversation {
  id: number;
  interlocuteur: Interlocuteur;
  campagne_initiale: number | null;
  dernier_message: MessagePrive | null;
  non_lus: number;
  /** Tranché par le serveur : l'OAG répond sans abonnement, l'acheteur non. */
  je_peux_ecrire: boolean;
  ouverte_le: string;
  dernier_message_le: string;
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
  a_traiter: {
    dossiers_kyc: number;
    decaissements: number;
    campagnes_a_verifier: number;
  };
  campagnes: { en_cours: number; financees: number; terminees: number; annulees: number };
  sequestre: {
    montant_detenu: number;
    total_consigne: number;
    total_libere: number;
    total_rembourse: number;
  };
  /** Deux sources : la commission sur les groupages, et le droit de publier. */
  revenus: {
    frais_encaisses: number;
    publications: number;
    total: number;
  };
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

export type MotifReclamation =
  | "non_livraison"
  | "retard"
  | "non_conforme"
  | "incomplete"
  | "minimum_non_atteint"
  | "paiement_conteste"
  | "fraude";

export type EtapeReclamation =
  | "ouverture"
  | "accuse_reception"
  | "contradictoire"
  | "analyse"
  | "decision"
  | "clos";

export interface Reclamation {
  id: number;
  numero_dossier: string;
  participation: number;
  campagne_titre: string;
  auteur: number;
  auteur_nom: string;
  motif: MotifReclamation;
  motif_libelle: string;
  description: string;
  piece_jointe: string | null;
  etape: EtapeReclamation;
  etape_libelle: string;
  reponse_oag: string;
  decision: string;
  remboursement_accorde: number;
  cree_le: string;
  mis_a_jour_le: string;
}

export interface HistoriqueBancaireOag {
  oag: {
    nom_complet: string;
    nom_commerce: string;
    telephone: string;
    date_inscription: string;
    statut_kyc: string;
    cadre_juridique: string;
    loi_donnees: string;
  };
  synthese: {
    offres_lancees: number;
    offres_terminees: number;
    taux_reussite_pourcent: number;
    montant_total_collecte_fcfa: number;
    montant_total_decaisse_fcfa: number;
    clients_servis: number;
    note_satisfaction: string;
    taux_livraison_a_temps: string;
    taux_reclamations: string;
  };
  lignes_historique: {
    id: number;
    titre: string;
    date_creation: string;
    statut: string;
    montant_collecte: number;
    participants: number;
    assurance: string;
  }[];
  reference_attestation: string;
  emise_le: string;
}
