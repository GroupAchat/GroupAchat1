import { createContext, useContext, type ReactNode } from "react";

/**
 * Les destinations du chrome acheteur — pied de page, et ce qui suivra.
 *
 * ## Pourquoi un contexte plutot que des proprietes
 *
 * `PiedPage` est monte par **neuf ecrans** : le catalogue, la fiche, les
 * commandes, les demandes, le profil, les questions, et les deux etats de
 * « Demander un produit ». Lui faire descendre cinq fonctions voudrait dire
 * ajouter cinq proprietes a ces neuf ecrans — dont aucun n'a a connaitre le
 * contenu du pied de page. `Questions` n'a rien a voir avec « Devenir
 * groupeur », et il devrait pourtant le transporter.
 *
 * ## ⚠️ Il vit dans `mise-en-page/`, et c'est pour la regle des couches
 *
 * Une couche ne connait que celles **en dessous** d'elle. Poser ce contexte
 * dans la coquille — qui est au-dessus — obligerait `mise-en-page/` a remonter
 * d'un etage, ce qu'aucun fichier de cette couche ne fait aujourd'hui. Ici, la
 * couche ne depend que d'elle-meme : la coquille **fournit**, le chrome
 * **consomme**, et aucune fleche ne s'inverse.
 *
 * ## ⚠️ Toutes les destinations sont facultatives
 *
 * Et `PiedPage` **n'affiche pas** un lien dont la destination manque. C'est ce
 * qui empeche les liens morts de revenir : le pied de page portait onze
 * `<button>` sans `onClick`, et rien ne le signalait. Desormais, une entree
 * non branchee ne se dessine pas.
 */
export interface DestinationsAcheteur {
  onCatalogue?: () => void;
  onDemanderProduit?: () => void;
  onMesCommandes?: () => void;
  onMesDemandes?: () => void;
  /** Vers le depot de dossier du groupeur — il **change de produit**. */
  onDevenirGroupeur?: () => void;
}

const Contexte = createContext<DestinationsAcheteur>({});

export function FournisseurNavigation({
  destinations,
  children,
}: {
  destinations: DestinationsAcheteur;
  children: ReactNode;
}) {
  return (
    <Contexte.Provider value={destinations}>{children}</Contexte.Provider>
  );
}

/**
 * ⚠️ **Ne jette pas hors du fournisseur**, a la difference de `useCatalogue`.
 *
 * La valeur par defaut est un objet vide, donc le chrome monte sans
 * destinations plutot que de casser. C'est deliberé : `PiedPage` doit rester
 * montable seul dans un atelier de maquette, et son comportement sans
 * destination est deja defini — il n'affiche pas les liens concernes.
 */
export function useNavigationAcheteur(): DestinationsAcheteur {
  return useContext(Contexte);
}
