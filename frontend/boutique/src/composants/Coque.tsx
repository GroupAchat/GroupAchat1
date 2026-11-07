import { AnimatePresence, motion } from "framer-motion";
import {
  BellRing,
  CheckCircle2,
  Clapperboard,
  Compass,
  MessageSquare,
  Search,
  ShoppingBag,
  Store,
  User,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";

import type { Page, Participation } from "@commun/api/types";
import { Cloche } from "@/composants/Cloche";
import { EVENEMENT_NOUVELLE_COMMANDE } from "@/outils/evenementsCommande";
import { Marque } from "@commun/composants/Marque";
import { Avatar, fusionner } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { francs } from "@commun/outils/formats";
import { api } from "@commun/outils/requetes";

/**
 * L'ossature mobile acheteur : 4 onglets dédiés.
 * Accueil (Fil vidéo immersif), Catalogue, Commandes, Profil (accès OAG).
 */

const ONGLETS = [
  { vers: "/", libelle: "Accueil", icone: Clapperboard, exact: true },
  { vers: "/catalogue", libelle: "Catalogue", icone: Compass },
  { vers: "/mes-achats", libelle: "Commandes", icone: ShoppingBag },
  { vers: "/profil", libelle: "Profil", icone: User },
];

export function EnTete() {
  const { utilisateur, connecte } = useSession();
  const naviguer = useNavigate();

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/95 backdrop-blur-md px-3 py-2.5 shadow-xs">
      <div className="flex items-center justify-between gap-2">
        <Link to="/" className="flex shrink-0 items-center" aria-label="Accueil">
          <Marque taille="moyenne" />
        </Link>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => naviguer("/catalogue?focus=1")}
            className="surface-douce grid size-9 place-items-center rounded-full transition-colors hover:brightness-95"
            aria-label="Rechercher"
          >
            <Search className="size-4" />
          </button>

          {connecte && (
            <Link
              to="/messages"
              className="surface-douce grid size-9 place-items-center rounded-full transition-colors hover:brightness-95"
              aria-label="Mes messages"
            >
              <MessageSquare className="size-4" />
            </Link>
          )}

          <Cloche />

          {connecte ? (
            <Link to="/profil" className="shrink-0 pl-1" aria-label="Mon profil">
              <Avatar nom={utilisateur?.nom_complet ?? "?"} taille={32} />
            </Link>
          ) : (
            <Link
              to="/connexion"
              className="degrade-accent shrink-0 rounded-full px-3 py-1.5 text-xs font-bold text-white shadow-sm transition-transform active:scale-95"
            >
              Connexion
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

export function EnTeteGroupeur({ livraison }: { livraison?: boolean } = {}) {
  const { utilisateur, deconnecter } = useSession();
  const naviguer = useNavigate();

  if (livraison) {
    return (
      <header className="sticky top-0 z-40 border-b bg-[color:var(--color-marine-950)] px-3 py-2.5 text-white">
        <div className="flex items-center justify-between gap-2">
          <Marque variante="blanc" />
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/70">
              {utilisateur?.transporteur === "poste"
                ? "La Poste"
                : utilisateur?.transporteur === "gozem"
                  ? "Gozem"
                  : "Livraison"}
            </span>
            <button
              onClick={async () => {
                await deconnecter();
                naviguer("/");
              }}
              className="rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold hover:bg-white/20"
            >
              Quitter
            </button>
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="sticky top-0 z-40 border-b bg-[color:var(--color-marine-950)] px-3 py-2.5 text-white">
      <div className="flex items-center justify-between gap-2">
        <Link to="/groupeur" className="flex items-center" aria-label="Tableau de bord OAG">
          <Marque variante="blanc" />
        </Link>
        <div className="flex items-center gap-2">
          <Link
            to="/"
            className="flex items-center gap-1.5 rounded-full bg-amber-400/20 px-2.5 py-1 text-xs font-bold text-amber-300 hover:bg-amber-400/30 transition-colors"
            aria-label="Mode Acheteur"
          >
            <Store className="size-3.5" />
            <span>Acheteur</span>
          </Link>
          <Link to="/groupeur/profil" aria-label="Mon compte OAG">
            <Avatar nom={utilisateur?.nom_complet ?? "?"} taille={28} />
          </Link>
        </div>
      </div>
    </header>
  );
}

export function BarreOnglets() {
  const { connecte } = useSession();
  const emplacement = useLocation();
  const [nbCommandes, setNbCommandes] = useState(0);
  const [ajoutRecent, setAjoutRecent] = useState(false);
  const [clePulse, setClePulse] = useState(0);

  const compterCommandes = useCallback(async () => {
    if (!connecte) {
      setNbCommandes(0);
      return;
    }
    try {
      const page = await api.get<Page<Participation>>("/participations/?page_size=100");
      const actives = page.results.filter(
        (part) => part.statut !== "en_attente_paiement" && part.statut !== "annulee",
      ).length;
      setNbCommandes(actives);
    } catch {
      // Garde la valeur actuelle en cas d'erreur réseau passagère
    }
  }, [connecte]);

  useEffect(() => {
    void compterCommandes();
  }, [compterCommandes, emplacement.pathname]);

  useEffect(() => {
    let minuterie: ReturnType<typeof setTimeout> | undefined;
    const surNouvelleCommande = () => {
      setNbCommandes((actuel) => actuel + 1);
      setClePulse((actuel) => actuel + 1);
      setAjoutRecent(true);
      void compterCommandes();
      if (minuterie) clearTimeout(minuterie);
      minuterie = setTimeout(() => setAjoutRecent(false), 5500);
    };
    window.addEventListener(EVENEMENT_NOUVELLE_COMMANDE, surNouvelleCommande);
    return () => {
      window.removeEventListener(EVENEMENT_NOUVELLE_COMMANDE, surNouvelleCommande);
      if (minuterie) clearTimeout(minuterie);
    };
  }, [compterCommandes]);

  return (
    <nav
      className="fixed bottom-0 left-1/2 -translate-x-1/2 z-40 w-full max-w-md border-t border-slate-200/80 bg-white/95 backdrop-blur-md shadow-[0_-4px_16px_rgba(0,0,0,0.06)]"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <ul className="flex h-[var(--hauteur-onglets)] w-full items-center">
        {ONGLETS.map((onglet) => {
          const estCommandes = onglet.vers === "/mes-achats";
          return (
            <li key={onglet.vers} className="flex-1">
              <NavLink
                to={onglet.vers}
                end={onglet.exact}
                className={({ isActive }) =>
                  fusionner(
                    "relative flex flex-col items-center justify-center gap-0.5 py-1 text-[0.65rem] font-bold transition-colors",
                    isActive
                      ? "text-[color:var(--color-accent,#ff6a00)]"
                      : "texte-doux hover:text-slate-800",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <motion.span
                        layoutId="curseur-onglets"
                        className="absolute -top-px h-0.5 w-7 rounded-full bg-[color:var(--color-accent,#ff6a00)]"
                        transition={{ type: "spring", stiffness: 420, damping: 34 }}
                      />
                    )}

                    {/* Bulle flottante "+1" lors d'une nouvelle commande */}
                    <AnimatePresence>
                      {estCommandes && ajoutRecent && (
                        <motion.span
                          key={`plus-un-${clePulse}`}
                          initial={{ opacity: 0, y: 8, scale: 0.6 }}
                          animate={{ opacity: 1, y: -18, scale: 1 }}
                          exit={{ opacity: 0, y: -26, scale: 0.8 }}
                          transition={{ type: "spring", stiffness: 380, damping: 22 }}
                          className="pointer-events-none absolute -top-1 rounded-full bg-emerald-600 px-1.5 py-0.5 text-[0.6rem] font-black text-white shadow-md"
                        >
                          +1
                        </motion.span>
                      )}
                    </AnimatePresence>

                    <span className="relative inline-flex items-center justify-center">
                      <motion.span
                        key={estCommandes ? clePulse : 0}
                        animate={
                          estCommandes && ajoutRecent
                            ? { scale: [1, 1.28, 0.95, 1.1, 1] }
                            : { scale: 1 }
                        }
                        transition={{ duration: 0.55 }}
                      >
                        <onglet.icone
                          className="size-5"
                          strokeWidth={isActive ? 2.5 : 1.8}
                        />
                      </motion.span>

                      {/* Badge d'incrémentation du nombre de commandes */}
                      <AnimatePresence>
                        {estCommandes && nbCommandes > 0 && (
                          <motion.span
                            key={`badge-${nbCommandes}`}
                            initial={{ scale: 0 }}
                            animate={{ scale: [1.35, 1] }}
                            exit={{ scale: 0 }}
                            transition={{ type: "spring", stiffness: 440, damping: 20 }}
                            className={fusionner(
                              "tabulaire absolute -right-2.5 -top-1.5 grid min-w-[1.1rem] place-items-center rounded-full px-1 text-[0.6rem] font-extrabold text-white ring-2 ring-white shadow-xs",
                              ajoutRecent
                                ? "bg-emerald-600"
                                : "bg-[color:var(--color-accent,#ff6a00)]",
                            )}
                          >
                            {nbCommandes > 99 ? "99+" : nbCommandes}
                          </motion.span>
                        )}
                      </AnimatePresence>
                    </span>

                    <span>{onglet.libelle}</span>
                  </>
                )}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/**
 * Bannière de notification flottante affichée instantanément en haut du cadre mobile
 * lorsqu'une commande est passée et consignée (visible même au-dessus de la feuille modale).
 */
export function NotificationCommandeToast() {
  const naviguer = useNavigate();
  const [commande, setCommande] = useState<Participation | null>(null);

  useEffect(() => {
    let minuterie: ReturnType<typeof setTimeout> | undefined;
    const surNouvelleCommande = (evenement: Event) => {
      const detail = (evenement as CustomEvent<Participation>).detail;
      if (!detail) return;
      setCommande(detail);
      if (minuterie) clearTimeout(minuterie);
      minuterie = setTimeout(() => setCommande(null), 6500);
    };
    window.addEventListener(EVENEMENT_NOUVELLE_COMMANDE, surNouvelleCommande);
    return () => {
      window.removeEventListener(EVENEMENT_NOUVELLE_COMMANDE, surNouvelleCommande);
      if (minuterie) clearTimeout(minuterie);
    };
  }, []);

  if (typeof document === "undefined") return null;

  return createPortal(
    <AnimatePresence>
      {commande && (
        <motion.div
          key={commande.id}
          initial={{ opacity: 0, y: -32, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -24, scale: 0.96 }}
          transition={{ type: "spring", stiffness: 380, damping: 28 }}
          role="status"
          aria-live="polite"
          className="fixed top-3 left-1/2 -translate-x-1/2 z-[60] w-[calc(100%-1.5rem)] max-w-[26rem] rounded-2xl border border-emerald-200 bg-white/98 p-3.5 shadow-2xl shadow-slate-900/20 backdrop-blur-md"
        >
          <div className="flex items-start gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-emerald-500 text-white shadow-sm shadow-emerald-500/30">
              <BellRing className="size-5" />
            </span>

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5 flex-wrap">
                <p className="text-xs font-black text-slate-900 flex items-center gap-1">
                  <CheckCircle2 className="size-3.5 text-emerald-600 shrink-0" />
                  Commande confirmée !
                </p>
                <span className="rounded-full bg-orange-100 px-2 py-0.5 text-[10px] font-extrabold text-[color:var(--color-accent,#ff6a00)]">
                  Commandes +1
                </span>
              </div>

              <p className="mt-0.5 truncate text-xs font-semibold text-slate-700">
                {commande.campagne.titre}
              </p>
              <p className="tabulaire text-[11px] font-bold text-emerald-700">
                {commande.quantite} pièce{commande.quantite > 1 ? "s" : ""} ·{" "}
                {francs(commande.montant_total)} consignés
              </p>

              <div className="mt-2 flex items-center gap-2">
                <button
                  onClick={() => {
                    const cible = `/mes-achats/${commande.id}`;
                    setCommande(null);
                    naviguer(cible);
                  }}
                  className="degrade-accent rounded-full px-3 py-1 text-[11px] font-bold text-white shadow-xs transition-transform active:scale-95"
                >
                  Voir ma commande
                </button>
                <button
                  onClick={() => {
                    setCommande(null);
                    naviguer("/mes-achats");
                  }}
                  className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-200"
                >
                  Mes commandes
                </button>
              </div>
            </div>

            <button
              onClick={() => setCommande(null)}
              className="grid size-7 shrink-0 place-items-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              aria-label="Fermer la notification"
            >
              <X className="size-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  );
}

/** Remonte en haut à chaque changement de page. */
export function RetourEnHaut() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [pathname]);
  return null;
}
