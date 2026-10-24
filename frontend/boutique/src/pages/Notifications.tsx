import { motion } from "framer-motion";
import {
  Bell,
  BellRing,
  CheckCheck,
  PackageCheck,
  ShieldCheck,
  Undo2,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";

import type { Notification, Page } from "@commun/api/types";
import { Bouton, EtatVide, fusionner, Squelette } from "@commun/composants/ui";
import { depuis } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/** La cloche : ce qui s'est passé pendant qu'on regardait ailleurs. */
const ICONES: Record<string, typeof Bell> = {
  paiement_enregistre: Wallet,
  paiement_recu: Wallet,
  minimum_atteint: BellRing,
  campagne_financee: ShieldCheck,
  marchandise_disponible: PackageCheck,
  retrait_confirme: CheckCheck,
  campagne_annulee: Undo2,
  remboursement: Undo2,
  kyc_decide: ShieldCheck,
  relance_retrait: PackageCheck,
  nouveau_commentaire: BellRing,
  reponse_commentaire: BellRing,
};

export default function Notifications() {
  const { donnees, chargement, recharger } = useRequete<Page<Notification>>(
    "/notifications/",
  );
  const avis = donnees?.results ?? [];
  const nonLues = avis.filter((item) => item.lue_le === null).length;

  const toutLire = useAction(async () => {
    await api.post("/notifications/tout-marquer-lu/");
    await recharger();
  });

  return (
    <div className="mx-auto max-w-2xl space-y-5 px-4 py-6">
      <header className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold">Notifications</h1>
          <p className="texte-doux text-sm">
            {nonLues > 0 ? `${nonLues} non lue${nonLues > 1 ? "s" : ""}` : "Tout est lu"}
          </p>
        </div>
        {nonLues > 0 && (
          <Bouton
            ton="contour"
            taille="sm"
            chargement={toutLire.envoi}
            onClick={() => void toutLire.lancer(undefined as never)}
          >
            Tout marquer comme lu
          </Bouton>
        )}
      </header>

      {chargement ? (
        <div className="space-y-3">
          <Squelette className="h-20" />
          <Squelette className="h-20" />
          <Squelette className="h-20" />
        </div>
      ) : avis.length === 0 ? (
        <EtatVide
          icone={<Bell className="size-7" />}
          titre="Rien à signaler"
          texte="Vous serez prévenu à chaque étape : paiement, financement, arrivée de la marchandise."
        />
      ) : (
        <ul className="space-y-2">
          {avis.map((item, rang) => (
            <LigneNotification
              key={item.id}
              notification={item}
              index={rang}
              surLecture={recharger}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function LigneNotification({
  notification,
  index,
  surLecture,
}: {
  notification: Notification;
  index: number;
  surLecture: () => void;
}) {
  const Icone = ICONES[notification.genre] ?? Bell;
  const lue = notification.lue_le !== null;

  const marquer = async () => {
    if (lue) return;
    await api.post(`/notifications/${notification.id}/marquer-lue/`).catch(() => undefined);
    surLecture();
  };

  const contenu = (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: Math.min(index, 8) * 0.04 }}
      className={fusionner(
        "flex gap-3 rounded-2xl border p-4 transition-colors",
        lue ? "surface" : "bg-accent-doux border-transparent",
      )}
    >
      <span
        className={fusionner(
          "grid size-10 shrink-0 place-items-center rounded-full",
          lue ? "surface-douce texte-doux" : "degrade-accent text-white",
        )}
      >
        <Icone className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className={fusionner("font-semibold", !lue && "text-[color:var(--color-accent-fort)]")}>
            {notification.titre}
          </p>
          <span className="texte-doux shrink-0 text-xs">{depuis(notification.cree_le)}</span>
        </div>
        <p className="texte-doux mt-0.5 text-sm leading-relaxed">{notification.message}</p>
      </div>
    </motion.div>
  );

  return (
    <li onClick={marquer}>
      {notification.lien ? <Link to={notification.lien}>{contenu}</Link> : contenu}
    </li>
  );
}
