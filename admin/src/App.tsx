import { motion } from "framer-motion";
import {
  Banknote,
  FileCheck2,
  LayoutDashboard,
  LogOut,
  MessageSquareWarning,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";
import {
  BrowserRouter,
  NavLink,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import type { Utilisateur } from "@commun/api/types";
import { Marque } from "@commun/composants/Marque";
import { Alerte, Avatar, Bouton, Carte, Champ, fusionner } from "@commun/composants/ui";
import { FournisseurSession, useSession } from "@commun/contexte/Session";
import Decaissements, { Moderation } from "@/pages/Decaissements";
import Dossiers from "@/pages/Dossiers";
import TableauAdmin from "@/pages/TableauAdmin";
import { api, useAction } from "@commun/outils/requetes";

/**
 * La console d'administration, sur son propre port et sa propre page.
 *
 * Elle vit à part de la boutique pour que la frontière soit réelle, et non
 * une affaire de route. Ce n'est pas pour autant la sécurité : c'est l'API
 * qui garde ses routes derrière `EstAdministrateur`.
 */

const ENTREES = [
  { vers: "/", libelle: "Supervision", icone: LayoutDashboard, exact: true },
  { vers: "/dossiers", libelle: "Dossiers KYC", icone: FileCheck2 },
  { vers: "/decaissements", libelle: "Décaissements", icone: Banknote },
  { vers: "/moderation", libelle: "Modération", icone: MessageSquareWarning },
];

function Barre() {
  const { utilisateur, deconnecter } = useSession();
  return (
    <aside className="surface sticky top-0 z-30 flex h-16 items-center gap-2 border-b px-4 lg:h-dvh lg:w-64 lg:flex-col lg:items-stretch lg:border-b-0 lg:border-r lg:px-4 lg:py-6">
      <div className="flex items-center gap-2 lg:mb-8 lg:flex-col lg:items-start">
        <Marque taille="compacte" />
        <p className="texte-doux text-xs font-semibold uppercase tracking-wide">
          Administration
        </p>
      </div>

      <nav className="sans-barre flex flex-1 gap-1 overflow-x-auto lg:flex-col lg:overflow-visible">
        {ENTREES.map((entree) => (
          <NavLink
            key={entree.vers}
            to={entree.vers}
            end={entree.exact}
            className={({ isActive }) =>
              fusionner(
                "flex shrink-0 items-center gap-2 rounded-2xl px-3.5 py-2.5 text-sm font-semibold transition-colors",
                isActive
                  ? "degrade-accent text-white"
                  : "texte-doux hover:surface-douce",
              )
            }
          >
            <entree.icone className="size-4" />
            <span className="whitespace-nowrap">{entree.libelle}</span>
          </NavLink>
        ))}
      </nav>

      <div className="flex items-center gap-2 lg:mt-auto lg:flex-col lg:items-stretch">
        <div className="hidden items-center gap-2 rounded-2xl p-2 lg:flex">
          <Avatar nom={utilisateur?.nom_complet ?? "?"} taille={34} />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">{utilisateur?.prenom}</p>
            <p className="texte-doux text-xs">Équipe</p>
          </div>
        </div>
        <button
          onClick={() => void deconnecter()}
          className="texte-doux grid size-10 place-items-center rounded-2xl transition-colors hover:surface-douce lg:flex lg:size-auto lg:justify-start lg:gap-2 lg:px-3.5 lg:py-2.5 lg:text-sm lg:font-semibold"
          aria-label="Se déconnecter"
        >
          <LogOut className="size-4" />
          <span className="hidden lg:inline">Déconnexion</span>
        </button>
      </div>
    </aside>
  );
}

function Pages() {
  const emplacement = useLocation();
  return (
    <motion.main
      key={emplacement.pathname}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22 }}
      className="mx-auto w-full max-w-[86rem] flex-1 px-4 py-6 lg:px-8 lg:py-9"
    >
      <Routes location={emplacement}>
        <Route path="/" element={<TableauAdmin />} />
        <Route path="/dossiers" element={<Dossiers />} />
        <Route path="/decaissements" element={<Decaissements />} />
        <Route path="/moderation" element={<Moderation />} />
        <Route
          path="*"
          element={<p className="texte-doux py-20 text-center">Page inconnue.</p>}
        />
      </Routes>
    </motion.main>
  );
}

function ConnexionAdmin() {
  const { definir } = useSession();
  const [telephone, setTelephone] = useState("");
  const [motDePasse, setMotDePasse] = useState("");

  const connexion = useAction(async () => {
    const reponse = await api.post<{ utilisateur: Utilisateur }>(
      "/comptes/connexion/",
      { telephone, mot_de_passe: motDePasse },
    );
    if (!reponse.utilisateur.est_equipe) {
      throw Object.assign(new Error("Ce compte n'appartient pas à l'équipe."), {
        statut: 403,
        champs: {},
        pourChamp: () => undefined,
      });
    }
    definir(reponse.utilisateur);
    return reponse;
  });

  return (
    <div className="mx-auto flex min-h-dvh max-w-md items-center px-5">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full"
      >
        <Carte className="space-y-5">
          <div className="space-y-2">
            <span className="grid size-12 place-items-center rounded-2xl bg-[color:var(--color-marine-800)] text-white">
              <ShieldCheck className="size-6" />
            </span>
            <h1 className="text-xl font-extrabold">Console d'administration</h1>
            <p className="texte-doux text-sm">
              Accès réservé à l'équipe Group Achat.
            </p>
          </div>

          <form
            onSubmit={(evenement) => {
              evenement.preventDefault();
              void connexion.lancer(undefined as never);
            }}
            className="space-y-4"
          >
            <Champ
              etiquette="Numéro de téléphone"
              type="tel"
              prefixe="+228"
              required
              value={telephone}
              onChange={(e) => setTelephone(e.target.value)}
            />
            <Champ
              etiquette="Mot de passe"
              type="password"
              required
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
            />
            <Alerte>{connexion.erreur?.message}</Alerte>
            <Bouton type="submit" pleineLargeur taille="lg" chargement={connexion.envoi}>
              Entrer
            </Bouton>
          </form>
        </Carte>
      </motion.div>
    </div>
  );
}

function Coque() {
  const { utilisateur, chargement } = useSession();

  // La teinte de l'administration est le bleu, comme l'espace groupeur : on
  // la pose ici plutôt que d'attendre la session, pour que l'écran de
  // connexion lui-même soit déjà dans le bon univers.
  document.documentElement.dataset.profil = "administrateur";

  if (chargement) {
    return (
      <div className="grid min-h-dvh place-items-center">
        <span className="squelette size-12 rounded-full" />
      </div>
    );
  }

  if (!utilisateur?.est_equipe) return <ConnexionAdmin />;

  return (
    <BrowserRouter>
      <div className="flex min-h-dvh flex-col lg:flex-row">
        <Barre />
        <Pages />
      </div>
    </BrowserRouter>
  );
}

export default function Console() {
  return (
    <FournisseurSession>
      <Coque />
    </FournisseurSession>
  );
}
