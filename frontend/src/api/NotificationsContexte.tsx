import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  listerMesNotifications,
  toutMarquerCommeLu,
  type NotificationApi,
} from "./notifications";
import { ErreurApi } from "./client";

/**
 * La cloche, partagee par tout le cote acheteur.
 *
 * ## Pourquoi un contexte, et pas des proprietes
 *
 * La cloche est dessinee dans **les deux en-tetes** — celui du telephone et
 * celui du bureau — qui sont montes par quatre ecrans differents. Le compteur
 * de non-lues etait donc ecrit `notifications={1}` a **sept endroits** : une
 * constante, repetee sept fois, qui allumait la pastille en permanence pour
 * une notification qui n'existait pas.
 *
 * Faire descendre le vrai compteur par proprietes aurait voulu dire le passer
 * a travers `Fil`, `GroupagesOuverts` et `RechercheEtFiltres`, qui n'ont rien
 * a voir avec les notifications. Un contexte le tient en un seul endroit.
 *
 * ## ⚠️ Les en-tetes gardent leurs proprietes
 *
 * `mise-en-page/` **ne lit pas `api/`** : la regle des couches veut qu'une
 * couche ne connaisse que celles en dessous d'elle, et aucun fichier de
 * `mise-en-page/` n'importe l'API aujourd'hui. Ce sont donc les **pages** qui
 * consultent ce contexte et passent le compteur a leur en-tete. Les en-tetes
 * restent montables seuls, ce qui compte pour un atelier de maquette.
 *
 * ## ⚠️ Il ne scrute pas le serveur
 *
 * Aucun intervalle, aucune interrogation repetee. On relit a l'ouverture de
 * l'application et apres un geste qui a pu en produire une — et c'est une
 * decision de produit, pas de la paresse : le §5 pose un forfait de donnees
 * limite, et une cloche qui interroge le serveur toutes les trente secondes
 * consomme toute la journee pour un evenement qui arrive deux fois par
 * semaine. Le jour ou il faudra du temps reel, ce sera une poussee du
 * serveur, pas une boucle dans le navigateur.
 */
interface Cloche {
  notifications: readonly NotificationApi[];
  chargement: boolean;
  erreur?: ErreurApi;
  /** Le nombre de non-lues : c'est lui qui allume la pastille. */
  nonLues: number;
  /** Le panneau est-il ouvert. */
  ouvert: boolean;
  ouvrir: () => void;
  fermer: () => void;
  /** Relit la liste depuis le serveur. */
  recharger: () => void;
}

const Contexte = createContext<Cloche | undefined>(undefined);

export function FournisseurNotifications({
  /** Rien n'est demande sans session : les notifications sont nominatives. */
  connecte,
  children,
}: {
  connecte: boolean;
  children: ReactNode;
}) {
  const [notifications, setNotifications] = useState<
    readonly NotificationApi[]
  >([]);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState<ErreurApi>();
  const [ouvert, setOuvert] = useState(false);

  const recharger = useCallback(() => {
    if (!connecte) {
      /* Deconnexion : on vide, sinon la pastille de la session precedente
         resterait allumee pour quelqu'un qui n'est plus la meme personne. */
      setNotifications([]);
      setErreur(undefined);
      return;
    }
    setChargement(true);
    listerMesNotifications()
      .then((liste) => {
        setNotifications(liste);
        setErreur(undefined);
      })
      .catch((cause) => {
        if (cause instanceof ErreurApi) {
          setErreur(cause);
        }
      })
      .finally(() => setChargement(false));
  }, [connecte]);

  useEffect(recharger, [recharger]);

  const ouvrir = () => {
    setOuvert(true);
    /*
     * ⚠️ **Marque tout comme lu a l'ouverture, et eteint la pastille
     * localement sans attendre le serveur.**
     *
     * Le geste reel est celui-la : on ouvre la cloche, on voit, c'est lu.
     * Attendre la reponse ferait clignoter la pastille une demi-seconde apres
     * l'ouverture du panneau, sur un reseau lent bien davantage.
     *
     * Les lignes gardent leur point de non-lu **dans ce panneau-ci** : c'est
     * ce qui permet de voir d'un coup d'oeil ce qu'on n'avait pas vu. Elles
     * l'auront perdu a la prochaine ouverture, ce qui est exactement
     * l'intention.
     */
    if (notifications.some((notification) => !notification.lue)) {
      toutMarquerCommeLu().catch(() => {
        /* Un echec n'a rien casse : la pastille se rallumera au prochain
           chargement, ce qui est la bonne degradation — on prefere la montrer
           une fois de trop que cacher quelque chose qu'on n'a pas lu. */
      });
    }
  };

  const nonLues = notifications.filter(
    (notification) => !notification.lue,
  ).length;

  return (
    <Contexte.Provider
      value={{
        notifications,
        chargement,
        erreur,
        nonLues: ouvert ? 0 : nonLues,
        ouvert,
        ouvrir,
        fermer: () => setOuvert(false),
        recharger,
      }}
    >
      {children}
    </Contexte.Provider>
  );
}

export function useNotifications(): Cloche {
  const valeur = useContext(Contexte);
  if (valeur === undefined) {
    throw new Error(
      "useNotifications hors de FournisseurNotifications : l'écran doit être " +
        "monté dans la coquille acheteur.",
    );
  }
  return valeur;
}
