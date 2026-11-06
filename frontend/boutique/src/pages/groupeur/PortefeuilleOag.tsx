import { motion } from "framer-motion";
import {
  ArrowLeft,
  CheckCircle2,
  Landmark,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";

import type { TableauDeBordGroupeur } from "@commun/api/types";
import { BandeauGrade } from "@/composants/BandeauGrade";
import { CarteDroitDePublier } from "@/composants/DroitDePublier";
import { Bouton, Carte, Squelette } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { francs, gradeLisible, tauxCommission, telephoneLisible } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

/**
 * Portefeuille et finances de l'OAG.
 * Affichage coloré et animé de ses fonds, commissions et statut de grade.
 */
export default function PortefeuilleOag() {
  const { utilisateur } = useSession();
  const { donnees: bord, chargement } = useRequete<TableauDeBordGroupeur>(
    "/groupeur/tableau-de-bord/",
  );

  const centiemes = utilisateur?.points.commission_centiemes ?? 400;
  const grade = utilisateur?.points.grade ?? "nouveau";

  if (chargement || !bord) {
    return (
      <div className="space-y-4 px-4 py-4">
        <Squelette className="h-8 w-44" />
        <Squelette className="h-44 rounded-3xl" />
        <Squelette className="h-28 rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="w-full space-y-5 px-4 py-4 pb-20">
      <div className="flex items-center justify-between">
        <Link
          to="/groupeur"
          className="texte-doux inline-flex items-center gap-1.5 text-xs font-semibold"
        >
          <ArrowLeft className="size-4" />
          Tableau de bord
        </Link>
        <span className="rounded-full bg-blue-100 dark:bg-blue-950 px-2.5 py-0.5 text-xs font-bold text-blue-800 dark:text-blue-300">
          Portefeuille OAG
        </span>
      </div>

      <header>
        <h1 className="text-xl font-extrabold text-slate-900 dark:text-slate-100">
          Mon Portefeuille
        </h1>
        <p className="texte-doux text-xs">
          Suivi de vos fonds consignés, montants décaissés et commissions
        </p>
      </header>

      {/* ── Carte portefeuille virtuelle OAG colorée ──────────────────── */}
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="relative overflow-hidden rounded-[26px] bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 p-5 text-white shadow-xl"
      >
        <span className="absolute -right-12 -top-12 size-44 rounded-full bg-blue-500/20 blur-2xl" />
        <span className="absolute -bottom-16 left-6 size-44 rounded-full bg-amber-500/20 blur-2xl" />

        <div className="relative space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="grid size-9 place-items-center rounded-xl bg-white/10 text-white backdrop-blur-xs">
                <Wallet className="size-5" />
              </span>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-300">
                  Group Achat Togo
                </p>
                <p className="text-xs font-semibold text-white/90">
                  Compte OAG certifié
                </p>
              </div>
            </div>
            <span className="rounded-full bg-amber-400/20 px-2.5 py-0.5 text-[11px] font-bold text-amber-300 border border-amber-400/30">
              Grade {gradeLisible(grade)}
            </span>
          </div>

          <div>
            <p className="text-xs text-white/70">Fonds actuellement sous séquestre</p>
            <p className="tabulaire mt-0.5 text-2xl font-black text-amber-300">
              {francs(bord.collecte.montant_consigne)}
            </p>
            <p className="text-[11px] text-white/60">
              {bord.collecte.pieces} pièces vendues auprès de {bord.collecte.participants} acheteurs
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 border-t border-white/15 pt-3 text-xs">
            <div>
              <p className="text-white/65 text-[11px]">Déjà décaissé (reçu)</p>
              <p className="tabulaire text-sm font-bold text-emerald-300">
                {francs(bord.decaissements.montant_recu)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-white/65 text-[11px]">Commission prélevée</p>
              <p className="tabulaire text-sm font-bold text-slate-300">
                {francs(bord.decaissements.frais_payes)} ({tauxCommission(centiemes)})
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── Statut actuel & Grade OAG ─────────────────────────────────── */}
      <section className="space-y-2">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Statut & Progression
        </h2>
        <BandeauGrade />
      </section>

      {/* ── Mode de versement vérifié ─────────────────────────────────── */}
      <Carte className="space-y-3">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-2xl bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
            <CheckCircle2 className="size-5" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-slate-900 dark:text-slate-100">
              Mobile Money de versement
            </p>
            <p className="texte-doux text-xs">
              Numéro vérifié : <strong>{telephoneLisible(utilisateur?.telephone ?? "")}</strong>
            </p>
          </div>
        </div>
        <p className="texte-doux text-xs leading-relaxed">
          Les décaissements sont versés automatiquement par Flooz ou T-Money dès qu'un groupage atteint son minimum et que la distribution commence.
        </p>
      </Carte>

      {/* ── Droits de publication ─────────────────────────────────────── */}
      <section className="space-y-2">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Tickets de publication
        </h2>
        <CarteDroitDePublier compact />
      </section>

      {/* ── Attestation bancaire ───────────────────────────────────────── */}
      <Carte className="flex items-center justify-between gap-3 border-indigo-200/80 bg-gradient-to-r from-indigo-50/70 to-blue-50/40 dark:border-indigo-900/40 dark:from-indigo-950/20 dark:to-blue-950/20">
        <div className="flex items-center gap-2.5">
          <span className="grid size-9 place-items-center rounded-xl bg-indigo-600 text-white shadow-xs">
            <Landmark className="size-4" />
          </span>
          <div>
            <p className="text-xs font-bold text-slate-900 dark:text-slate-100">
              Attestation bancaire certifiée
            </p>
            <p className="texte-doux text-[11px]">
              Export officiel pour vos dossiers de crédit
            </p>
          </div>
        </div>
        <Link to="/groupeur/historique-bancaire">
          <Bouton taille="sm" ton="contour">
            Générer
          </Bouton>
        </Link>
      </Carte>
    </div>
  );
}
