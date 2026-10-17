import type { Commande } from "../domaine/commande";
import type { Demande, Question } from "../domaine/demande";
import type {
  Categorie,
  Groupage,
  MediaProduit,
  Quartier,
} from "../domaine/groupage";
import { appeler, type Page } from "./client";

/**
 * Le catalogue : ce que l'API renvoie, et comment les ecrans le lisent.
 *
 * ## L'adaptateur, et pourquoi il existe
 *
 * L'API parle en `snake_case` et en vocabulaire **interne** — « campagne »,
 * `date_fin`, `media`. Les ecrans parlent en `camelCase` et en vocabulaire
 * **utilisateur** — « groupage », `clotureLe`, `photo` (§3 : le mot visible
 * est « groupage », jamais « campagne »).
 *
 * `adapterGroupage` fait la traduction, **en un seul endroit**. Les vingt
 * ecrans acheteur continuent de lire le type `Groupage` qu'ils connaissent
 * depuis le debut : brancher l'API n'a donc demande de toucher ni a leur mise
 * en page, ni a leurs calculs.
 *
 * ⚠️ **C'est ici que se verra une divergence de forme avec le serveur.** Si un
 * serialiseur change un nom de champ, c'est cette fonction qui cassera — pas
 * vingt ecrans. Le prix a payer est qu'elle casse **silencieusement** :
 * TypeScript ne verifie rien a l'execution, et un champ renomme cote serveur
 * produira `undefined` ici. Les garde-fous sont les tests backend, qui
 * verifient champ par champ ce qui sort.
 */

/** Une campagne telle que `GET /api/campagnes/` la renvoie. */
export interface CampagneApi {
  id: number;
  titre: string;
  description: string;
  contenu_part: string;
  categorie: Categorie;
  /** DRF serialise les decimaux en **chaine**, pour ne pas perdre de precision. */
  prix_part: string;
  paliers: { quantite_min: number; prix_part: string }[];
  participants_recents: {
    quartier: string;
    quantite: number;
    heures: number;
  }[];
  /** Tous les medias, dans l'ordre. */
  medias: MediaProduit[];
  /** La couverture, **deduite de la liste par le serveur**. */
  media: string;
  media_alt: string;
  date_fin: string;
  statut: string;
  /** Le **pseudonyme** du groupeur. Jamais son nom (§1.7). */
  groupeur: string;
  acheteurs_confirmes: number;
  objectif_participants: number;
  progression: number;
  heures_restantes: number;
  frais_livraison_a_partir_de: string;
  caracteristiques: { cle: string; valeur: string }[];
  variante: { libelle: string; options: string[] } | null;
  quartier_remise: string;
  point_remise: string;
  remise_le: string | null;
  nombre_de_questions: number;
  questions_recentes: { question: string; reponse: string }[];
}

/**
 * Traduit une campagne de l'API en groupage d'interface.
 *
 * ⚠️ **`id` devient une chaine.** Le type `Groupage` l'attend ainsi depuis le
 * debut — il valait « C1 », « C2 » — et tout le code acheteur compare des
 * chaines. Convertir ici plutot que de changer le type evite de relire vingt
 * fichiers pour une egalite qui marcherait encore par coincidence.
 */
export function adapterGroupage(campagne: CampagneApi): Groupage {
  return {
    id: String(campagne.id),
    produit: campagne.titre,
    contenuPart: campagne.contenu_part,
    description: campagne.description,
    caracteristiques: campagne.caracteristiques ?? [],
    /* `Number` et non `parseInt` : une chaine mal formee doit donner `NaN`,
       visible tout de suite, plutot qu'un nombre tronque qui passerait pour
       un prix. */
    prixPart: Number(campagne.prix_part),
    /* `?? []` : un serveur plus ancien que ce client ne sert pas le champ, et
       une grille absente doit se lire comme « pas de palier », pas planter la
       fiche produit. */
    paliers: (campagne.paliers ?? []).map((palier) => ({
      quantiteMin: palier.quantite_min,
      prixPart: Number(palier.prix_part),
    })),
    /* `?? []` pour la meme raison que les paliers : un serveur plus ancien ne
       sert pas ce champ, et la fiche doit s'afficher sans. */
    participantsRecents: campagne.participants_recents ?? [],
    acheteursConfirmes: campagne.acheteurs_confirmes,
    objectifParticipants: campagne.objectif_participants,
    progression: campagne.progression,
    groupeur: campagne.groupeur,
    categorie: campagne.categorie,
    heuresRestantes: campagne.heures_restantes,
    clotureLe: campagne.date_fin.slice(0, 10),
    questions: campagne.nombre_de_questions,
    questionsRecentes: campagne.questions_recentes ?? [],
    variante: campagne.variante ?? undefined,
    quartier: campagne.quartier_remise as Quartier,
    pointRemise: campagne.point_remise,
    remiseLe: campagne.remise_le ?? "",
    photo: campagne.media,
    photoAlt: campagne.media_alt,
    medias: campagne.medias ?? [],
  };
}

/**
 * Le catalogue ouvert.
 *
 * ⚠️ **La recherche et le filtrage par categorie restent faits dans le
 * navigateur** (`domaine/filtres.ts`), bien que l'API sache les faire. Ce
 * n'est pas un oubli :
 *
 * - le catalogue tient en **une page de quelques dizaines de produits**, et le
 *   filtrer en memoire est instantane — alors qu'un aller-retour reseau par
 *   frappe coute du temps et des donnees sur le forfait limite du §5 ;
 * - les filtres de l'ecran 2 se combinent (categorie, prix, temps restant) et
 *   affichent un **compteur de resultats avant application**, ce qu'un
 *   filtrage serveur obligerait a precharger de toute facon.
 *
 * Le jour ou le catalogue depasse ce que l'on peut raisonnablement envoyer en
 * une fois, c'est `CampagneViewSet.get_queryset` qui reprend la main — il sait
 * deja filtrer sur `categorie`, `statut` et `q`.
 */
export async function listerLesGroupages(
  signal?: AbortSignal,
): Promise<Groupage[]> {
  const page = await appeler<Page<CampagneApi>>("/campagnes/", {
    parametres: { statut: "ouverte" },
    signal,
  });
  return page.results.map(adapterGroupage);
}

/**
 * Un seul groupage, par son identifiant.
 *
 * ⚠️ **Elle existe pour les groupages que la liste ne contient pas.** Le
 * catalogue ne sert que de l'ouvert — `get_queryset` filtre sur `list`
 * seulement — alors que `retrieve` repond encore sur un groupage cloture.
 * C'est exactement ce que demande le `CLAUDE.md` : « sa fiche reste
 * atteignable par son lien ». Chercher la fiche dans le catalogue deja charge
 * aurait donc marche pour les groupages ouverts et echoue, en silence, pour
 * les seuls cas ou ce lien sert vraiment — celui qu'on a recu hier et qu'on
 * ouvre aujourd'hui.
 */
export async function lireUnGroupage(
  identifiant: string,
  signal?: AbortSignal,
): Promise<Groupage> {
  const campagne = await appeler<CampagneApi>(`/campagnes/${identifiant}/`, {
    signal,
  });
  return adapterGroupage(campagne);
}

// ── Questions publiques ────────────────────────────────────────────────────

export interface QuestionApi {
  id: number;
  campagne: number;
  /** « Akosua D. » — prenom et initiale, jamais un nom complet (§1.7). */
  auteur: string;
  texte: string;
  reponse: string;
  etat: string;
  posee_le: string;
  repondue_le: string | null;
}

/**
 * Traduit une question de l'API vers le type de l'interface.
 *
 * ⚠️ **Le pseudonyme du groupeur n'est pas dans la reponse de l'API** : le
 * serialiseur ne renvoie que l'auteur de la question. L'appelant le fournit
 * donc depuis le groupage qu'il affiche deja — plutot que de l'ajouter au
 * serialiseur, ce qui ferait voyager la meme chaine deux fois par question.
 */
export function adapterQuestion(
  question: QuestionApi,
  pseudonymeGroupeur: string,
): Question {
  return {
    id: String(question.id),
    groupageId: String(question.campagne),
    texte: question.texte,
    auteur: question.auteur,
    poseeLe: question.posee_le.slice(0, 10),
    etat: question.etat as Question["etat"],
    reponse: question.reponse
      ? {
          auteur: pseudonymeGroupeur,
          texte: question.reponse,
          repondueLe: (question.repondue_le ?? question.posee_le).slice(0, 10),
        }
      : undefined,
  };
}

export function listerLesQuestions(
  campagne: string,
  signal?: AbortSignal,
): Promise<Page<QuestionApi>> {
  return appeler("/questions/", { parametres: { campagne }, signal });
}

/**
 * Pose une question publique.
 *
 * ⚠️ Elle passe par **le filtre de moderation du serveur** avant publication
 * (§15) : un numero de telephone ou une invitation a se contacter hors
 * plateforme revient en 400, avec le passage en cause. Le front applique le
 * meme filtre a la saisie pour prevenir avant l'envoi, mais **c'est le serveur
 * qui decide** — un filtre d'interface se contourne.
 */
export function poserUneQuestion(
  entree: { campagne: string; texte: string },
  signal?: AbortSignal,
): Promise<QuestionApi> {
  return appeler("/questions/", { methode: "POST", corps: entree, signal });
}

/** Les trois motifs de signalement du §15. **Liste fermee, pas de champ libre.** */
export const MOTIFS_DE_SIGNALEMENT = [
  { cle: "coordonnees", libelle: "Coordonnées personnelles" },
  { cle: "hors-plateforme", libelle: "Proposition de vente hors plateforme" },
  { cle: "inapproprie", libelle: "Contenu inapproprié" },
] as const;

export type MotifDeSignalement = (typeof MOTIFS_DE_SIGNALEMENT)[number]["cle"];

/**
 * Signale une question deja publiee. §15, niveau 3.
 *
 * ⚠️ **Elle ne depublie rien.** Le serveur enregistre le signalement et laisse
 * la question en ligne : un humain tranche. Depublier sur signalement
 * donnerait a n'importe qui le pouvoir de faire taire n'importe qui.
 */
export function signalerUneQuestion(
  identifiant: string,
  motif: MotifDeSignalement,
  signal?: AbortSignal,
): Promise<{ signale: boolean; message: string }> {
  return appeler(`/questions/${identifiant}/signaler/`, {
    methode: "POST",
    corps: { motif },
    signal,
  });
}

/** Les trois motifs de refus de l'ecran 9. Liste fermee elle aussi. */
export const MOTIFS_DE_REFUS = [
  { cle: "pas-le-produit", libelle: "Ce n'est pas le produit commandé" },
  { cle: "abime", libelle: "Produit visiblement abîmé" },
  { cle: "autre", libelle: "Autre" },
] as const;

export type MotifDeRefus = (typeof MOTIFS_DE_REFUS)[number]["cle"];

/**
 * Refuse le colis a la remise. Ecran 9.
 *
 * ⚠️ **Le refus ouvre un litige, il ne rembourse pas** — la commande passe a
 * `litige` et un humain examine sous 48 h. C'est exactement ce que l'ecran
 * promet, et l'ecrire autrement serait promettre un virement.
 */
export function refuserLeColis(
  identifiant: string,
  motif: MotifDeRefus,
  description: string,
  signal?: AbortSignal,
): Promise<CommandeApi> {
  return appeler<CommandeApi>(`/commandes/${identifiant}/refuser/`, {
    methode: "POST",
    corps: { motif, description },
    signal,
  });
}

// ── Commandes de l'acheteur ────────────────────────────────────────────────

export interface CommandeApi {
  id: number;
  campagne: number;
  campagne_titre: string;
  groupeur: string;
  quantite: number;
  variante: string;
  montant_parts: string;
  frais_livraison: string;
  total: string;
  quartier: string;
  repere: string;
  telephone: string;
  code_livraison: string;
  statut: string;
  passee_le: string;
}

/**
 * Ses commandes. **Identifie par le jeton de session**, plus par son numero.
 *
 * ⚠️ `?telephone=` n'ouvre plus rien, et ne doit pas revenir : huit chiffres
 * se devinent, se lisent sur un recu, se retrouvent dans un repertoire. Le
 * serveur repond 401 a qui n'a pas de session.
 */
export function listerMesCommandes(
  signal?: AbortSignal,
): Promise<CommandeApi[]> {
  return appeler("/commandes/", { signal });
}

/**
 * Paie une part. **Le seul appel qui engage de l'argent.**
 *
 * ⚠️ `cle_idempotence` est generee **par le navigateur, avant l'appel**, et
 * elle doit rester la meme sur un reessai. C'est elle qui garantit qu'un
 * double appui sur « Payer » — geste naturel sur un reseau lent — n'encaisse
 * qu'une fois : le serveur renvoie alors 200 avec la commande existante, au
 * lieu de 201 avec une seconde.
 *
 * ⚠️ **Le montant n'est pas envoye**, et c'est delibere. Le serveur recalcule
 * tout a partir du prix de la campagne et de la quantite ; une requete forgee
 * ne peut donc pas payer 5 000 F une commande de 50 000 F.
 */
export function payer(
  entree: {
    campagne: string;
    /**
     * Le numero **de livraison**, facultatif : celui du compte par defaut.
     *
     * ⚠️ Ce n'est **pas** lui qui identifie l'acheteur — c'est la session. On
     * se fait livrer chez sa sœur sans changer de compte, et accepter ce
     * numero comme identite laisserait payer au nom d'un autre.
     */
    telephone?: string;
    quantite: number;
    variante?: string;
    quartier: string;
    repere: string;
    cle_idempotence: string;
  },
  signal?: AbortSignal,
): Promise<CommandeApi> {
  return appeler("/commandes/payer/", {
    methode: "POST",
    corps: entree,
    signal,
  });
}

/**
 * Traduit une commande de l'API en commande d'interface.
 *
 * ⚠️ Elle a besoin du **catalogue** : le type `Commande` du front porte le
 * groupage entier — c'est lui qui alimente la vignette, le titre et le prix
 * sur l'ecran 8 — alors que l'API ne renvoie qu'un identifiant de campagne et
 * son titre. Le groupage introuvable (campagne cloturee, hors du catalogue
 * ouvert) donne `undefined` : l'appelant l'ecarte plutot que de dessiner une
 * ligne a moitie vide.
 */
export function adapterCommande(
  commande: CommandeApi,
  groupages: readonly Groupage[],
): Commande | undefined {
  const groupage = groupages.find((g) => g.id === String(commande.campagne));
  if (!groupage) {
    return undefined;
  }
  return {
    id: String(commande.id),
    groupage,
    quantite: commande.quantite,
    variante: commande.variante || undefined,
    position: {
      /* L'API ne garde pas **comment** la position a ete obtenue : elle garde
         la position. La source ne sert qu'a l'ecran de saisie, pour savoir
         quel bloc afficher ; une fois la commande passee, elle n'informe plus
         personne. */
      source: "lieu",
      quartier: commande.quartier as Groupage["quartier"],
      repere: commande.repere,
    },
    telephone: commande.telephone,
    montantParts: Number(commande.montant_parts),
    fraisLivraison: Number(commande.frais_livraison),
    total: Number(commande.total),
    codeLivraison: commande.code_livraison,
    statut: commande.statut as Commande["statut"],
    passeeLe: commande.passee_le.slice(0, 10),
    /* La cle d'idempotence ne ressort pas de l'API, et il n'y a aucune raison
       qu'elle le fasse : elle ne sert qu'a l'aller. */
    cleIdempotence: "",
  };
}

// ── Demandes de produit — ecran 12 ─────────────────────────────────────────

export interface DemandeApi {
  id: number;
  produit: string;
  quantite: string;
  quartier: string;
  budget_maximum: string | null;
  precisions: string;
  /** L'adresse de la photo, ou `null`. **Jamais les octets** — voir l'API. */
  photo_url: string | null;
  statut: string;
  campagne: number | null;
  deposee_le: string;
}

/**
 * Ce que l'acheteur a demande. **La demande cree l'offre.**
 *
 * Retrouvee par **le jeton de session**, comme ses commandes.
 */
/**
 * Traduit une demande de l'API vers le type de l'interface.
 *
 * ⚠️ `detail` **n'est pas un champ de l'API**, c'est une phrase d'ecran : elle
 * explique ce que le statut veut dire pour celui qui lit. Un acheteur a qui on
 * affiche « en attente » sans rien d'autre se demande pendant combien de temps,
 * et si quelqu'un regarde — ce qui est exactement la question a laquelle la
 * demande doit repondre, puisqu'elle n'engage a rien.
 */
export function adapterDemande(brute: DemandeApi): Demande {
  const detail: Record<string, string> = {
    "en-attente":
      "Nous la montrons aux groupeurs de votre quartier. Vous serez prévenu si l'un d'eux lance le groupage.",
    "groupage-lance":
      "Un groupeur a lancé ce groupage : vous pouvez commander votre part.",
    "sans-suite":
      "Aucun groupeur ne l'a reprise. Vous pouvez la redéposer, ou en faire une autre.",
  };

  return {
    id: String(brute.id),
    produit: brute.produit,
    quantite: brute.quantite,
    quartier: brute.quartier as Demande["quartier"],
    budgetMaximum: brute.budget_maximum
      ? Number(brute.budget_maximum)
      : undefined,
    precisions: brute.precisions || undefined,
    photoUrl: brute.photo_url ?? undefined,
    deposeeLe: brute.deposee_le.slice(0, 10),
    statut: brute.statut as Demande["statut"],
    detail: detail[brute.statut] ?? "",
    groupageId: brute.campagne ? String(brute.campagne) : undefined,
  };
}

export async function listerMesDemandes(
  signal?: AbortSignal,
): Promise<Demande[]> {
  const page = await appeler<Page<DemandeApi>>("/demandes/", { signal });
  return page.results.map(adapterDemande);
}

/**
 * Depose une demande de produit. **La demande cree l'offre.**
 *
 * ⚠️ **L'ecran 11 ne l'appelait pas.** Il affichait « Demande envoyee » apres
 * un simple changement d'etat local : rien ne partait, et l'acheteur
 * attendait une reponse a une demande que personne n'avait recue. C'est le
 * defaut que cette fonction corrige, et la photo n'en est que l'occasion.
 *
 * Le corps part en **multipart** des qu'il y a une photo, en JSON sinon : une
 * demande sans photo n'a aucune raison de payer le surcout d'un formulaire
 * multipart.
 *
 * Appel **authentifie** — le serveur reconnait l'acheteur a son jeton de
 * session, comme pour ses commandes. Un depot sans session repond 401, et
 * l'ecran doit alors ouvrir la feuille de connexion (§1.5).
 */
export async function deposerUneDemande(
  entree: {
    produit: string;
    quantite: string;
    quartier: Quartier;
    budgetMaximum?: number;
    precisions?: string;
    photo?: Blob;
  },
  signal?: AbortSignal,
): Promise<Demande> {
  const champs: Record<string, string> = {
    produit: entree.produit,
    quantite: entree.quantite,
    quartier: entree.quartier,
  };
  if (entree.budgetMaximum !== undefined) {
    champs.budget_maximum = String(entree.budgetMaximum);
  }
  if (entree.precisions) {
    champs.precisions = entree.precisions;
  }

  let corps: Record<string, string> | FormData = champs;
  if (entree.photo) {
    const formulaire = new FormData();
    for (const [cle, valeur] of Object.entries(champs)) {
      formulaire.append(cle, valeur);
    }
    /* Le nom de fichier est impose ici : celui du telephone peut contenir
       l'identite de son proprietaire (« IMG_Akosua_… »), et cette demande est
       lue par un groupeur qui ne doit rien savoir de l'acheteur (§1.7). */
    formulaire.append("photo", entree.photo, "demande.jpg");
    corps = formulaire;
  }

  const brute = await appeler<DemandeApi>("/demandes/", {
    methode: "POST",
    corps,
    signal,
  });
  return adapterDemande(brute);
}
