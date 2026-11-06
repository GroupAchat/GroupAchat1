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
 * La teinte dominante suit **le lieu, pas le compte** : l'orange de la
 * boutique, le bleu de l'espace OAG. Un OAG qui revient faire ses courses
 * doit retrouver la boutique telle qu'il l'a quittée ; lui peindre le
 * catalogue en bleu parce qu'il organise des groupages par ailleurs
 * reviendrait à lui dire qu'il n'est plus chez lui.
 *
 * Par défaut la teinte suit quand même le compte — c'est ce dont la console
 * d'administration a besoin, elle n'a qu'un seul univers. Une application à
 * plusieurs lieux appelle `imposerTeinte()` et reprend la main.
 *
 * L'attribut est posé ici, sur `<html>`, **à un seul endroit** : deux effets
 * qui écrivent le même attribut finiraient par se contredire au rechargement
 * d'une page, et la couleur dépendrait de l'ordre des rendus.
 */

export type Profil = "visiteur" | "acheteur" | "groupeur" | "administrateur";

interface ValeurSession {
  utilisateur: Utilisateur | null;
  /** Le profil du **compte**, indépendamment de la page affichée. */
  profil: Profil;
  /** Impose la teinte du lieu ; `null` rend la main au profil du compte. */
  imposerTeinte: (profil: Profil | null) => void;
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
  // Le bleu de l'OAG n'arrive qu'avec le badge : tant que le dossier est en
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
  const [teinteImposee, imposerTeinte] = useState<Profil | null>(null);

  useEffect(() => {
    document.documentElement.dataset.profil = teinteImposee ?? profil;
  }, [profil, teinteImposee]);

  const deconnecter = useCallback(async () => {
    await api.post("/comptes/deconnexion/");
    setUtilisateur(null);
  }, []);

  const valeur = useMemo<ValeurSession>(
    () => ({
      utilisateur,
      profil,
      imposerTeinte,
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
