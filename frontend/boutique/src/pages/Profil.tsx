import { motion } from "framer-motion";
import {
  BadgeCheck,
  ChevronRight,
  Clock3,
  LayoutDashboard,
  LogOut,
  MessageCircle,
  MessagesSquare,
  Rocket,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Store,
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
} from "@commun/composants/ui";
import { CarteParrainage } from "@/composants/Parrainage";
import { useSession } from "@commun/contexte/Session";
import { dateLongue, telephoneLisible } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/** Le profil : identité, badge de confiance, réglages. */
export default function Profil() {
  const { utilisateur, deconnecter, connecte } = useSession();
  const naviguer = useNavigate();

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
    // et l'espace OAG à gauche, les réglages à droite. En une seule
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
            {/* Le nom public est rappelé ici parce que c'est le seul que
                les autres voient : sans ce rappel, on croit être connu sous
                son nom civil, qui est juste au-dessus. */}
            <p className="text-sm text-white/85">
              Vu par les autres sous{" "}
              <strong className="font-bold">{utilisateur.nom_public}</strong>
            </p>
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
                  OAG de confiance
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

      <div className="mt-5 space-y-4">
        <div className="space-y-4">
          <EspaceGroupeur />

          {/* Programme de fidélité acheteur (Nouveau Cahier des Charges) */}
          <CarteFideliteAcheteur />

          <CarteParrainage />

          <Carte className="space-y-1 !p-2">
            <LienProfil vers="/mes-achats" icone={Store} libelle="Mes achats" />
            <LienProfil vers="/reclamations" icone={ShieldAlert} libelle="Mes réclamations (REC-2026)" />
            <LienProfil vers="/messages" icone={MessageCircle} libelle="Mes messages" />
            <LienProfil vers="/notifications" icone={Clock3} libelle="Notifications" />
            <LienProfil vers="/communaute" icone={MessagesSquare} libelle="Mes demandes" />
          </Carte>

          {/* Protection des données personnelles (IPDCP Togo - Loi n°2019-014) */}
          <div className="surface rounded-2xl border border-slate-200/80 p-3.5 text-xs">
            <p className="flex items-center gap-1.5 font-bold text-slate-800 dark:text-slate-200">
              <ShieldCheck className="size-4 text-emerald-600" />
              Protection IPDCP Togo (Loi n°2019-014)
            </p>
            <p className="texte-doux mt-1 leading-relaxed">
              Vos coordonnées téléphoniques et géographiques sont protégées et masquées aux organisateurs (OAG). Seul le livreur mandaté y accède pour la remise.
            </p>
          </div>
        </div>

        <div className="space-y-4">
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

/** La carte qui mène à l'espace OAG, ou dit pourquoi il est fermé. */
function EspaceGroupeur() {
  const { utilisateur } = useSession();
  if (!utilisateur) return null;

  if (utilisateur.est_groupeur_valide) {
    return (
      <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
        <Link to="/groupeur">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 p-4 text-white shadow-md">
            <span className="absolute -right-8 -top-8 size-28 rounded-full bg-blue-500/20 blur-xl" />
            <div className="relative flex items-center gap-3.5">
              <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-white/10 text-white backdrop-blur-xs">
                <LayoutDashboard className="size-6 text-amber-300" />
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-extrabold text-sm text-white">Espace OAG Certifié</p>
                  <span className="rounded-full bg-amber-400/20 px-2 py-0.2 text-[10px] font-bold text-amber-300 border border-amber-400/30">
                    Actif
                  </span>
                </div>
                <p className="text-xs text-white/80 truncate mt-0.5">
                  Gérer vos offres, acheteurs et portefeuille de commissions.
                </p>
              </div>
              <Bouton taille="sm" className="degrade-accent border-none text-white text-xs shrink-0 font-bold shadow-sm">
                Ouvrir
              </Bouton>
            </div>
          </div>
        </Link>
      </motion.div>
    );
  }

  if (utilisateur.statut_kyc === "en_attente") {
    return (
      <Carte className="flex items-start gap-4 border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40">
        <Clock3 className="size-5 shrink-0 text-amber-600 mt-0.5" />
        <div>
          <p className="font-bold text-amber-900 dark:text-amber-200">
            Dossier OAG en cours de vérification
          </p>
          <p className="text-xs text-amber-800 dark:text-amber-300 mt-1 leading-relaxed">
            Notre équipe juridique examine vos pièces d'identité et informations de commerce. Votre espace OAG sera débloqué sous 24h.
          </p>
        </div>
      </Carte>
    );
  }

  return (
    <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
      <Link to="/profil/devenir-groupeur">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 p-5 text-white shadow-lg">
          <span className="absolute -right-8 -top-8 size-32 rounded-full bg-white/20 blur-xl" />
          <span className="absolute -bottom-8 left-10 size-28 rounded-full bg-black/20 blur-xl" />

          <div className="relative space-y-3">
            <div className="flex items-center justify-between">
              <span className="verre-sombre flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-bold">
                <Rocket className="size-3 text-amber-200" />
                Opportunité Organisateur Togo
              </span>
              <span className="rounded-full bg-black/25 px-2 py-0.5 text-[10px] font-bold">
                Jusqu'à 4% de com.
              </span>
            </div>

            <div>
              <h2 className="text-base font-extrabold leading-snug">
                Devenir Organisateur d'Achats Groupés (OAG)
              </h2>
              <p className="text-xs text-white/90 mt-1 leading-relaxed">
                Lancez vos propres offres groupées, touchez des commissions garanties sur les fonds collectés et développez votre activité sans avance de trésorerie.
              </p>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <span className="flex-1 rounded-xl bg-black/20 backdrop-blur-xs py-1.5 px-2 text-center text-[10px] font-semibold">
                🛡️ Séquestre sécurisé
              </span>
              <span className="flex-1 rounded-xl bg-black/20 backdrop-blur-xs py-1.5 px-2 text-center text-[10px] font-semibold">
                🏛️ Prêts bancaires
              </span>
              <span className="flex-1 rounded-xl bg-black/20 backdrop-blur-xs py-1.5 px-2 text-center text-[10px] font-semibold">
                📦 Réseau La Poste
              </span>
            </div>

            <Bouton
              pleineLargeur
              className="mt-1 border-none bg-white text-orange-950 hover:bg-white font-extrabold text-xs py-2.5 shadow-md flex items-center justify-center gap-2"
            >
              <Store className="size-4 text-orange-600" />
              <span>Postuler comme OAG (Gratuit)</span>
              <ChevronRight className="size-4" />
            </Bouton>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

function CarteFideliteAcheteur() {
  const { utilisateur } = useSession();
  if (!utilisateur) return null;
  const pts = utilisateur.points?.cumules ?? 0;

  return (
    <Carte className="space-y-3.5 border-amber-200/70 bg-gradient-to-br from-amber-50/60 to-orange-50/30 dark:border-amber-900/40 dark:from-amber-950/20 dark:to-orange-950/10">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="grid size-10 place-items-center rounded-2xl bg-amber-500 text-white shadow-sm">
            <Sparkles className="size-5" />
          </span>
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300">
              Programme Fidélité Acheteur
            </p>
            <p className="text-lg font-extrabold">{pts} point{pts > 1 ? "s" : ""}</p>
          </div>
        </div>
        <span className="rounded-full bg-amber-500/15 px-2.5 py-1 text-[11px] font-bold text-amber-800 dark:text-amber-200">
          Group Achat Togo
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div className="surface rounded-xl p-2 shadow-xs">
          <p className="font-extrabold text-[color:var(--color-accent)]">+5 pts</p>
          <p className="texte-doux text-[10px]">Achat groupé</p>
        </div>
        <div className="surface rounded-xl p-2 shadow-xs">
          <p className="font-extrabold text-[color:var(--color-accent)]">+2 pts</p>
          <p className="texte-doux text-[10px]">Ami parrainé</p>
        </div>
        <div className="surface rounded-xl p-2 shadow-xs">
          <p className="font-extrabold text-[color:var(--color-accent)]">+10 pts</p>
          <p className="texte-doux text-[10px]">Contact Privé</p>
        </div>
      </div>

      <div className="space-y-1.5 border-t border-amber-200/50 pt-2.5 text-xs">
        <p className="font-semibold text-slate-800 dark:text-slate-200">Paliers & Avantages :</p>
        <div className="space-y-1 text-slate-600 dark:text-slate-300 text-[11px]">
          <div className="flex items-center justify-between">
            <span>50 pts · Badge Membre Actif</span>
            <span className={pts >= 50 ? "font-bold text-emerald-600" : "texte-doux"}>
              {pts >= 50 ? "✓ Débloqué" : "À 50 pts"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>100 pts · -50% sur 1 livraison</span>
            <span className={pts >= 100 ? "font-bold text-emerald-600" : "texte-doux"}>
              {pts >= 100 ? "✓ Débloqué" : "À 100 pts"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>200 pts · Avantages partenaires Lomé</span>
            <span className={pts >= 200 ? "font-bold text-emerald-600" : "texte-doux"}>
              {pts >= 200 ? "✓ Débloqué" : "À 200 pts"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>500 pts · Statut Acheteur Fidèle</span>
            <span className={pts >= 500 ? "font-bold text-emerald-600" : "texte-doux"}>
              {pts >= 500 ? "✓ Débloqué" : "À 500 pts"}
            </span>
          </div>
        </div>
      </div>
    </Carte>
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
    nom_utilisateur: "",
  });

  useEffect(() => {
    if (dossier) {
      setSaisie({
        type_piece: dossier.type_piece,
        numero_piece: dossier.numero_piece,
        numero_mobile_money: dossier.numero_mobile_money,
        nom_commerce: dossier.nom_commerce,
        nom_utilisateur: dossier.utilisateur?.nom_utilisateur ?? "",
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
        <h1 className="text-2xl font-extrabold">Devenir OAG</h1>
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
          aide="Pour l'équipe seulement : les acheteurs ne le verront jamais."
        />

        <Champ
          etiquette="Nom d'utilisateur"
          required
          maxLength={24}
          placeholder="Faya-02"
          value={saisie.nom_utilisateur}
          onChange={(e) => setSaisie({ ...saisie, nom_utilisateur: e.target.value })}
          erreur={depot.erreur?.pourChamp("nom_utilisateur")}
          aide="C'est la seule chose que les acheteurs verront de vous. Il ne changera plus une fois votre dossier validé."
        />

        {/* Un grossiste installé voudra naturellement mettre l'enseigne qu'il
            a mis des années à faire connaître. Mieux vaut lui dire pourquoi
            c'est refusé avant qu'il ne la saisisse, plutôt qu'après. */}
        <Carte className="flex items-start gap-3 border-[color:var(--color-marine-200)] bg-[color:var(--color-marine-50)] dark:border-[color:var(--color-marine-800)] dark:bg-[color:var(--color-marine-950)]">
          <ShieldAlert className="size-5 shrink-0 text-[color:var(--color-marine-700)] dark:text-[color:var(--color-marine-300)]" />
          <div className="space-y-1 text-sm">
            <p className="font-bold">Pourquoi pas le nom de votre boutique</p>
            <p className="texte-doux">
              Sur Group Achat, l'acheteur ne sait pas qui vous êtes : c'est la
              plateforme qui répond de l'opération, pas vous. Donner votre
              enseigne lui permettrait de passer vous voir directement — là où
              ni le séquestre, ni l'assurance, ni le contrat ne le couvrent.
            </p>
            <p className="texte-doux">
              La réputation que vous construisez ici vous suit même quand vous
              changez de fournisseur.
            </p>
          </div>
        </Carte>

        <div className="surface-douce rounded-2xl p-4 text-sm">
          <p className="mb-1 font-semibold">Ce qui vous attend</p>
          <ul className="texte-doux space-y-1">
            <li>• Création de campagnes libre, sourcing libre.</li>
            <li>• Suivi des paiements en temps réel.</li>
            <li>• Retrait de 100 % de la collecte, moins la commission de votre grade.</li>
            <li>• Preuve de livraison par code de retrait, contre les fausses réclamations.</li>
            <li>• Votre réputation se construit sur les avis de vos acheteurs.</li>
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
