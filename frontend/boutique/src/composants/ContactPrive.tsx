import {
  BadgeCheck,
  ChevronRight,
  MessageCircle,
  Sparkles,
  ShieldAlert,
  RefreshCw,
  Coins,
  ShieldCheck,
} from "lucide-react";
import { Link } from "react-router-dom";

import type { EtatContactPrive, GroupeurPublic } from "@commun/api/types";
import { Alerte, Bouton } from "@commun/composants/ui";
import { francs } from "@commun/outils/formats";
import { useAction } from "@commun/outils/requetes";

/**
 * L'entrée vers le Contact Privé sur la fiche d'une campagne.
 */
export function ContactPriveSurCampagne({
  groupeur,
  campagneId,
  etat,
}: {
  groupeur: GroupeurPublic;
  campagneId: number;
  etat?: EtatContactPrive | null;
}) {
  return (
    <Link
      to={`/messages/nouveau?campagne=${campagneId}`}
      className="surface group flex w-full items-center gap-3.5 rounded-2xl border border-slate-200/90 p-3.5 text-left transition-all hover:border-orange-400 hover:shadow-sm"
    >
      <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-orange-100 text-orange-600 group-hover:bg-orange-600 group-hover:text-white transition-colors">
        <MessageCircle className="size-5" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2">
          <span className="block text-sm font-bold text-slate-900">
            Discuter avec {groupeur.nom_utilisateur}
          </span>
          {etat?.actif ? (
            <span className="inline-flex items-center gap-0.5 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
              <ShieldCheck className="size-3" /> Actif
            </span>
          ) : (
            <span className="inline-flex items-center gap-0.5 rounded-full bg-orange-100 px-2 py-0.5 text-[10px] font-bold text-orange-800">
              <Sparkles className="size-3" /> +10 pts
            </span>
          )}
        </span>
        <span className="texte-doux block text-xs mt-0.5">
          {etat?.actif
            ? "Votre Contact Privé est actif · Envoyez votre message en direct"
            : "Contact Privé · 2 000 FCFA/mois · Renouvelable"}
        </span>
      </span>
      <ChevronRight className="texte-doux size-4 shrink-0 group-hover:text-orange-600 transition-colors" />
    </Link>
  );
}

/**
 * Présentation complète de l'abonnement Contact Privé :
 * - Tarif : 2 000 FCFA
 * - Durée : 1 mois (30 jours)
 * - Renouvelable à tout moment
 * - Récompense : gain de points fidélité à chaque abonnement/renouvellement (+10 pts)
 */
export function OffreAbonnement({
  etat,
  nomOag,
  action,
  compact = false,
}: {
  etat: EtatContactPrive | null;
  nomOag?: string;
  action: ReturnType<typeof useAction>;
  compact?: boolean;
}) {
  const prix = etat?.prix ?? 2000;
  const points = etat?.points_par_mois ?? 10;
  const actif = Boolean(etat?.actif);

  return (
    <div className="space-y-4">
      {/* En-tête coloré avec badge de points */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-orange-500 via-amber-500 to-orange-600 p-4 text-white shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div>
            <span className="inline-flex items-center gap-1 rounded-full bg-white/20 px-2.5 py-0.5 text-[11px] font-bold tracking-wide backdrop-blur-xs">
              <Sparkles className="size-3" /> FONCTIONNALITÉ CONTACT PRIVÉ
            </span>
            <h3 className="mt-1.5 text-lg font-extrabold leading-tight">
              {actif ? "Prolonger votre accès OAG" : "Discutez en direct avec l'OAG"}
            </h3>
            <p className="mt-1 text-xs text-white/90 leading-snug">
              {nomOag
                ? `Échangez librement avec ${nomOag} et tous les organisateurs de groupage.`
                : "Posez toutes vos questions sur les lots, délais et retraits."}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <span className="rounded-xl bg-white/25 px-2.5 py-1 text-xs font-black backdrop-blur-xs block">
              +{points} PTS
            </span>
            <span className="text-[10px] text-white/80 block mt-0.5">par mois</span>
          </div>
        </div>
      </div>

      {!compact && (
        <div className="space-y-3">
          <ul className="space-y-2.5">
            <Avantage icone={MessageCircle}>
              Discussion privée avec <strong>l'OAG pendant 1 mois</strong> (30 jours illimités)
            </Avantage>
            <Avantage icone={RefreshCw}>
              <strong>Renouvelable à tout moment</strong> sans perdre aucun jour d'avance
            </Avantage>
            <Avantage icone={Coins}>
              <strong>+{points} points de fidélité</strong> crédités sur votre compte à chaque souscription
            </Avantage>
            <Avantage icone={BadgeCheck}>
              Coordonnées directes et suivi transparent de votre commande
            </Avantage>
          </ul>
        </div>
      )}

      {/* Carte tarifaire */}
      <div className="surface rounded-2xl border border-slate-200/90 p-4 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <span className="font-bold text-slate-900 block">Contact Privé OAG</span>
            <span className="text-xs text-slate-500">
              Accès illimité pendant {etat?.duree_jours ?? 30} jours (1 mois)
            </span>
          </div>
          <div className="text-right">
            <span className="text-xl font-extrabold text-orange-600 tabulaire">
              {francs(prix)}
            </span>
            <span className="block text-[10px] font-semibold text-emerald-600">
              +{points} pts gagnés
            </span>
          </div>
        </div>

        {/* Moyens de paiement mobile money acceptés au Togo */}
        <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2.5 text-[11px] text-slate-500">
          <span>Paiement mobile Togo :</span>
          <span className="font-semibold text-slate-700">TMoney · Moov Flooz</span>
        </div>
      </div>

      <AvertissementHorsPlateforme />
      <Alerte>{action.erreur?.message}</Alerte>

      <Bouton
        pleineLargeur
        taille="lg"
        chargement={action.envoi}
        onClick={() => void action.lancer(undefined as never)}
        className="font-bold bg-orange-600 hover:bg-orange-700 text-white shadow-md active:scale-98"
      >
        {actif
          ? `Renouveler pour 1 mois — ${francs(prix)} (+${points} pts)`
          : `Activer pour 1 mois — ${francs(prix)} (+${points} pts)`}
      </Bouton>

      <p className="texte-doux text-center text-xs">
        Validation instantanée via votre compte Mobile Money.
      </p>
    </div>
  );
}

function Avantage({
  icone: Icone,
  children,
}: {
  icone: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <li className="flex items-start gap-2.5 text-xs text-slate-700">
      <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-lg bg-orange-100 text-orange-600">
        <Icone className="size-3.5" />
      </span>
      <span className="leading-snug pt-0.5">{children}</span>
    </li>
  );
}

/**
 * Avertissement de sécurité pour protéger acheteurs et OAG.
 */
export function AvertissementHorsPlateforme() {
  return (
    <div className="rounded-xl bg-slate-50 border border-slate-200/80 p-2.5 text-slate-600 flex items-start gap-2 text-xs">
      <ShieldAlert className="mt-0.5 size-3.5 shrink-0 text-amber-600" />
      <span className="text-[11px] leading-relaxed">
        Restez sur la plateforme : le séquestre bancaire et l'assurance Togo protègent vos fonds et vos échanges jusqu'au retrait effectif.
      </span>
    </div>
  );
}
