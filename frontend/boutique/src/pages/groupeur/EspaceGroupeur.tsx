import { motion } from "framer-motion";
import {
  BarChart3,
  Clock3,
  FileCheck2,
  Hourglass,
  LayoutDashboard,
  Plus,
  ShieldAlert,
  Store,
  UserCog,
  Wallet,
} from "lucide-react";
import {
  Link,
  NavLink,
  Outlet,
  useLocation,
} from "react-router-dom";

import type { Conversation, EtatGroupeur } from "@commun/api/types";
import { Bouton, Carte, Squelette } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { dateLongue } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

/**
 * Ce que contient l'espace de gestion. **Une seule liste** pour la barre
 * laterale et les onglets du bas : deux listes finissent par diverger, et
 * c'est l'entree la plus recente qui manque dans l'une des deux.
 */
const LIENS_GESTION = [
  { vers: "/groupeur", libelle: "Tableau de bord", icone: LayoutDashboard,
    court: "Bord", exact: true },
  { vers: "/groupeur/campagnes", libelle: "Mes offres", icone: BarChart3,
    court: "Offres" },
  { vers: "/groupeur/campagnes/nouvelle", libelle: "Nouvelle offre",
    icone: Plus, court: "Publier" },
  { vers: "/groupeur/portefeuille", libelle: "Mon portefeuille",
    icone: Wallet, court: "Portefeuille" },
  { vers: "/groupeur/profil", libelle: "Mon compte", icone: UserCog,
    court: "Compte" },
];

// Les onglets reprennent les memes destinations sous un libelle court : sur
// 360 pixels, « Nouvelle campagne » ne tient pas sous une icone.
const ONGLETS_OAG = LIENS_GESTION.map((lien) => ({
  ...lien,
  libelle: lien.court,
}));

/**
 * La porte de l'espace OAG.
 *
 * Décision du cahier des charges : **tant que le dossier n'est pas validé,
 * l'espace n'est pas accessible** — pas seulement la publication. Ce qui
 * s'affiche alors n'est pas un refus sec mais l'état du dossier : la personne
 * doit savoir si elle attend ou si elle doit corriger quelque chose.
 */
export default function EspaceGroupeur() {
  const { utilisateur, chargement } = useSession();
  const { donnees: etat, chargement: chargementEtat } = useRequete<EtatGroupeur>(
    "/groupeur/etat/",
  );
  // Le compte de non-lus est lu **ici**, une seule fois : la barre laterale
  // et les onglets du bas sont montes tous les deux, et deux appels pour le
  // meme chiffre doubleraient la requete a chaque page.
  const { donnees: fils } = useRequete<Conversation[]>(
    utilisateur?.est_groupeur_valide ? "/conversations/" : null,
  );
  const nonLus = (fils ?? []).reduce((total, fil) => total + fil.non_lus, 0);
  const estMessagerie = useLocation().pathname.startsWith("/groupeur/messages");

  if (chargement || chargementEtat) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 px-4 py-8">
        <Squelette className="h-10 w-56" />
        <Squelette className="h-32" />
      </div>
    );
  }

  if (!utilisateur) return <PorteFermee etat={{ acces: false, raison: "non_connecte" }} />;
  if (!utilisateur.est_groupeur_valide) {
    return <PorteFermee etat={etat ?? { acces: false, raison: "aucun_dossier" }} />;
  }

  return (
    <>
      <div className="w-full flex-1 flex flex-col">
        <main
          className={
            estMessagerie
              ? "w-full flex-1"
              : "w-full flex-1 pb-24"
          }
        >
          <Outlet />
        </main>
      </div>
      <OngletsOag nonLus={nonLus} />
    </>
  );
}

/**
 * Les onglets du bas de l'espace OAG : 100% mobile responsive.
 */
function OngletsOag({ nonLus }: { nonLus: number }) {
  return (
    <nav
      className="fixed bottom-0 left-1/2 -translate-x-1/2 z-40 w-full max-w-md border-t border-slate-200/80 bg-white/95 backdrop-blur-md shadow-[0_-4px_16px_rgba(0,0,0,0.06)]"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <ul className="flex h-[var(--hauteur-onglets)] w-full items-center">
        {ONGLETS_OAG.map((onglet) => (
          <li key={onglet.vers} className="flex-1">
            <NavLink
              to={onglet.vers}
              end={onglet.exact}
              className={({ isActive }) =>
                `relative flex flex-col items-center justify-center gap-0.5 py-1 text-[0.65rem] font-bold transition-colors ${
                  isActive
                    ? "text-[color:var(--color-accent)]"
                    : "texte-doux hover:text-slate-800"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.span
                      layoutId="curseur-onglets-oag"
                      className="absolute -top-px h-0.5 w-7 rounded-full bg-[color:var(--color-accent)]"
                      transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    />
                  )}
                  <span className="relative">
                    <onglet.icone
                      className="size-5"
                      strokeWidth={isActive ? 2.4 : 1.8}
                    />
                    {onglet.vers.endsWith("/messages") && nonLus > 0 && (
                      <span className="absolute -right-1.5 -top-1 grid size-4 place-items-center rounded-full bg-[color:var(--color-accent)] text-[0.55rem] font-bold text-white">
                        {nonLus > 9 ? "9+" : nonLus}
                      </span>
                    )}
                  </span>
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



function PorteFermee({ etat }: { etat: EtatGroupeur }) {
  const contenus: Record<
    EtatGroupeur["raison"],
    { icone: typeof Store; titre: string; texte: string; action: React.ReactNode }
  > = {
    non_connecte: {
      icone: Store,
      titre: "Connectez-vous",
      texte: "L'espace OAG est réservé aux comptes vérifiés.",
      action: (
        <Link to="/connexion">
          <Bouton taille="lg">Se connecter</Bouton>
        </Link>
      ),
    },
    aucun_dossier: {
      icone: Store,
      titre: "Devenez OAG",
      texte:
        "Déposez vos pièces pour obtenir votre badge de confiance. L'équipe les vérifie, puis votre espace s'ouvre.",
      action: (
        <Link to="/profil/devenir-groupeur">
          <Bouton taille="lg">Déposer mon dossier</Bouton>
        </Link>
      ),
    },
    en_attente: {
      icone: Hourglass,
      titre: "Dossier en cours de vérification",
      texte:
        "Vos pièces sont entre les mains de l'équipe. Vous recevrez une notification dès la décision — en général sous 48 heures.",
      action: (
        <Link to="/">
          <Bouton ton="contour" taille="lg">
            Retour à la boutique
          </Bouton>
        </Link>
      ),
    },
    rejete: {
      icone: ShieldAlert,
      titre: "Dossier à corriger",
      texte:
        etat.motif_rejet ||
        "Votre dossier n'a pas pu être validé. Corrigez-le et redéposez-le.",
      action: (
        <Link to="/profil/devenir-groupeur">
          <Bouton taille="lg">Corriger mon dossier</Bouton>
        </Link>
      ),
    },
    valide: {
      icone: FileCheck2,
      titre: "Dossier validé",
      texte: "Reconnectez-vous pour accéder à votre espace.",
      action: (
        <Link to="/profil">
          <Bouton taille="lg">Mon profil</Bouton>
        </Link>
      ),
    },
  };

  const contenu = contenus[etat.raison];

  return (
    <div className="mx-auto flex min-h-[calc(100dvh-10rem)] max-w-lg items-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="w-full"
      >
        <Carte className="space-y-5 text-center">
          <motion.span
            animate={
              etat.raison === "en_attente" ? { rotate: [0, 12, 0, -12, 0] } : undefined
            }
            transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
            className="mx-auto grid size-16 place-items-center rounded-3xl bg-[color:var(--color-marine-800)] text-white"
          >
            <contenu.icone className="size-7" />
          </motion.span>

          <div className="space-y-2">
            <h1 className="text-xl font-extrabold">{contenu.titre}</h1>
            <p className="texte-doux text-sm leading-relaxed">{contenu.texte}</p>
          </div>

          {etat.depose_le && (
            <p className="texte-doux surface-douce flex items-center justify-center gap-2 rounded-xl py-2 text-xs">
              <Clock3 className="size-3.5" />
              Déposé le {dateLongue(etat.depose_le)}
            </p>
          )}

          <div className="flex justify-center">{contenu.action}</div>
        </Carte>
      </motion.div>
    </div>
  );
}
