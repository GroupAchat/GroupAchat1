import { useCallback, useEffect, useRef, useState } from "react";

import { api, ErreurApi } from "@commun/api/client";

/**
 * Un petit crochet de lecture, sans bibliothèque de cache.
 *
 * Les écrans de ce produit lisent peu et écrivent beaucoup ; une couche de
 * cache apporterait surtout des questions d'invalidation. Ce dont on a besoin
 * — recharger après une action — tient dans `recharger`.
 */
export function useRequete<T>(chemin: string | null, dependances: unknown[] = []) {
  const [donnees, setDonnees] = useState<T | null>(null);
  const [chargement, setChargement] = useState(chemin !== null);
  const [erreur, setErreur] = useState<ErreurApi | null>(null);

  // Garde-fou contre les réponses qui reviennent dans le désordre : seule la
  // dernière demande a le droit d'écrire dans l'état, sinon un filtre tapé
  // vite affiche le résultat du filtre précédent.
  const compteur = useRef(0);

  const charger = useCallback(async () => {
    if (chemin === null) {
      setDonnees(null);
      setChargement(false);
      return;
    }
    const demande = ++compteur.current;
    setChargement(true);
    try {
      const resultat = await api.get<T>(chemin);
      if (demande === compteur.current) {
        setDonnees(resultat);
        setErreur(null);
      }
    } catch (souci) {
      if (demande === compteur.current) {
        setErreur(
          souci instanceof ErreurApi
            ? souci
            : new ErreurApi(0, "Connexion impossible. Vérifiez votre réseau."),
        );
      }
    } finally {
      if (demande === compteur.current) setChargement(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chemin, ...dependances]);

  useEffect(() => {
    void charger();
  }, [charger]);

  return { donnees, chargement, erreur, recharger: charger, definir: setDonnees };
}

/** Une action qui écrit : suit l'envoi en cours et l'erreur éventuelle. */
export function useAction<Entree, Sortie>(
  executer: (entree: Entree) => Promise<Sortie>,
) {
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState<ErreurApi | null>(null);

  const lancer = useCallback(
    async (entree: Entree): Promise<Sortie | null> => {
      setEnvoi(true);
      setErreur(null);
      try {
        return await executer(entree);
      } catch (souci) {
        setErreur(
          souci instanceof ErreurApi
            ? souci
            : new ErreurApi(0, "Connexion impossible. Vérifiez votre réseau."),
        );
        return null;
      } finally {
        setEnvoi(false);
      }
    },
    [executer],
  );

  return { lancer, envoi, erreur, effacerErreur: () => setErreur(null) };
}

export { api, ErreurApi };
