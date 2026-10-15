import type {
  Campagne,
  DemandeAgregee,
  MouvementPortefeuille,
  StatutCampagne,
  Tache,
} from "../domaine/groupeur";
import type {
  Categorie,
  MediaProduit,
  Quartier,
} from "../domaine/groupage";
import { appeler } from "./client";

/**
 * L'espace de travail du groupeur : ses campagnes, son argent, ses questions.
 *
 * ⚠️ **Rien de ce qui passe par ici ne porte l'identite d'un acheteur.** Le
 * groupeur voit des codes de livraison et des quartiers, jamais un nom, un
 * numero ou une adresse (§1.7). Ce n'est pas une precaution de confort : c'est
 * ce qui protege le modele contre la desintermediation. Le serveur tient
 * cette regle — `api_groupeur.py` — et `test_espace_groupeur.py` verifie
 * qu'aucune reponse ne laisse fuir un acheteur.
 *
 * ⚠️ **Le groupeur est identifie par son numero de telephone**, comme
 * l'acheteur. Qui connait le numero voit le portefeuille. Acceptable sur des
 * donnees fictives, **plus du tout ensuite** : c'est l'authentification qui
 * reglera ca.
 */

// ── Tableau de bord — ecran 13 ─────────────────────────────────────────────

export interface TableauDeBordApi {
  pseudonyme: string;
  niveau: string;
  plafond: number | null;
  campagnes_ouvertes: number;
  commandes: number;
  /**
   * L'argent des acheteurs sur des campagnes **encore ouvertes**.
   *
   * ⚠️ Il ne lui appartient pas : il est **detenu jusqu'a la cloture**.
   * Jamais « bloque jusqu'a la livraison » (§1.7) — et surtout, jamais
   * additionne a `disponible`, qui est ce qui lui a ete verse.
   */
  en_collecte: number;
  disponible: number;
  /**
   * D'ou viennent ses commandes. **Agrege par le serveur**, en une requete.
   *
   * ⚠️ Des quartiers et des nombres, jamais un nom ni un repere : un quartier
   * n'identifie personne (§1.7), et c'est ce qui autorise a le lui montrer.
   */
  par_quartier: { quartier: string; commandes: number; part: number }[];
  taches: Tache[];
}

export function lireLeTableauDeBord(
  telephone: string,
  signal?: AbortSignal,
): Promise<TableauDeBordApi> {
  return appeler("/espace-groupeur/tableau-de-bord/", {
    parametres: { telephone },
    signal,
  });
}

// ── Ses campagnes — ecrans 14, 15, 16 ──────────────────────────────────────

export interface CampagneGroupeurApi {
  id: number;
  produit: string;
  categorie: Categorie;
  prix_part: string;
  commandes: number;
  collecte: string;
  objectif_participants: number;
  progression: number;
  heures_restantes: number;
  statut: StatutCampagne;
  photo: string;
  arrivee_annoncee_le: string | null;
}

export function adapterCampagne(brute: CampagneGroupeurApi): Campagne {
  return {
    id: String(brute.id),
    produit: brute.produit,
    categorie: brute.categorie,
    prixPart: Number(brute.prix_part),
    commandes: brute.commandes,
    collecte: Number(brute.collecte),
    objectifParticipants: brute.objectif_participants,
    progression: brute.progression,
    heuresRestantes: brute.heures_restantes,
    statut: brute.statut,
    photo: brute.photo || undefined,
    arriveeAnnonceeLe: brute.arrivee_annoncee_le ?? undefined,
  };
}

export async function listerMesCampagnes(
  telephone: string,
  signal?: AbortSignal,
): Promise<Campagne[]> {
  const brutes = await appeler<CampagneGroupeurApi[]>(
    "/espace-groupeur/campagnes/",
    { parametres: { telephone }, signal },
  );
  return brutes.map(adapterCampagne);
}

export interface NouvelleCampagne {
  telephone: string;
  titre: string;
  /**
   * Combien de personnes le groupeur veut reunir. **Obligatoire.**
   *
   * ⚠️ Le serveur refuse une creation sans lui : c'est le denominateur de la
   * barre de progression des cartes (§2.5), et un objectif pose d'office
   * serait publie aux acheteurs sans qu'il l'ait choisi.
   */
  objectif_participants: number;
  description: string;
  contenu_part: string;
  categorie: Categorie;
  prix_part: number;
  duree_heures: number;
  quartier_remise: string;
  point_remise: string;
  /** Jusqu'a 4 images et 2 videos. Le serveur refuse au-dela. */
  medias?: MediaProduit[];
  caracteristiques?: { cle: string; valeur: string }[];
  variante_libelle?: string;
  variante_options?: string[];
  remise_le?: string;
}

/**
 * Lance un groupage.
 *
 * ⚠️ **Le serveur refuse si le dossier KYC n'est pas valide** (§10.5) ou si la
 * campagne depasserait le plafond de collecte (§10.4). Les deux vivent dans
 * `Campagne.clean`, donc **au modele** et non dans une vue : un bouton masque
 * dans l'interface ne protege de rien, il suffit d'une requete directe. Le
 * message du refus est explicite et s'affiche tel quel.
 */
export function creerUneCampagne(
  campagne: NouvelleCampagne,
  signal?: AbortSignal,
): Promise<CampagneGroupeurApi> {
  return appeler("/espace-groupeur/campagnes/", {
    methode: "POST",
    corps: campagne,
    signal,
  });
}

export interface ResultatCloture {
  collecte: number;
  frais_plateforme: number;
  montant_retirable: number;
  frais_livraison_collectes: number;
}

/**
 * Cloture un groupage : **le solde du groupeur devient retirable**.
 *
 * ⚠️ **Rien ne part ici.** L'argent etait deja le sien depuis le paiement de
 * ses acheteurs ; il cesse simplement d'etre detenu. Aucun ecran ne doit
 * ecrire « votre argent est bloque jusqu'a la livraison » — la formulation
 * autorisee est « detenu jusqu'a la cloture ».
 */
export function cloturerUneCampagne(
  telephone: string,
  campagne: string,
  signal?: AbortSignal,
): Promise<ResultatCloture> {
  return appeler(`/espace-groupeur/${campagne}/cloturer/`, {
    methode: "POST",
    corps: { telephone },
    signal,
  });
}

// ── Les commandes d'une campagne — ecran 15 ────────────────────────────────

export interface CommandeGroupeurApi {
  code_livraison: string;
  quantite: number;
  variante: string;
  montant_parts: string;
  quartier: string;
}

/**
 * Les commandes d'une de ses campagnes.
 *
 * ⚠️ **Cinq champs, et pas un de plus.** Le code identifie la commande, le
 * quartier sert a organiser les tournees. Ajouter l'acheteur, le repere ou le
 * telephone lui permettrait de se constituer un fichier de clients et de les
 * servir hors plateforme — autrement dit de nous supprimer du circuit.
 */
export function listerLesCommandes(
  campagne: string,
  signal?: AbortSignal,
): Promise<CommandeGroupeurApi[]> {
  return appeler(`/campagnes/${campagne}/commandes/`, { signal });
}

// ── Portefeuille — ecran 18 ────────────────────────────────────────────────

export type EtatRetrait = "retirable" | "demande" | "effectue" | "annule";

export interface PortefeuilleApi {
  disponible: number;
  retire: number;
  mouvements: {
    id: string;
    date: string;
    campagne: string;
    etat: EtatRetrait;
    collecte: number;
    frais_plateforme: number;
    montant: number;
  }[];
}

/**
 * ⚠️ **Le libelle depend de l'etat, et la difference compte.**
 *
 * Un solde devenu retirable n'est pas de l'argent parti. Les ecrire pareil
 * ferait croire au groupeur qu'il a ete paye deux fois pour le meme groupage —
 * c'est le genre de confusion qui se termine par un appel au support, et par
 * un doute qui ne se repare pas.
 */
const LIBELLE_RETRAIT: Record<EtatRetrait, string> = {
  retirable: "Groupage clôturé",
  demande: "Retrait demandé",
  effectue: "Retrait",
  annule: "Groupage annulé",
};

export async function lireLePortefeuille(
  telephone: string,
  signal?: AbortSignal,
): Promise<{
  disponible: number;
  retire: number;
  mouvements: MouvementPortefeuille[];
}> {
  const brut = await appeler<PortefeuilleApi>("/espace-groupeur/portefeuille/", {
    parametres: { telephone },
    signal,
  });

  return {
    disponible: brut.disponible,
    retire: brut.retire,
    /**
     * ⚠️ **Deux lignes par groupage, et c'est volontaire.**
     *
     * Les frais ont leur propre ligne, negative, plutot que d'etre deduits en
     * silence du montant. Fondus dans le total, ils priveraient le groupeur du
     * moyen de verifier les 1 500 F — et c'est exactement le genre d'opacite
     * qui fait douter d'une plateforme qui tient l'argent des autres.
     *
     * Un groupage annule ne porte **aucune ligne de frais** : il n'y en a pas,
     * et une ligne a zero serait a expliquer.
     */
    mouvements: brut.mouvements.flatMap((retrait) => {
      const entree = {
        id: `${retrait.id}-net`,
        date: retrait.date,
        libelle: `${LIBELLE_RETRAIT[retrait.etat]} — ${retrait.campagne}`,
        montant: retrait.etat === "annule" ? undefined : retrait.montant,
        mention: retrait.etat === "annule" ? "Aucun frais" : undefined,
      };

      if (retrait.etat === "annule") return [entree];

      return [
        entree,
        {
          id: `${retrait.id}-frais`,
          date: retrait.date,
          libelle:
            retrait.etat === "effectue"
              ? "Frais Group Achat — retenus"
              : "Frais Group Achat — à retenir au retrait",
          montant: -retrait.frais_plateforme,
        },
      ];
    }),
  };
}

/**
 * Le bouton « Retirer mes fonds » de l'ecran 18.
 *
 * ⚠️ **Il retire tout ce qui est retirable, d'un geste**, et la reponse dit
 * combien de groupages ont ete soldes pour que la confirmation puisse annoncer
 * les frais : 1 500 F par groupage abouti.
 */
export interface ResultatRetrait {
  groupages: number;
  frais_plateforme: number;
  montant: number;
  disponible: number;
}

export function retirerMesFonds(
  telephone: string,
  signal?: AbortSignal,
): Promise<ResultatRetrait> {
  return appeler("/espace-groupeur/retirer/", {
    methode: "POST",
    corps: { telephone },
    signal,
  });
}

// ── Demandes agregees — ecran 19 ───────────────────────────────────────────

export interface DemandeAgregeeApi {
  id: string;
  produit: string;
  quartier: string;
  personnes: number;
  jours_ecoules: number;
  budget_moyen: number;
  /** La quantite que les demandeurs ont ecrite le plus souvent. */
  quantite_courante: string;
}

export async function listerLesDemandes(
  telephone: string,
  signal?: AbortSignal,
): Promise<DemandeAgregee[]> {
  const brutes = await appeler<DemandeAgregeeApi[]>(
    "/espace-groupeur/demandes/",
    { parametres: { telephone }, signal },
  );

  return brutes.map((brute) => ({
    id: brute.id,
    produit: brute.produit,
    quartier: brute.quartier as Quartier,
    personnes: brute.personnes,
    joursEcoules: brute.jours_ecoules,
    budgetMoyen: brute.budget_moyen,
    /**
     * **La quantite la plus souvent demandee**, et non un volume estime.
     *
     * ⚠️ Le volume, lui, n'est pas connu : il supposerait de connaitre le
     * conditionnement du produit — « 14 personnes × 1 sac de 25 kg » — ce que
     * la demande ne porte pas. L'inventer sur un ecran qui sert a decider
     * d'un achat en gros serait pire que de ne rien afficher.
     *
     * Ce que les gens ont ecrit, en revanche, se compte : c'est ce que le
     * serveur renvoie ici. La ligne disparait quand il n'y a rien a dire.
     */
    volumeEstime: brute.quantite_courante ?? "",
  }));
}

// ── Questions recues — ecran 20 ────────────────────────────────────────────

export interface QuestionRecueApi {
  id: number;
  campagne: number;
  campagne_titre: string;
  /** « Akosua D. » — prenom et initiale, jamais un nom complet (§1.7). */
  auteur: string;
  texte: string;
  reponse: string;
  posee_le: string;
}

export function listerLesQuestionsRecues(
  telephone: string,
  signal?: AbortSignal,
): Promise<QuestionRecueApi[]> {
  return appeler("/espace-groupeur/questions/", {
    parametres: { telephone },
    signal,
  });
}

/**
 * Repond a une question publique.
 *
 * ⚠️ **La reponse passe par le filtre de moderation** (§15), qui agit dans les
 * deux sens : un groupeur qui glisse son numero dans une reponse publique
 * contourne la plateforme aussi surement qu'un acheteur qui le demande — et
 * c'est meme le cas le plus probable des deux, puisque c'est lui qui y gagne.
 * Le refus revient en 400, sur le champ `reponse`.
 */
export function repondreALaQuestion(
  entree: { telephone: string; question: number; reponse: string },
  signal?: AbortSignal,
): Promise<{ id: number; reponse: string }> {
  return appeler(`/espace-groupeur/${entree.question}/repondre/`, {
    methode: "POST",
    corps: { telephone: entree.telephone, reponse: entree.reponse },
    signal,
  });
}
