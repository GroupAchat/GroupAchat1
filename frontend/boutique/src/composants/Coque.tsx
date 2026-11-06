import { motion } from "framer-motion";
import {
  Compass,
  Clapperboard,
  MessageSquare,
  Search,
  ShoppingBag,
  Store,
  User,
} from "lucide-react";
import { useEffect } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";

import { Cloche } from "@/composants/Cloche";
import { Marque } from "@commun/composants/Marque";
import { Avatar, fusionner } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";

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
  return (
    <nav
      className="fixed bottom-0 left-1/2 -translate-x-1/2 z-40 w-full max-w-md border-t border-slate-200/80 bg-white/95 backdrop-blur-md shadow-[0_-4px_16px_rgba(0,0,0,0.06)]"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <ul className="flex h-[var(--hauteur-onglets)] w-full items-center">
        {ONGLETS.map((onglet) => (
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
                  <onglet.icone
                    className="size-5"
                    strokeWidth={isActive ? 2.5 : 1.8}
                  />
                  <span>{onglet.libelle}</span>
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
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
