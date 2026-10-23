import { motion } from "framer-motion";
import {
  Compass,
  Home,
  LayoutDashboard,
  MessagesSquare,
  Search,
  ShoppingBag,
  User,
} from "lucide-react";
import { useEffect } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";

import { Cloche } from "@/composants/Cloche";
import { Marque } from "@/composants/Marque";
import { Avatar, fusionner } from "@/composants/ui";
import { useSession } from "@/contexte/Session";

/**
 * L'ossature de la boutique : barre du haut, onglets du bas.
 *
 * Les onglets du bas sont la navigation principale **sur téléphone**, où le
 * haut de l'écran est hors de portée du pouce. Sur grand écran ils cèdent la
 * place à une barre horizontale classique.
 */

const ONGLETS = [
  { vers: "/", libelle: "Accueil", icone: Home, exact: true },
  { vers: "/catalogue", libelle: "Catalogue", icone: Compass },
  { vers: "/communaute", libelle: "Demandes", icone: MessagesSquare },
  { vers: "/mes-achats", libelle: "Mes achats", icone: ShoppingBag },
  { vers: "/profil", libelle: "Profil", icone: User },
];

export function EnTete() {
  const { utilisateur, connecte } = useSession();
  const naviguer = useNavigate();
  return (
    <header className="verre sticky top-0 z-40 border-b">
      {/* La barre va chercher les bords de l'écran, au lieu de s'aligner
          sur la colonne de contenu : le logo se cale ainsi à gauche et les
          actions à droite, là où l'œil et le pouce les attendent. Un
          plafond très large évite seulement qu'ils s'éloignent à l'absurde
          sur un écran panoramique. */}
      <div className="mx-auto flex h-16 w-full max-w-[110rem] items-center gap-3 px-3 sm:px-6">
        <Link to="/" className="flex shrink-0 items-center" aria-label="Accueil">
          <Marque />
        </Link>

        <nav className="ml-4 hidden items-center gap-1 md:flex">
          {ONGLETS.slice(0, 3).map((onglet) => (
            <NavLink
              key={onglet.vers}
              to={onglet.vers}
              end={onglet.exact}
              className={({ isActive }) =>
                fusionner(
                  "rounded-full px-3.5 py-2 text-sm font-semibold transition-colors",
                  isActive
                    ? "bg-accent-doux text-[color:var(--color-accent-fort)]"
                    : "texte-doux hover:surface-douce",
                )
              }
            >
              {onglet.libelle}
            </NavLink>
          ))}
        </nav>

        <button
          onClick={() => naviguer("/catalogue?focus=1")}
          className="surface-douce ml-auto flex h-10 shrink-0 items-center gap-2 rounded-full px-4 text-sm transition-colors hover:brightness-97"
          aria-label="Rechercher"
        >
          <Search className="size-4" />
          <span className="texte-doux hidden sm:inline">Rechercher un produit…</span>
        </button>

        <Cloche />

        {utilisateur?.est_groupeur_valide && (
          <Link
            to="/groupeur"
            className="hidden items-center gap-1.5 rounded-full bg-[color:var(--color-marine-800)] px-3.5 py-2 text-sm font-semibold text-white transition-transform hover:scale-[1.03] sm:flex"
          >
            <LayoutDashboard className="size-4" />
            Espace groupeur
          </Link>
        )}

        {connecte ? (
          <Link to="/profil" className="shrink-0" aria-label="Mon profil">
            <Avatar nom={utilisateur?.nom_complet ?? "?"} taille={36} />
          </Link>
        ) : (
          <Link
            to="/connexion"
            className="degrade-accent shrink-0 rounded-full px-4 py-2 text-sm font-semibold text-white transition-transform hover:scale-[1.03]"
          >
            Connexion
          </Link>
        )}
      </div>
    </header>
  );
}

export function BarreOnglets() {
  const { utilisateur } = useSession();
  const onglets = utilisateur?.est_groupeur_valide
    ? [...ONGLETS.slice(0, 2),
       { vers: "/groupeur", libelle: "Groupeur", icone: LayoutDashboard },
       ...ONGLETS.slice(3)]
    : ONGLETS;

  return (
    <nav
      className="verre fixed inset-x-0 bottom-0 z-40 border-t md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <ul className="mx-auto flex max-w-lg">
        {onglets.map((onglet) => (
          <li key={onglet.vers} className="flex-1">
            <NavLink
              to={onglet.vers}
              end={onglet.exact}
              className={({ isActive }) =>
                fusionner(
                  "relative flex flex-col items-center gap-0.5 py-2.5 text-[0.62rem] font-semibold transition-colors",
                  isActive ? "text-[color:var(--color-accent)]" : "texte-doux",
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    // Le curseur glisse d'un onglet à l'autre plutôt que de
                    // sauter : c'est ce qui rend la navigation continue.
                    <motion.span
                      layoutId="curseur-onglets"
                      className="absolute -top-px h-0.5 w-8 rounded-full bg-[color:var(--color-accent)]"
                      transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    />
                  )}
                  <onglet.icone
                    className="size-[1.35rem]"
                    strokeWidth={isActive ? 2.4 : 1.8}
                  />
                  {onglet.libelle}
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
