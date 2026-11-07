import { AnimatePresence, motion } from "framer-motion";
import {
  Bell,
  BellRing,
  CheckCheck,
  PackageCheck,
  ShieldCheck,
  Undo2,
  Wallet,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import type { Notification, Page } from "@commun/api/types";
import { EVENEMENT_NOUVELLE_COMMANDE } from "@/outils/evenementsCommande";
import { Bouton, fusionner, Squelette } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { depuis } from "@commun/outils/formats";
import { api } from "@commun/outils/requetes";

/**
 * La cloche de la barre du haut.
 *
 * Elle ouvre les notifications **sur place**, dans un panneau : les consulter
 * ne doit pas faire quitter la page qu'on était en train de lire. La page
 * complète reste accessible par un lien en bas du panneau, pour l'historique.
 */

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

export function Cloche() {
  const { connecte } = useSession();
  const emplacement = useLocation();
  const [ouvert, setOuvert] = useState(false);
  const [nonLues, setNonLues] = useState(0);
  const [pulsation, setPulsation] = useState(0);
  const [avis, setAvis] = useState<Notification[] | null>(null);
  const zone = useRef<HTMLDivElement>(null);

  const compter = useCallback(async () => {
    if (!connecte) {
      setNonLues(0);
      return;
    }
    try {
      const { non_lues } = await api.get<{ non_lues: number }>(
        "/notifications/non-lues/",
      );
      setNonLues(non_lues);
    } catch {
      setNonLues(0);
    }
  }, [connecte]);

  // Le compteur se rafraîchit au changement de page : c'est le moment où
  // l'utilisateur regarde l'écran, et ça évite une minuterie qui tournerait
  // dans un onglet oublié.
  useEffect(() => {
    void compter();
    setOuvert(false);
  }, [compter, emplacement.pathname]);

  // Rafraîchissement instantané dès qu'une commande est validée sur la page courante.
  useEffect(() => {
    const surNouvelleCommande = () => {
      setNonLues((actuel) => actuel + 1);
      setPulsation((actuel) => actuel + 1);
      setAvis(null);
      void compter();
    };
    window.addEventListener(EVENEMENT_NOUVELLE_COMMANDE, surNouvelleCommande);
    return () => {
      window.removeEventListener(EVENEMENT_NOUVELLE_COMMANDE, surNouvelleCommande);
    };
  }, [compter]);

  // Les messages sont chargés à l'ouverture (ou rechargés après invalidation).
  useEffect(() => {
    if (!ouvert || avis !== null) return;
    let vivant = true;
    void api
      .get<Page<Notification>>("/notifications/?page_size=12")
      .then((page) => vivant && setAvis(page.results))
      .catch(() => vivant && setAvis([]));
    return () => {
      vivant = false;
    };
  }, [ouvert, avis]);

  useEffect(() => {
    if (!ouvert) return;
    const auClic = (evenement: MouseEvent) => {
      if (!zone.current?.contains(evenement.target as Node)) setOuvert(false);
    };
    const auClavier = (evenement: KeyboardEvent) => {
      if (evenement.key === "Escape") setOuvert(false);
    };
    document.addEventListener("mousedown", auClic);
    window.addEventListener("keydown", auClavier);
    return () => {
      document.removeEventListener("mousedown", auClic);
      window.removeEventListener("keydown", auClavier);
    };
  }, [ouvert]);

  const toutLire = async () => {
    await api.post("/notifications/tout-marquer-lu/").catch(() => undefined);
    setAvis((liste) =>
      liste ? liste.map((item) => ({ ...item, lue_le: new Date().toISOString() })) : liste,
    );
    setNonLues(0);
  };

  const lire = async (notification: Notification) => {
    if (notification.lue_le) return;
    setAvis((liste) =>
      liste
        ? liste.map((item) =>
            item.id === notification.id
              ? { ...item, lue_le: new Date().toISOString() }
              : item,
          )
        : liste,
    );
    setNonLues((reste) => Math.max(0, reste - 1));
    await api
      .post(`/notifications/${notification.id}/marquer-lue/`)
      .catch(() => undefined);
  };

  return (
    <div ref={zone} className="relative shrink-0">
      <button
        onClick={() => {
          setOuvert((etat) => {
            const prochain = !etat;
            if (prochain) setAvis(null);
            return prochain;
          });
        }}
        className={fusionner(
          "relative grid size-10 place-items-center rounded-full transition-colors",
          ouvert ? "bg-accent-doux text-[color:var(--color-accent)]" : "hover:surface-douce",
        )}
        aria-label={`Notifications${nonLues ? ` — ${nonLues} non lues` : ""}`}
        aria-expanded={ouvert}
      >
        <motion.span
          key={pulsation}
          // La cloche s'agite quand il y a du neuf ou qu'une commande vient d'être passée.
          animate={nonLues > 0 ? { rotate: [0, -16, 14, -10, 6, 0] } : { rotate: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
        >
          <Bell className="size-5" />
        </motion.span>
        <AnimatePresence>
          {nonLues > 0 && (
            <motion.span
              key={nonLues}
              initial={{ scale: 0 }}
              animate={{ scale: [1.3, 1] }}
              exit={{ scale: 0 }}
              transition={{ type: "spring", stiffness: 420, damping: 20 }}
              className="absolute right-0.5 top-0.5 grid min-w-[1.1rem] place-items-center rounded-full bg-[color:var(--color-mangue-500)] px-1 text-[0.62rem] font-bold text-white ring-2 ring-[color:var(--fond-carte)]"
            >
              {nonLues > 9 ? "9+" : nonLues}
            </motion.span>
          )}
        </AnimatePresence>
      </button>

      <AnimatePresence>
        {ouvert && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            role="dialog"
            aria-label="Notifications"
            // Ancré à droite et borné par la largeur de l'écran : sur un
            // téléphone, un panneau de largeur fixe déborderait du cadre.
            className="surface absolute right-0 top-12 z-50 w-[min(22rem,calc(100vw-1.5rem))] overflow-hidden rounded-[var(--radius-carte)] shadow-2xl shadow-black/15"
          >
            <div className="flex items-center justify-between gap-2 border-b px-4 py-3">
              <p className="font-bold">Notifications</p>
              {nonLues > 0 && (
                <button
                  onClick={toutLire}
                  className="text-xs font-semibold text-[color:var(--color-accent)]"
                >
                  Tout marquer comme lu
                </button>
              )}
            </div>

            <div className="sans-barre max-h-[min(26rem,60dvh)] overflow-y-auto">
              {!connecte ? (
                <div className="space-y-3 p-6 text-center">
                  <Bell className="texte-doux mx-auto size-7" />
                  <p className="texte-doux text-sm">
                    Connectez-vous pour suivre vos paiements, vos campagnes et
                    vos colis.
                  </p>
                  <Link to="/connexion" onClick={() => setOuvert(false)}>
                    <Bouton taille="sm">Se connecter</Bouton>
                  </Link>
                </div>
              ) : avis === null ? (
                <div className="space-y-2 p-3">
                  <Squelette className="h-14" />
                  <Squelette className="h-14" />
                  <Squelette className="h-14" />
                </div>
              ) : avis.length === 0 ? (
                <div className="p-6 text-center">
                  <Bell className="texte-doux mx-auto size-7" />
                  <p className="texte-doux mt-2 text-sm">
                    Rien à signaler pour l'instant.
                  </p>
                </div>
              ) : (
                <ul>
                  {avis.map((notification) => {
                    const Icone = ICONES[notification.genre] ?? Bell;
                    const lue = notification.lue_le !== null;
                    const contenu = (
                      <div
                        className={fusionner(
                          "flex gap-3 border-b px-4 py-3 transition-colors last:border-0",
                          lue ? "hover:surface-douce" : "bg-accent-doux/60",
                        )}
                      >
                        <span
                          className={fusionner(
                            "grid size-9 shrink-0 place-items-center rounded-full",
                            lue
                              ? "surface-douce texte-doux"
                              : "degrade-accent text-white",
                          )}
                        >
                          <Icone className="size-4" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start justify-between gap-2">
                            <p
                              className={fusionner(
                                "text-sm leading-tight",
                                lue ? "font-medium" : "font-bold",
                              )}
                            >
                              {notification.titre}
                            </p>
                            <span className="texte-doux shrink-0 text-[0.68rem]">
                              {depuis(notification.cree_le)}
                            </span>
                          </div>
                          <p className="texte-doux mt-0.5 line-clamp-2 text-xs leading-relaxed">
                            {notification.message}
                          </p>
                        </div>
                      </div>
                    );

                    return (
                      <li
                        key={notification.id}
                        onClick={() => {
                          void lire(notification);
                          if (notification.lien) setOuvert(false);
                        }}
                      >
                        {notification.lien ? (
                          <Link to={notification.lien}>{contenu}</Link>
                        ) : (
                          contenu
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>

            {connecte && (
              <Link
                to="/notifications"
                onClick={() => setOuvert(false)}
                className="block border-t px-4 py-3 text-center text-sm font-semibold text-[color:var(--color-accent)] transition-colors hover:surface-douce"
              >
                Voir tout l'historique
              </Link>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
