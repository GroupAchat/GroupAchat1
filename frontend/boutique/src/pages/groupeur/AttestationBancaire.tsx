import {
  ArrowLeft,
  Landmark,
  Printer,
  ShieldCheck,
} from "lucide-react";
import { Link } from "react-router-dom";

import type { HistoriqueBancaireOag } from "@commun/api/types";
import { Carte, Squelette } from "@commun/composants/ui";
import { francs } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

export default function AttestationBancaire() {
  const { donnees, chargement } = useRequete<HistoriqueBancaireOag>(
    "/groupeur/historique-bancaire/",
  );

  const imprimer = () => {
    window.print();
  };

  if (chargement) {
    return (
      <div className="space-y-4 px-4 py-4">
        <Squelette className="h-8 w-40" />
        <Squelette className="h-64 rounded-2xl" />
      </div>
    );
  }

  if (!donnees) {
    return (
      <div className="px-4 py-12 text-center text-xs text-slate-500">
        Historique indisponible pour l'instant.
      </div>
    );
  }

  const { oag, synthese, lignes_historique } = donnees;

  return (
    <div className="space-y-4 px-4 py-4 pb-20">
      <div className="flex items-center justify-between">
        <Link to="/groupeur" className="texte-doux flex items-center gap-1.5 text-xs font-bold">
          <ArrowLeft className="size-4" />
          Tableau de bord
        </Link>
        <button
          onClick={imprimer}
          className="flex items-center gap-1.5 rounded-full bg-slate-900 px-3 py-1.5 text-xs font-bold text-white shadow-sm"
        >
          <Printer className="size-3.5" />
          Imprimer / PDF
        </button>
      </div>

      <header>
        <div className="flex items-center gap-2">
          <span className="grid size-8 place-items-center rounded-xl bg-blue-100 text-blue-900">
            <Landmark className="size-4" />
          </span>
          <div>
            <h1 className="text-lg font-black leading-tight text-slate-900">
              Historique Certifié OAG
            </h1>
            <p className="texte-doux text-xs">
              Justificatif d'activité pour demande de prêt bancaire
            </p>
          </div>
        </div>
      </header>

      {/* Attestation officielle card */}
      <Carte className="space-y-4 border border-blue-200 bg-white p-4 shadow-sm print:m-0 print:border-none print:p-0 print:shadow-none">
        {/* En-tête certifié */}
        <div className="border-b border-slate-200 pb-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[0.65rem] font-black uppercase tracking-widest text-orange-600">
                PLATEFORME TOGO
              </p>
              <h2 className="text-base font-black text-slate-900">GROUP ACHAT</h2>
            </div>
            <div className="text-right">
              <span className="rounded-md bg-blue-50 px-2 py-0.5 font-mono text-[0.68rem] font-bold text-blue-900">
                {donnees.reference_attestation}
              </span>
              <p className="texte-doux mt-0.5 text-[0.62rem]">Émise le {donnees.emise_le}</p>
            </div>
          </div>
          <p className="mt-2 text-center text-xs font-bold text-slate-700 underline underline-offset-4">
            ATTESTATION D'ACTIVITÉ COMMERCIALE ET DE TRAÇABILITÉ FINANCIÈRE
          </p>
        </div>

        {/* Coordonnées OAG */}
        <div className="grid grid-cols-2 gap-2 rounded-xl bg-slate-50 p-2.5 text-xs">
          <div>
            <p className="texte-doux text-[0.65rem]">Organisateur (OAG)</p>
            <p className="font-bold text-slate-900">{oag.nom_complet}</p>
            <p className="text-[0.68rem] text-slate-600">Commerce : {oag.nom_commerce}</p>
          </div>
          <div className="text-right">
            <p className="texte-doux text-[0.65rem]">Statut juridique</p>
            <p className="font-bold text-emerald-700">✓ {oag.statut_kyc}</p>
            <p className="text-[0.65rem] text-slate-500">Inscrit le {oag.date_inscription}</p>
          </div>
        </div>

        {/* Indicateurs financiers certifiés */}
        <div className="space-y-2">
          <p className="text-[0.68rem] font-bold uppercase tracking-wider text-slate-600">
            Chiffres d'affaires et régularité (BCEAO / Lomé)
          </p>
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-2.5">
              <p className="texte-doux text-[0.65rem]">Total collecté</p>
              <p className="text-sm font-extrabold text-slate-900">
                {francs(synthese.montant_total_collecte_fcfa)}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-2.5">
              <p className="texte-doux text-[0.65rem]">Montant décaissé</p>
              <p className="text-sm font-extrabold text-blue-900">
                {francs(synthese.montant_total_decaisse_fcfa)}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-2.5">
              <p className="texte-doux text-[0.65rem]">Taux de succès</p>
              <p className="text-sm font-extrabold text-emerald-700">
                {synthese.taux_reussite_pourcent} %
              </p>
              <p className="text-[0.62rem] text-slate-500">{synthese.offres_terminees} offres livrées</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-2.5">
              <p className="texte-doux text-[0.65rem]">Satisfaction clients</p>
              <p className="text-sm font-extrabold text-amber-600">
                ★ {synthese.note_satisfaction} / 5
              </p>
              <p className="text-[0.62rem] text-slate-500">{synthese.clients_servis} clients servis</p>
            </div>
          </div>
        </div>

        {/* Garanties */}
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-2.5 text-xs text-emerald-950">
          <p className="flex items-center gap-1.5 font-bold">
            <ShieldCheck className="size-4 text-emerald-700" />
            Cadre de confiance certifié
          </p>
          <ul className="mt-1 space-y-0.5 text-[0.68rem] text-emerald-900">
            <li>• Contrat OAG certifié par Notaire</li>
            <li>• 100 % des opérations couvertes par l'Assurance Tout Risques</li>
            <li>• Traçabilité complète des transactions Mobile Money (Flooz & T-Money)</li>
            <li>• Traitement conforme IPDCP Togo (Loi n°2019-014)</li>
          </ul>
        </div>

        {/* Lignes d'opérations */}
        <div className="space-y-1.5">
          <p className="text-[0.68rem] font-bold uppercase tracking-wider text-slate-600">
            Dernières opérations enregistrées
          </p>
          <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 text-xs">
            {lignes_historique.slice(0, 5).map((l) => (
              <div key={l.id} className="flex items-center justify-between p-2">
                <div>
                  <p className="font-bold text-slate-900">{l.titre}</p>
                  <p className="texte-doux text-[0.65rem]">{l.date_creation} • {l.participants} acheteurs</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-slate-900">{francs(l.montant_collecte)}</p>
                  <span className="text-[0.62rem] font-semibold text-emerald-700">{l.statut}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tampon & Signature */}
        <div className="border-t border-slate-200 pt-3 text-center text-[0.65rem] text-slate-500">
          <p className="font-bold text-slate-700">Direction Générale Group Achat Togo</p>
          <p>Lomé — République Togolaise</p>
          <p className="mt-1 italic">
            Document généré automatiquement à la demande de l'OAG. Valable pour instruction de dossier de crédit.
          </p>
        </div>
      </Carte>
    </div>
  );
}
