import { appeler } from "./client";

/**
 * La cloche de l'acheteur.
 *
 * Elle etait dessinee dans les deux en-tetes, **pastille comprise**, et ne
 * faisait rien : le compteur etait la constante `1` ecrite dans le routeur.
 * Elle promettait donc en permanence une information qui n'existait pas.
 */

/** Ce que le serveur peut nous envoyer, et d'ou ca vient. */
export type NatureNotification =
  /** Le groupeur a recu la marchandise. Il la declenche depuis l'ecran 15. */
  | "produit-arrive"
  /** Le groupeur a repondu a une question qu'on avait posee. */
  | "reponse-question"
  /** Le groupage a ete cloture : le groupeur a ete paye, notre garantie porte. */
  | "groupage-cloture"
  /** Le groupage n'a pas abouti, et le montant rembourse est dans le corps. */
  | "groupage-annule";

export interface NotificationApi {
  id: number;
  nature: NatureNotification;
  titre: string;
  /**
   * ⚠️ **Fige a l'envoi, cote serveur.** Une notification decrit un
   * evenement date : « vos 5 000 F vous ont ete rembourses » doit continuer a
   * dire 5 000 F si le prix de la part change ensuite. On l'affiche tel quel,
   * **on ne le reformate jamais** — et surtout on n'y recalcule aucun montant.
   */
  corps: string;
  /** Vers quoi ouvrir au clic. `null` quand la notification ne mene nulle part. */
  campagne: number | null;
  /** Relu a chaque affichage, a la difference de `corps`. */
  campagne_titre: string;
  commande: number | null;
  question: number | null;
  creee_le: string;
  lue: boolean;
}

/** Ses cinquante dernieres notifications, les plus recentes d'abord. */
export function listerMesNotifications(
  signal?: AbortSignal,
): Promise<NotificationApi[]> {
  return appeler("/notifications/", { signal });
}

/**
 * Eteint la pastille.
 *
 * ⚠️ **Tout d'un coup, et pas une par une.** Marquer chaque ligne
 * separement demanderait un appel par notification a l'ouverture du
 * panneau, ce qui est l'inverse de ce qu'on veut sur le forfait de donnees
 * limite du §5. Et le geste reel est celui-la : on ouvre la cloche, on voit,
 * c'est lu.
 */
export function toutMarquerCommeLu(
  signal?: AbortSignal,
): Promise<{ lues: number; non_lues: number }> {
  return appeler("/notifications/tout-lu/", { methode: "POST", signal });
}

/** L'annonce d'arrivee, cote groupeur. Ecran 15. */
export function annoncerLArrivee(
  campagne: string,
  telephone: string,
  signal?: AbortSignal,
): Promise<{
  prevenus: number;
  deja_annonce: boolean;
  annonce_le: string | null;
}> {
  return appeler(`/espace-groupeur/${campagne}/annoncer-l-arrivee/`, {
    methode: "POST",
    /*
     * ⚠️ **Aucun texte n'est envoye, et c'est tout le sujet.** Le groupeur
     * declenche, la plateforme redige. Ajouter ici un champ de message ferait
     * de cette route une messagerie privee vers ses acheteurs — ce que le
     * produit refuse — et un texte partant a trente personnes d'un coup
     * echapperait au filtre du §15.
     */
    corps: { telephone },
    signal,
  });
}
