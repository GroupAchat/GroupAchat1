import { motion } from "framer-motion";
import { Clock3, FileCheck2, Hourglass, ShieldAlert, Store } from "lucide-react";
import { Link, Outlet } from "react-router-dom";

import type { EtatGroupeur } from "@commun/api/types";
import { Bouton, Carte, Squelette } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { dateLongue } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

/**
 * La porte de l'espace groupeur.
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

  return <Outlet />;
}

function PorteFermee({ etat }: { etat: EtatGroupeur }) {
  const contenus: Record<
    EtatGroupeur["raison"],
    { icone: typeof Store; titre: string; texte: string; action: React.ReactNode }
  > = {
    non_connecte: {
      icone: Store,
      titre: "Connectez-vous",
      texte: "L'espace groupeur est réservé aux comptes vérifiés.",
      action: (
        <Link to="/connexion">
          <Bouton taille="lg">Se connecter</Bouton>
        </Link>
      ),
    },
    aucun_dossier: {
      icone: Store,
      titre: "Devenez groupeur",
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
