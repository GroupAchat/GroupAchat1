import { useEffect, useRef } from "react";
import {
  type NatureNotification,
  type NotificationApi,
} from "../../api/notifications";
import { formaterDateCourte } from "../../domaine/format";
import {
  IconeCamion,
  IconeCoche,
  IconeFermer,
  IconeQuestion,
  IconeAlerte,
} from "../../ui/Icones";
import EtatVide from "../../ui/EtatVide";
import { ErreurReseau, ListeEnChargement } from "../../ui/EtatReseau";
import { type ErreurApi } from "../../api/client";

/**
 * La cloche, ouverte. §1.9 bis.
 *
 * ## Ce qu'elle repare
 *
 * La cloche existait dans les deux en-tetes acheteur, **avec sa pastille**, et
 * ne faisait rien : le compteur etait la constante `1` ecrite dans le routeur.
 * Elle affichait donc une notification non lue en permanence, pour une
 * notification qui n'existait pas — ce qui est pire qu'une cloche absente,
 * parce qu'on finit par ne plus la croire.
 *
 * ## ⚠️ Ce n'est pas une messagerie
 *
 * **Tout ce qui s'affiche ici a ete ecrit par la plateforme.** Un groupeur
 * peut declencher une notification — « le produit est arrive » — il n'en
 * redige jamais le texte. D'ou l'absence totale de champ de reponse dans ce
 * panneau : il n'y a personne a qui repondre. Une question se pose sur la
 * fiche du produit, en public (§1.7), et c'est la que mene la notification de
 * reponse.
 *
 * ## ⚠️ Le corps n'est jamais reformate
 *
 * Il est fige a l'envoi cote serveur, parce qu'une notification decrit un
 * evenement date. On l'affiche tel quel : recalculer un montant a
 * l'affichage ferait dire a un remboursement de la semaine derniere le prix
 * de la part d'aujourd'hui.
 *
 * ## Meme panneau partout
 *
 * Feuille basse sur telephone, carte dans l'angle a partir de `sm` — la meme
 * mecanique que `PanneauQuestions`, et pour la meme raison : un panneau de
 * 384 px dans un coin de 390 px n'est pas un coin.
 */

/** L'icone dit de quoi il s'agit avant qu'on ait lu le titre. */
const ICONES: Record<
  NatureNotification,
  (proprietes: { taille?: number; className?: string }) => React.ReactElement
> = {
  "produit-arrive": IconeCamion,
  "reponse-question": IconeQuestion,
  "groupage-cloture": IconeCoche,
  "groupage-annule": IconeAlerte,
};

/**
 * ⚠️ **Le ton suit le sens, pas la nouveaute.**
 *
 * `groupage-annule` est la seule en orange d'alerte : c'est la seule qui
 * annonce quelque chose qui ne s'est pas passe comme prevu. Mettre les quatre
 * en orange ferait de la couleur un ornement, ce que le §1.2 interdit — une
 * couleur signale une action, un etat ou un risque.
 */
const TONS: Record<NatureNotification, string> = {
  "produit-arrive": "bg-confiance-fond text-confiance",
  "reponse-question": "bg-confiance-fond text-confiance",
  "groupage-cloture": "bg-confiance-fond text-confiance",
  "groupage-annule": "bg-primaire-fond text-primaire-texte-sur-fond",
};

export default function PanneauNotifications({
  notifications,
  chargement,
  erreur,
  onRecharger,
  onFermer,
  onOuvrir,
}: {
  notifications: readonly NotificationApi[];
  chargement: boolean;
  /** L'erreur reseau, s'il y en a une. */
  erreur?: ErreurApi;
  onRecharger: () => void;
  onFermer: () => void;
  /** Ouvre ce que la notification concerne. Sans cible, elle n'est pas cliquable. */
  onOuvrir: (notification: NotificationApi) => void;
}) {
  const panneau = useRef<HTMLDivElement>(null);

  /* Echap ferme, comme tout ce qui se pose par-dessus une page. */
  useEffect(() => {
    const auClavier = (evenement: KeyboardEvent) => {
      if (evenement.key === "Escape") onFermer();
    };
    document.addEventListener("keydown", auClavier);
    return () => document.removeEventListener("keydown", auClavier);
  }, [onFermer]);

  useEffect(() => {
    panneau.current?.focus();
  }, []);

  return (
    <div
      ref={panneau}
      tabIndex={-1}
      role="dialog"
      aria-modal="false"
      aria-label="Notifications"
      /* Pas de voile : on doit pouvoir continuer a lire la page. */
      className="fixed inset-x-0 bottom-0 z-30 flex max-h-[80dvh] flex-col rounded-t-2xl border border-bordure bg-white shadow-[0_-4px_24px_rgba(29,25,22,0.18)] sm:inset-x-auto sm:top-20 sm:right-6 sm:bottom-auto sm:max-h-[min(34rem,calc(100dvh-7rem))] sm:w-96 sm:rounded-2xl sm:shadow-[0_8px_32px_rgba(29,25,22,0.22)]"
    >
      <header className="flex shrink-0 items-center gap-2 border-b border-filet px-4 py-3">
        <h2 className="min-w-0 flex-1 text-sm font-semibold text-texte">
          Notifications
        </h2>
        <button
          type="button"
          onClick={onFermer}
          aria-label="Fermer les notifications"
          className="flex size-10 shrink-0 items-center justify-center rounded-full text-texte-secondaire hover:bg-surface-douce"
        >
          <IconeFermer taille={18} />
        </button>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {chargement ? (
          <div className="px-4 py-4">
            <ListeEnChargement nombre={3} />
          </div>
        ) : erreur !== undefined ? (
          <div className="px-4 py-4">
            <ErreurReseau erreur={erreur} onReessayer={onRecharger} />
          </div>
        ) : notifications.length === 0 ? (
          <div className="px-4 py-2">
            <EtatVide
              titre="Rien de neuf"
              explication="Vous serez prévenu ici quand un groupage que vous avez rejoint avance."
              registre="attente"
            />
          </div>
        ) : (
          <ul className="divide-y divide-filet">
            {notifications.map((notification) => (
              <Ligne
                key={notification.id}
                notification={notification}
                onOuvrir={onOuvrir}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Ligne({
  notification,
  onOuvrir,
}: {
  notification: NotificationApi;
  onOuvrir: (notification: NotificationApi) => void;
}) {
  const Icone = ICONES[notification.nature];
  /* Une notification sans cible n'est pas cliquable : un element qui reagit au
     survol et ne mene nulle part se fait essayer deux fois. */
  const cliquable =
    notification.campagne !== null || notification.commande !== null;

  const contenu = (
    <>
      <span
        className={`flex size-9 shrink-0 items-center justify-center rounded-full ${TONS[notification.nature]}`}
      >
        <Icone taille={18} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-start gap-2">
          <span className="min-w-0 flex-1 text-sm font-semibold text-texte">
            {notification.titre}
          </span>
          {/* Le point de non-lu, pas un fond colore sur toute la ligne : la
              liste reste lisible quand tout est neuf, ce qui est le cas la
              premiere fois qu'on l'ouvre. */}
          {!notification.lue ? (
            <span
              aria-label="Non lue"
              className="mt-1.5 size-2 shrink-0 rounded-full bg-marque"
            />
          ) : null}
        </span>
        <span className="mt-0.5 block text-sm text-texte-secondaire">
          {notification.corps}
        </span>
        <span className="mt-1 block text-xs text-texte-mention">
          {formaterDateCourte(notification.creee_le)}
        </span>
      </span>
    </>
  );

  return (
    <li>
      {cliquable ? (
        <button
          type="button"
          onClick={() => onOuvrir(notification)}
          className="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-surface-douce"
        >
          {contenu}
        </button>
      ) : (
        <div className="flex items-start gap-3 px-4 py-3">{contenu}</div>
      )}
    </li>
  );
}
