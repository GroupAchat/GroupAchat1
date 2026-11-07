import type { Participation } from "@commun/api/types";

export const EVENEMENT_NOUVELLE_COMMANDE = "ga:nouvelle-commande";

/**
 * Signale dans toute l'interface acheteur qu'une commande vient d'être payée :
 * - déclenche la bannière de notification instantanée,
 * - rafraîchit et anime la cloche de notifications en haut,
 * - incrémente immédiatement (+1) le compteur sur l'onglet « Commandes ».
 */
export function signalerNouvelleCommande(participation: Participation): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent<Participation>(EVENEMENT_NOUVELLE_COMMANDE, {
      detail: participation,
    }),
  );
}
