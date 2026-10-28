import type { PalierPrix } from "@commun/api/types";

/**
 * Le prix que le serveur facturera pour une quantité donnée.
 *
 * Reprend à l'identique `Campagne.prix_pour_quantite` (catalogue/models.py) :
 * le palier franchi de plus grand seuil l'emporte, sinon le prix affiché.
 * La règle existe donc à deux endroits ; le test de contrat
 * `tests/test_prix_affiche_et_facture.py` écrit les mêmes cas en dur côté
 * serveur pour que l'un ne dérive pas sans que l'autre le dise.
 *
 * `quantiteTotale` est ce que le serveur compte à la création d'une part :
 * les pièces déjà payées **plus** la quantité demandée. Ce n'est qu'un
 * affichage — le montant réellement consigné est celui que renvoie
 * `POST /participations/` (`montant_total`), jamais ce calcul.
 */
export function prixPourQuantite(
  prixUnitaire: number,
  paliers: Pick<PalierPrix, "quantite_min" | "prix_unitaire">[],
  quantiteTotale: number,
): number {
  let retenu: Pick<PalierPrix, "quantite_min" | "prix_unitaire"> | null = null;
  for (const palier of paliers) {
    if (palier.quantite_min > quantiteTotale) continue;
    if (retenu === null || palier.quantite_min > retenu.quantite_min) retenu = palier;
  }
  return retenu === null ? prixUnitaire : retenu.prix_unitaire;
}
