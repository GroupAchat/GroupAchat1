import { motion } from "framer-motion";
import {
  BadgeCheck,
  ChevronRight,
  Clock3,
  LayoutDashboard,
  LogOut,
  MessagesSquare,
  Moon,
  ShieldAlert,
  ShieldCheck,
  Store,
  Sun,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import type { DossierKYC } from "@commun/api/types";
import {
  Alerte,
  Avatar,
  Bouton,
  Carte,
  Champ,
  Etiquette,
  fusionner,
} from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { dateLongue, telephoneLisible } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/** Le profil : identité, badge de confiance, réglages. */
export default function Profil() {
  const { utilisateur, deconnecter, connecte } = useSession();
  const naviguer = useNavigate();
  const [theme, setTheme] = useState<"clair" | "sombre" | "auto">("auto");

  useEffect(() => {
    const enregistre = localStorage.getItem("ga-theme");
    if (enregistre === "clair" || enregistre === "sombre") setTheme(enregistre);
  }, []);

  const changerTheme = (valeur: "clair" | "sombre" | "auto") => {
    setTheme(valeur);
    const racine = document.documentElement;
    if (valeur === "auto") {
      delete racine.dataset.theme;
      localStorage.removeItem("ga-theme");
    } else {
      racine.dataset.theme = valeur === "clair" ? "light" : "dark";
      localStorage.setItem("ga-theme", valeur);
    }
  };

  if (!connecte || !utilisateur) {
    return (
      <div className="mx-auto max-w-md space-y-4 px-4 py-16 text-center">
        <Avatar nom="?" taille={64} className="mx-auto" />
        <h1 className="text-xl font-bold">Vous n'êtes pas connecté</h1>
        <p className="texte-doux text-sm">
          Connectez-vous pour suivre vos commandes et retrouver vos codes de retrait.
        </p>
        <div className="flex flex-col gap-2 pt-2">
          <Link to="/connexion">
            <Bouton pleineLargeur taille="lg">
              Se connecter
            </Bouton>
          </Link>
          <Link to="/inscription">
            <Bouton ton="contour" pleineLargeur>
              Créer un compte
            </Bouton>
          </Link>
        </div>
      </div>
    );
  }

  return (
    // Sur grand écran, la page passe en deux colonnes : la carte d'identité
    // et l'espace groupeur à gauche, les réglages à droite. En une seule
    // colonne étroite, cette page laissait les deux tiers de l'écran vides.
    <div className="mx-auto w-full max-w-5xl px-4 py-6 lg:px-8 lg:py-10">
      <motion.header
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-[var(--radius-carte)] p-6 text-white lg:p-8"
      >
        <div className="degrade-accent absolute inset-0" />
        <span className="absolute -right-10 -top-16 size-56 rounded-full bg-white/15 blur-3xl" />
        <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center">
          <Avatar
            nom={utilisateur.nom_complet}
            taille={68}
            className="shrink-0 ring-4 ring-white/30"
          />
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-xl font-extrabold lg:text-2xl">
              {utilisateur.nom_complet}
            </h1>
            <p className="tabulaire text-sm text-white/85">
              {telephoneLisible(utilisateur.telephone)}
              {utilisateur.email && ` · ${utilisateur.email}`}
            </p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {utilisateur.telephone_verifie && (
                <span className="verre-sombre flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold">
                  <ShieldCheck className="size-3" />
                  Numéro vérifié
                </span>
              )}
              {utilisateur.est_groupeur_valide && (
                <span className="verre-sombre flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold">
                  <BadgeCheck className="size-3" />
                  Groupeur de confiance
                </span>
              )}
            </div>
          </div>
          <p className="texte-doux hidden shrink-0 text-right text-xs text-white/70 lg:block">
            Membre depuis
            <br />
            <strong className="text-sm text-white/90">
              {dateLongue(utilisateur.date_inscription).split(" à ")[0]}
            </strong>
          </p>
        </div>
      </motion.header>

      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_20rem] lg:items-start">
        <div className="space-y-5">
          <EspaceGroupeur />

          <Carte className="space-y-1 !p-2">
            <LienProfil vers="/mes-achats" icone={Store} libelle="Mes achats" />
            <LienProfil vers="/notifications" icone={Clock3} libelle="Notifications" />
            <LienProfil vers="/communaute" icone={MessagesSquare} libelle="Mes demandes" />
          </Carte>
        </div>

        <div className="space-y-5">
          <Carte className="space-y-3">
            <p className="text-sm font-semibold">Apparence</p>
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  { cle: "clair", libelle: "Clair", icone: Sun },
                  { cle: "sombre", libelle: "Sombre", icone: Moon },
                  { cle: "auto", libelle: "Système", icone: LayoutDashboard },
                ] as const
              ).map((option) => (
                <button
                  key={option.cle}
                  onClick={() => changerTheme(option.cle)}
                  className={fusionner(
                    "flex flex-col items-center gap-1 rounded-2xl border p-3 text-xs font-semibold transition-all",
                    theme === option.cle
                      ? "border-[color:var(--color-accent)] bg-accent-doux text-[color:var(--color-accent-fort)]"
                      : "surface",
                  )}
                >
                  <option.icone className="size-4" />
                  {option.libelle}
                </button>
              ))}
            </div>
          </Carte>

          <Bouton
            ton="contour"
            pleineLargeur
            icone={<LogOut className="size-4" />}
            onClick={async () => {
              await deconnecter();
              naviguer("/");
            }}
          >
            Se déconnecter
          </Bouton>
        </div>
      </div>
    </div>
  );
}

function LienProfil({
  vers,
  icone: Icone,
  libelle,
}: {
  vers: string;
  icone: typeof Store;
  libelle: string;
}) {
  return (
    <Link
      to={vers}
      className="flex items-center gap-3 rounded-2xl p-3 transition-colors hover:surface-douce"
    >
      <span className="grid size-9 place-items-center rounded-xl bg-accent-doux text-[color:var(--color-accent)]">
        <Icone className="size-4" />
      </span>
      <span className="flex-1 font-medium">{libelle}</span>
      <ChevronRight className="texte-doux size-4" />
    </Link>
  );
}

/** La carte qui mène à l'espace groupeur, ou dit pourquoi il est fermé. */
function EspaceGroupeur() {
  const { utilisateur } = useSession();
  if (!utilisateur) return null;

  if (utilisateur.est_groupeur_valide) {
    return (
      <Link to="/groupeur">
        <Carte
          survol
          className="flex items-center gap-4 border-[color:var(--color-marine-800)]/30 bg-[color:var(--color-marine-50)] dark:bg-[color:var(--color-marine-950)]/40"
        >
          <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-[color:var(--color-marine-800)] text-white">
            <LayoutDashboard className="size-5" />
          </span>
          <div className="flex-1">
            <p className="font-bold">Espace groupeur</p>
            <p className="texte-doux text-sm">
              Vos campagnes, vos paiements, vos décaissements.
            </p>
          </div>
          <ChevronRight className="texte-doux size-4" />
        </Carte>
      </Link>
    );
  }

  if (utilisateur.statut_kyc === "en_attente") {
    return (
      <Carte className="flex items-start gap-4 border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40">
        <Clock3 className="size-5 shrink-0 text-amber-600" />
        <div>
          <p className="font-bold text-amber-900 dark:text-amber-200">
            Dossier en cours de vérification
          </p>
          <p className="text-sm text-amber-800 dark:text-amber-300">
            L'équipe examine vos pièces. L'espace groupeur s'ouvrira dès la
            validation — vous recevrez une notification.
          </p>
        </div>
      </Carte>
    );
  }

  return (
    <Link to="/profil/devenir-groupeur">
      <Carte survol className="flex items-center gap-4">
        <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-[color:var(--color-marine-800)] text-white">
          <Store className="size-5" />
        </span>
        <div className="flex-1">
          <p className="font-bold">
            {utilisateur.statut_kyc === "rejete"
              ? "Corriger mon dossier"
              : "Devenir groupeur"}
          </p>
          <p className="texte-doux text-sm">
            Lancez vos propres campagnes. Gratuit, 1 500 FCFA par décaissement.
          </p>
        </div>
        <ChevronRight className="texte-doux size-4" />
      </Carte>
    </Link>
  );
}

// ── Dépôt du dossier de confiance ──────────────────────────────────────────

export function DevenirGroupeur() {
  const naviguer = useNavigate();
  const { rafraichir, utilisateur } = useSession();
  const { donnees: dossier } = useRequete<DossierKYC>(
    utilisateur?.statut_kyc ? "/comptes/dossier/" : null,
  );
  const [saisie, setSaisie] = useState({
    type_piece: "cni",
    numero_piece: "",
    numero_mobile_money: "",
    nom_commerce: "",
  });

  useEffect(() => {
    if (dossier) {
      setSaisie({
        type_piece: dossier.type_piece,
        numero_piece: dossier.numero_piece,
        numero_mobile_money: dossier.numero_mobile_money,
        nom_commerce: dossier.nom_commerce,
      });
    }
  }, [dossier]);

  const depot = useAction(async () => {
    await api.post("/comptes/dossier/", saisie);
    await rafraichir();
    naviguer("/profil");
  });

  return (
    <div className="mx-auto w-full max-w-xl space-y-5 px-4 py-6 lg:py-10">
      <header className="space-y-2">
        <span className="grid size-12 place-items-center rounded-2xl bg-[color:var(--color-marine-800)] text-white">
          <Store className="size-5" />
        </span>
        <h1 className="text-2xl font-extrabold">Devenir groupeur</h1>
        <p className="texte-doux text-sm">
          Vos pièces servent à obtenir le badge de confiance que verront vos
          acheteurs. L'équipe les vérifie avant d'ouvrir votre espace.
        </p>
      </header>

      {dossier?.statut === "rejete" && dossier.motif_rejet && (
        <Carte className="flex items-start gap-3 border-red-300 bg-red-50 dark:border-red-900 dark:bg-red-950/40">
          <ShieldAlert className="size-5 shrink-0 text-red-600" />
          <div className="text-sm">
            <p className="font-bold text-red-900 dark:text-red-200">Dossier à corriger</p>
            <p className="text-red-800 dark:text-red-300">{dossier.motif_rejet}</p>
            <p className="texte-doux mt-1 text-xs">
              Examiné le {dossier.decide_le ? dateLongue(dossier.decide_le) : "—"}
            </p>
          </div>
        </Carte>
      )}

      <form
        onSubmit={(evenement) => {
          evenement.preventDefault();
          void depot.lancer(undefined as never);
        }}
        className="space-y-4"
      >
        <div className="space-y-1.5">
          <label className="block text-sm font-medium">Pièce d'identité</label>
          <select
            value={saisie.type_piece}
            onChange={(e) => setSaisie({ ...saisie, type_piece: e.target.value })}
            className="surface h-12 w-full rounded-2xl px-4 text-[0.95rem] outline-none focus:border-[color:var(--color-accent)]"
          >
            <option value="cni">Carte nationale d'identité</option>
            <option value="passeport">Passeport</option>
            <option value="carte_consulaire">Carte consulaire</option>
          </select>
        </div>

        <Champ
          etiquette="Numéro de la pièce"
          required
          value={saisie.numero_piece}
          onChange={(e) => setSaisie({ ...saisie, numero_piece: e.target.value })}
          erreur={depot.erreur?.pourChamp("numero_piece")}
        />

        <Champ
          etiquette="Numéro Mobile Money"
          type="tel"
          inputMode="tel"
          prefixe="+228"
          placeholder="90 00 11 22"
          required
          value={saisie.numero_mobile_money}
          onChange={(e) => setSaisie({ ...saisie, numero_mobile_money: e.target.value })}
          erreur={depot.erreur?.pourChamp("numero_mobile_money")}
          aide="C'est sur ce numéro que vous recevrez les fonds de vos campagnes."
        />

        <Champ
          etiquette="Nom de votre commerce (facultatif)"
          placeholder="Abalo Import"
          value={saisie.nom_commerce}
          onChange={(e) => setSaisie({ ...saisie, nom_commerce: e.target.value })}
          aide="C'est ce nom que verront les acheteurs sur vos campagnes."
        />

        <div className="surface-douce rounded-2xl p-4 text-sm">
          <p className="mb-1 font-semibold">Ce qui vous attend</p>
          <ul className="texte-doux space-y-1">
            <li>• Création de campagnes libre, sourcing libre.</li>
            <li>• Suivi nominatif des paiements en temps réel.</li>
            <li>• Retrait de 100 % de la collecte, moins 1 500 FCFA fixes.</li>
            <li>• Protection contre les faux litiges grâce aux codes de retrait.</li>
          </ul>
        </div>

        <Alerte>{depot.erreur?.message}</Alerte>

        <Bouton type="submit" pleineLargeur taille="lg" chargement={depot.envoi}>
          Déposer mon dossier
        </Bouton>
        <p className="texte-doux text-center text-xs">
          <Etiquette>Démonstration</Etiquette> Les pièces justificatives ne sont
          pas téléversées dans cette version.
        </p>
      </form>
    </div>
  );
}
