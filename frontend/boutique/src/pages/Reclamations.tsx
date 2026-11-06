import {
  ArrowLeft,
  Plus,
  Scale,
} from "lucide-react";
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import type { MotifReclamation, Page, Participation, Reclamation } from "@commun/api/types";
import {
  Alerte,
  Bouton,
  Carte,
  Champ,
  Etiquette,
  EtatVide,
  Squelette,
} from "@commun/composants/ui";
import { dateLongue, francs } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

const MOTIFS: { cle: MotifReclamation; libelle: string; detail: string }[] = [
  { cle: "non_livraison", libelle: "Non-livraison", detail: "Commande payée mais colis non remis" },
  { cle: "retard", libelle: "Retard de livraison", detail: "Délai annoncé dépassé sans information" },
  { cle: "non_conforme", libelle: "Produit non conforme", detail: "Article reçu différent de la description" },
  { cle: "incomplete", libelle: "Commande incomplète", detail: "Quantité manquante ou pièces absentes" },
  { cle: "minimum_non_atteint", libelle: "Minimum non atteint", detail: "Club d'achat non abouti, remboursement attendu" },
  { cle: "paiement_conteste", libelle: "Paiement contesté", detail: "Débit Mobile Money sans validation" },
  { cle: "fraude", libelle: "Suspicion de fraude", detail: "OAG injoignable ou anomalie grave" },
];

export default function Reclamations() {
  const [params] = useSearchParams();
  const participationIdParam = params.get("participation");
  const [modeFormulaire, setModeFormulaire] = useState(Boolean(participationIdParam));
  const { donnees: reclamations, chargement, recharger } = useRequete<Reclamation[]>("/reclamations/");
  const { donnees: partsDonnees } = useRequete<Page<Participation>>("/participations/");

  const participations = partsDonnees?.results ?? [];

  return (
    <div className="space-y-4 px-4 py-4 pb-20">
      <div className="flex items-center justify-between">
        <Link to="/mes-achats" className="texte-doux flex items-center gap-1.5 text-xs font-bold">
          <ArrowLeft className="size-4" />
          Mes achats
        </Link>
        {!modeFormulaire && (
          <button
            onClick={() => setModeFormulaire(true)}
            className="flex items-center gap-1.5 rounded-full bg-[color:var(--color-accent)] px-3 py-1.5 text-xs font-bold text-white shadow-sm"
          >
            <Plus className="size-3.5" />
            Nouveau dossier
          </button>
        )}
      </div>

      <header>
        <div className="flex items-center gap-2">
          <span className="grid size-8 place-items-center rounded-xl bg-orange-100 text-[color:var(--color-accent)]">
            <Scale className="size-4" />
          </span>
          <div>
            <h1 className="text-lg font-black leading-tight">Réclamations & Litiges</h1>
            <p className="texte-doux text-xs">Procédure contradictoire en 5 étapes garantie par la plateforme</p>
          </div>
        </div>
      </header>

      {modeFormulaire ? (
        <FormulaireReclamation
          participations={participations}
          preselectionId={participationIdParam ? Number(participationIdParam) : undefined}
          surAnnuler={() => setModeFormulaire(false)}
          surCree={async () => {
            setModeFormulaire(false);
            await recharger();
          }}
        />
      ) : chargement ? (
        <div className="space-y-3">
          <Squelette className="h-24 rounded-2xl" />
          <Squelette className="h-24 rounded-2xl" />
        </div>
      ) : !reclamations || reclamations.length === 0 ? (
        <EtatVide
          icone={<Scale className="size-7" />}
          titre="Aucun dossier en cours"
          texte="Chaque Club d'achat est couvert par l'Assurance Tout Risques. En cas de problème de livraison ou de conformité, vous pouvez ouvrir un dossier ici."
          action={
            <Bouton taille="sm" onClick={() => setModeFormulaire(true)}>
              Ouvrir une réclamation
            </Bouton>
          }
        />
      ) : (
        <div className="space-y-3">
          {reclamations.map((rec) => (
            <CarteDossier key={rec.id} reclamation={rec} onRefresh={recharger} />
          ))}
        </div>
      )}
    </div>
  );
}

function FormulaireReclamation({
  participations,
  preselectionId,
  surAnnuler,
  surCree,
}: {
  participations: Participation[];
  preselectionId?: number;
  surAnnuler: () => void;
  surCree: () => Promise<void>;
}) {
  const [partId, setPartId] = useState<number | undefined>(preselectionId ?? participations[0]?.id);
  const [motif, setMotif] = useState<MotifReclamation>("non_livraison");
  const [description, setDescription] = useState("");

  const soumettre = useAction(async () => {
    if (!partId) throw new Error("Sélectionnez une commande concernée.");
    if (!description.trim()) throw new Error("Veuillez décrire le problème rencontré.");
    await api.post("/reclamations/", {
      participation: partId,
      motif,
      description: description.trim(),
    });
    await surCree();
  });

  return (
    <Carte className="space-y-4 border border-orange-200/80 bg-orange-50/20">
      <div className="border-b pb-2">
        <h2 className="text-sm font-bold text-slate-900">Étape 1 : Ouverture du dossier</h2>
        <p className="texte-doux text-xs">Un numéro de suivi officiel REC-2026-XXXX vous sera immédiatement attribué.</p>
      </div>

      <div className="space-y-1.5">
        <label className="text-xs font-bold text-slate-700">Commande concernée</label>
        {participations.length === 0 ? (
          <p className="texte-doux text-xs italic">Aucun achat disponible.</p>
        ) : (
          <select
            value={partId}
            onChange={(e) => setPartId(Number(e.target.value))}
            className="w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs font-medium focus:border-orange-500 focus:outline-none"
          >
            {participations.map((p) => (
              <option key={p.id} value={p.id}>
                {p.campagne.titre} — {francs(p.montant_total)} ({p.statut_libelle})
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="space-y-1.5">
        <label className="text-xs font-bold text-slate-700">Type d'incident</label>
        <div className="grid gap-2">
          {MOTIFS.map((m) => (
            <label
              key={m.cle}
              onClick={() => setMotif(m.cle)}
              className={`flex cursor-pointer items-start gap-2.5 rounded-xl border p-2.5 transition-colors ${
                motif === m.cle ? "border-orange-500 bg-orange-500/10" : "border-slate-200 bg-white"
              }`}
            >
              <input
                type="radio"
                name="motif"
                checked={motif === m.cle}
                onChange={() => setMotif(m.cle)}
                className="mt-0.5 text-orange-600 focus:ring-orange-500"
              />
              <div>
                <p className="text-xs font-bold leading-tight text-slate-800">{m.libelle}</p>
                <p className="texte-doux text-[0.68rem]">{m.detail}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-xs font-bold text-slate-700">Description des faits</label>
        <textarea
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Expliquez ce qui s'est passé, date de livraison prévue, détails du produit..."
          className="w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs focus:border-orange-500 focus:outline-none"
        />
      </div>

      <Alerte>{soumettre.erreur?.message}</Alerte>

      <div className="flex gap-2 pt-1">
        <Bouton ton="contour" taille="sm" className="flex-1" onClick={surAnnuler}>
          Annuler
        </Bouton>
        <Bouton
          taille="sm"
          className="flex-1"
          chargement={soumettre.envoi}
          onClick={() => void soumettre.lancer(undefined as never)}
        >
          Créer mon dossier
        </Bouton>
      </div>
    </Carte>
  );
}

function CarteDossier({
  reclamation,
  onRefresh,
}: {
  reclamation: Reclamation;
  onRefresh: () => Promise<void>;
}) {
  const [reponseTexte, setReponseTexte] = useState("");
  const repondreOag = useAction(async () => {
    if (!reponseTexte.trim()) return;
    await api.post(`/reclamations/${reclamation.id}/repondre_oag/`, {
      reponse_oag: reponseTexte.trim(),
    });
    setReponseTexte("");
    await onRefresh();
  });

  const etapes = [
    { cle: "ouverture", num: "1", nom: "Ouverture" },
    { cle: "accuse_reception", num: "2", nom: "Accusé" },
    { cle: "contradictoire", num: "3", nom: "Contradictoire" },
    { cle: "analyse", num: "4", nom: "Analyse" },
    { cle: "decision", num: "5", nom: "Décision" },
  ];

  const rangActif = etapes.findIndex((e) => e.cle === reclamation.etape);
  const actifIdx = rangActif >= 0 ? rangActif : 1;

  return (
    <Carte className="space-y-3 border-slate-200">
      <div className="flex items-start justify-between gap-2 border-b pb-2">
        <div>
          <span className="font-mono text-xs font-black tracking-wider text-[color:var(--color-accent)]">
            {reclamation.numero_dossier}
          </span>
          <h3 className="text-xs font-bold leading-tight text-slate-900">{reclamation.campagne_titre}</h3>
        </div>
        <Etiquette ton="accent">{reclamation.motif_libelle}</Etiquette>
      </div>

      {/* Barre des 5 étapes */}
      <div className="space-y-1.5 rounded-xl bg-slate-50 p-2.5">
        <p className="text-[0.65rem] font-bold uppercase tracking-wider text-slate-500">
          Progression de la procédure
        </p>
        <div className="flex items-center justify-between gap-1">
          {etapes.map((et, i) => (
            <div key={et.cle} className="flex flex-1 flex-col items-center">
              <span
                className={`grid size-5 place-items-center rounded-full text-[0.62rem] font-black ${
                  i <= actifIdx ? "bg-orange-500 text-white" : "bg-slate-200 text-slate-500"
                }`}
              >
                {et.num}
              </span>
              <span className="mt-0.5 text-[0.58rem] font-medium leading-tight text-slate-600">
                {et.nom}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-1 text-xs">
        <p className="font-semibold text-slate-700">Faits déclarés :</p>
        <p className="rounded-lg bg-slate-50 p-2 text-slate-600">{reclamation.description}</p>
      </div>

      {reclamation.reponse_oag && (
        <div className="space-y-1 text-xs">
          <p className="font-semibold text-blue-800">Éléments contradictoires de l'OAG :</p>
          <p className="rounded-lg bg-blue-50 p-2 text-blue-900">{reclamation.reponse_oag}</p>
        </div>
      )}

      {reclamation.decision && (
        <div className="space-y-1 text-xs">
          <p className="font-semibold text-emerald-800">Décision motivée de la plateforme :</p>
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-2 text-emerald-950">
            <p>{reclamation.decision}</p>
            {reclamation.remboursement_accorde > 0 && (
              <p className="mt-1 font-bold text-emerald-700">
                ✓ Remboursement exécuté : {francs(reclamation.remboursement_accorde)}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Si étape contradictoire, possibilité de répondre */}
      {reclamation.etape === "accuse_reception" && (
        <div className="space-y-1.5 pt-1">
          <Champ
            etiquette="Ajouter une précision"
            placeholder="Élément complémentaire..."
            value={reponseTexte}
            onChange={(e) => setReponseTexte(e.target.value)}
          />
          <Bouton
            taille="sm"
            ton="contour"
            chargement={repondreOag.envoi}
            onClick={() => void repondreOag.lancer(undefined as never)}
          >
            Transmettre
          </Bouton>
        </div>
      )}

      <p className="texte-doux pt-1 text-[0.65rem]">
        Ouvert le {dateLongue(reclamation.cree_le)} • Délai moyen de résolution : 3 à 5 jours ouvrés
      </p>
    </Carte>
  );
}
