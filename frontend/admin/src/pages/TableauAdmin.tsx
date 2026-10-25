import { motion } from "framer-motion";
import {
  AlertTriangle,
  Banknote,
  FileCheck2,
  Landmark,
  TrendingUp,
  Users,
  Vault,
} from "lucide-react";
import { Link } from "react-router-dom";

import type { TableauDeBordAdmin } from "@commun/api/types";
import { Carte, Squelette } from "@commun/composants/ui";
import { francs } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

/** La supervision : l'argent détenu, ce qu'il reste à traiter. */
export default function TableauAdmin() {
  const { donnees, chargement } = useRequete<TableauDeBordAdmin>(
    "/admin/tableau-de-bord/",
  );

  if (chargement || !donnees) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }, (_, rang) => (
          <Squelette key={rang} className="h-28" />
        ))}
      </div>
    );
  }

  const aTraiter =
    donnees.a_traiter.dossiers_kyc + donnees.a_traiter.decaissements;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-extrabold">Supervision</h1>
        <p className="texte-doux text-sm">
          L'état de la plateforme, et ce qui attend une décision.
        </p>
      </header>

      {aTraiter > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Carte className="flex flex-wrap items-center gap-4 border-[color:var(--color-accent)]">
            <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-accent-doux text-[color:var(--color-accent)]">
              <AlertTriangle className="size-6" />
            </span>
            <p className="flex-1 font-bold">
              {aTraiter} dossier{aTraiter > 1 ? "s" : ""} en attente de votre décision
            </p>
            <div className="flex flex-wrap gap-2">
              {donnees.a_traiter.dossiers_kyc > 0 && (
                <Raccourci
                  vers="/dossiers"
                  libelle={`${donnees.a_traiter.dossiers_kyc} KYC`}
                />
              )}
              {donnees.a_traiter.decaissements > 0 && (
                <Raccourci
                  vers="/decaissements"
                  libelle={`${donnees.a_traiter.decaissements} décaissement(s)`}
                />
              )}
            </div>
          </Carte>
        </motion.div>
      )}

      {/* ── Le séquestre, d'abord : c'est l'argent des autres ───────────── */}
      <section className="grid gap-4 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          className="lg:col-span-2"
        >
          <Carte className="relative overflow-hidden border-transparent text-white">
            <span className="degrade-accent absolute inset-0 -z-10" />
            <span className="absolute -right-12 -top-16 size-56 rounded-full bg-white/12 blur-3xl" />
            <Vault className="size-6" />
            <p className="mt-4 text-sm text-white/80">Détenu en séquestre</p>
            <p className="tabulaire text-4xl font-extrabold">
              {francs(donnees.sequestre.montant_detenu)}
            </p>
            <div className="mt-5 grid grid-cols-3 gap-4 border-t border-white/20 pt-4 text-sm">
              <div>
                <p className="text-white/70">Consigné</p>
                <p className="tabulaire font-bold">
                  {francs(donnees.sequestre.total_consigne)}
                </p>
              </div>
              <div>
                <p className="text-white/70">Libéré</p>
                <p className="tabulaire font-bold">
                  {francs(donnees.sequestre.total_libere)}
                </p>
              </div>
              <div>
                <p className="text-white/70">Remboursé</p>
                <p className="tabulaire font-bold">
                  {francs(donnees.sequestre.total_rembourse)}
                </p>
              </div>
            </div>
          </Carte>
        </motion.div>

        <Tuile
          icone={TrendingUp}
          libelle="Frais encaissés"
          valeur={francs(donnees.revenus.frais_encaisses)}
          detail="1 500 FCFA par décaissement"
          index={1}
        />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tuile
          icone={FileCheck2}
          libelle="Dossiers KYC à vérifier"
          valeur={String(donnees.a_traiter.dossiers_kyc)}
          detail={`${donnees.comptes.groupeurs_valides} groupeurs validés`}
          index={0}
        />
        <Tuile
          icone={Banknote}
          libelle="Décaissements demandés"
          valeur={String(donnees.a_traiter.decaissements)}
          detail="à libérer du séquestre"
          index={1}
        />
        <Tuile
          icone={Users}
          libelle="Comptes"
          valeur={String(donnees.comptes.acheteurs + donnees.comptes.groupeurs)}
          detail={`${donnees.comptes.acheteurs} acheteurs · ${donnees.comptes.groupeurs} groupeurs`}
          index={3}
        />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Compteur libelle="En cours" valeur={donnees.campagnes.en_cours} />
        <Compteur libelle="Financées" valeur={donnees.campagnes.financees} />
        <Compteur libelle="Terminées" valeur={donnees.campagnes.terminees} />
        <Compteur libelle="Annulées" valeur={donnees.campagnes.annulees} />
      </section>

      <Carte className="flex flex-wrap items-center gap-3 text-sm">
        <Landmark className="size-5 text-[color:var(--color-accent)]" />
        <p className="texte-doux flex-1">
          <strong className="text-[color:var(--texte)]">Mode démonstration.</strong>{" "}
          Les {donnees.transactions_simulees} transactions enregistrées sont
          simulées : aucun mouvement réel n'a lieu chez les opérateurs Mobile
          Money. La comptabilité du séquestre est en revanche tenue pour de vrai.
        </p>
      </Carte>
    </div>
  );
}

function Raccourci({ vers, libelle }: { vers: string; libelle: string }) {
  return (
    <Link
      to={vers}
      className="degrade-accent rounded-full px-3.5 py-2 text-sm font-semibold text-white transition-transform hover:scale-105"
    >
      {libelle}
    </Link>
  );
}

function Tuile({
  icone: Icone,
  libelle,
  valeur,
  detail,
  index,
}: {
  icone: typeof Users;
  libelle: string;
  valeur: string;
  detail: string;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
    >
      <Carte>
        <Icone className="size-5 text-[color:var(--color-accent)]" />
        <p className="texte-doux mt-3 text-sm">{libelle}</p>
        <p className="tabulaire mt-0.5 text-2xl font-extrabold">{valeur}</p>
        <p className="texte-doux text-xs">{detail}</p>
      </Carte>
    </motion.div>
  );
}

function Compteur({ libelle, valeur }: { libelle: string; valeur: number }) {
  return (
    <Carte className="!p-4 text-center">
      <p className="tabulaire text-2xl font-extrabold">{valeur}</p>
      <p className="texte-doux text-xs">{libelle}</p>
    </Carte>
  );
}
