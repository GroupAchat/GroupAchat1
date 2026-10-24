import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api, ErreurApi } from "@commun/api/client";
import type { Utilisateur } from "@commun/api/types";

/**
 * Qui est connecté, et de quelle couleur est son univers.
 *
 * La teinte dominante suit le profil — orange pour l'acheteur, bleu pour le
 * groupeur. Elle est posée ici, sur `<html>`, une seule fois : aucun composant
 * n'a donc à savoir qui le regarde pour s'habiller correctement.
 */

export type Profil = "visiteur" | "acheteur" | "groupeur" | "administrateur";

interface ValeurSession {
  utilisateur: Utilisateur | null;
  profil: Profil;
  chargement: boolean;
  connecte: boolean;
  /** Vrai seulement si le numéro est vérifié : c'est le seuil pour agir. */
  peutAgir: boolean;
  rafraichir: () => Promise<Utilisateur | null>;
  definir: (utilisateur: Utilisateur | null) => void;
  deconnecter: () => Promise<void>;
}

const Contexte = createContext<ValeurSession | null>(null);

function profilDe(utilisateur: Utilisateur | null): Profil {
  if (!utilisateur) return "visiteur";
  if (utilisateur.est_equipe || utilisateur.role === "administrateur") {
    return "administrateur";
  }
  // Le bleu du groupeur n'arrive qu'avec le badge : tant que le dossier est en
  // examen, la personne n'a pas accès à l'espace, autant ne pas lui en
  // promettre les couleurs.
  if (utilisateur.role === "groupeur" && utilisateur.est_groupeur_valide) {
    return "groupeur";
  }
  return "acheteur";
}

// `children` et non `enfants` : c'est le nom qu'impose React pour le
// contenu imbriqué, comme `is_active` côté Django.
export function FournisseurSession({ children }: { children: ReactNode }) {
  const [utilisateur, setUtilisateur] = useState<Utilisateur | null>(null);
  const [chargement, setChargement] = useState(true);

  const rafraichir = useCallback(async () => {
    try {
      const compte = await api.get<Utilisateur>("/comptes/moi/");
      setUtilisateur(compte);
      return compte;
    } catch (erreur) {
      // 401 et 403 ne sont pas des pannes : c'est simplement un visiteur.
      if (erreur instanceof ErreurApi && [401, 403].includes(erreur.statut)) {
        setUtilisateur(null);
        return null;
      }
      throw erreur;
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => {
    void rafraichir();
  }, [rafraichir]);

  const profil = profilDe(utilisateur);

  useEffect(() => {
    document.documentElement.dataset.profil = profil;
  }, [profil]);

  const deconnecter = useCallback(async () => {
    await api.post("/comptes/deconnexion/");
    setUtilisateur(null);
  }, []);

  const valeur = useMemo<ValeurSession>(
    () => ({
      utilisateur,
      profil,
      chargement,
      connecte: utilisateur !== null,
      peutAgir: Boolean(utilisateur?.telephone_verifie),
      rafraichir,
      definir: setUtilisateur,
      deconnecter,
    }),
    [utilisateur, profil, chargement, rafraichir, deconnecter],
  );

  return <Contexte.Provider value={valeur}>{children}</Contexte.Provider>;
}

export function useSession(): ValeurSession {
  const valeur = useContext(Contexte);
  if (!valeur) {
    throw new Error("useSession doit être utilisé dans un FournisseurSession.");
  }
  return valeur;
}
