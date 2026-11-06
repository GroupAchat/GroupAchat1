import { motion } from "framer-motion";
import { Check, Package, ShieldAlert, Users } from "lucide-react";
import { useState } from "react";

import type { Campagne } from "@commun/api/types";
import { Feuille } from "@commun/composants/Feuille";
import {
  Alerte,
  Avatar,
  Bouton,
  Carte,
  Etiquette,
  EtatVide,
  Squelette,
  ZoneTexte,
} from "@commun/composants/ui";
import { dateLongue, francs, gradeLisible } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/**
 * La relecture des groupages avant la vitrine.
 *
 * **C'est le seul filtre entre un OAG tout neuf et l'acheteur.** Le dossier
 * de confiance dit qui il est ; il ne dit rien de ce qu'il publie. Un prix
 * absurde, une photo volée ou un produit interdit coûtent plus cher à
 * réparer qu'à relire — et c'est l'acheteur qui paie la différence, puisque
 * c'est la plateforme qu'il croit.
 *
 * Qui passe ici dépend du grade : systématique en Bronze, un sur quatre en
 * Argent, jamais en Or.
 */
export default function Verification() {
  const { donnees, chargement, recharger } = useRequete<Campagne[]>(
    "/admin/campagnes/a-verifier/",
  );
  const [examine, setExamine] = useState<Campagne | null>(null);

  const file = donnees ?? [];

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold">Groupages à vérifier</h1>
        <p className="texte-doux text-sm">
          Relus avant d'apparaître au catalogue. Un refus renvoie l'OAG au
          brouillon et lui rend sa publication.
        </p>
      </header>

      {chargement ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }, (_, rang) => (
            <Squelette key={rang} className="h-24" />
          ))}
        </div>
      ) : !file.length ? (
        <EtatVide
          icone={<Check className="size-7" />}
          titre="Rien à relire"
          texte="Tous les groupages demandés sont passés."
        />
      ) : (
        <ul className="space-y-3">
          {file.map((campagne, rang) => (
            <motion.li
              key={campagne.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(rang, 8) * 0.04 }}
            >
              <button
                type="button"
                onClick={() => setExamine(campagne)}
                className="w-full text-left"
              >
                <Carte survol className="flex items-center gap-4">
                  <span className="bg-accent-doux grid size-11 shrink-0 place-items-center rounded-2xl text-[color:var(--color-accent)]">
                    <Package className="size-5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-bold">{campagne.titre}</p>
                    <p className="texte-doux truncate text-sm">
                      {campagne.groupeur.nom_utilisateur} ·{" "}
                      {gradeLisible(campagne.groupeur.grade)} ·{" "}
                      {francs(campagne.prix_unitaire)} l'unité
                    </p>
                  </div>
                  <Etiquette ton="alerte">À relire</Etiquette>
                </Carte>
              </button>
            </motion.li>
          ))}
        </ul>
      )}

      <FeuilleExamen
        campagne={examine}
        surFermeture={() => setExamine(null)}
        surDecision={async () => {
          setExamine(null);
          await recharger();
        }}
      />
    </div>
  );
}

function FeuilleExamen({
  campagne,
  surFermeture,
  surDecision,
}: {
  campagne: Campagne | null;
  surFermeture: () => void;
  surDecision: () => Promise<void>;
}) {
  const [motif, setMotif] = useState("");

  const trancher = useAction(async (decision: "valider" | "refuser") => {
    const retour = await api.post(
      `/admin/campagnes/${campagne!.id}/verification/`,
      { decision, motif },
    );
    setMotif("");
    await surDecision();
    return retour;
  });

  if (!campagne) return null;

  return (
    <Feuille
      ouverte={Boolean(campagne)}
      surFermeture={surFermeture}
      titre="Relire ce groupage"
    >
      <div className="space-y-4">
        <div>
          <p className="font-bold">{campagne.titre}</p>
          <p className="texte-doux text-sm">{campagne.produit.nom}</p>
        </div>

        <div className="flex items-center gap-3">
          <Avatar nom={campagne.groupeur.nom_utilisateur} taille={40} />
          <div className="min-w-0 text-sm">
            <p className="truncate font-semibold">
              {campagne.groupeur.nom_utilisateur}
            </p>
            <p className="texte-doux">
              {gradeLisible(campagne.groupeur.grade)}
              {campagne.groupeur.reputation &&
                ` · note ${campagne.groupeur.reputation.note}`}
            </p>
          </div>
        </div>

        <dl className="divide-y text-sm">
          <Ligne intitule="Prix affiché" valeur={francs(campagne.prix_unitaire)} />
          <Ligne
            intitule="Minimum"
            valeur={`${campagne.quantite_minimale} pièces`}
          />
          <Ligne
            intitule="Fin de collecte"
            valeur={dateLongue(campagne.date_limite)}
          />
          <Ligne
            intitule="Barème"
            valeur={
              campagne.paliers.length
                ? `${campagne.paliers.length} paliers`
                : "aucun"
            }
          />
          <Ligne
            intitule="Photos du lot"
            valeur={String(campagne.medias?.length ?? 0)}
          />
        </dl>

        {campagne.description && (
          <p className="surface-douce rounded-2xl p-3 text-sm">
            {campagne.description}
          </p>
        )}

        {/* Les paliers en clair : c'est là que se cache un barème saisi de
            travers, qui ferait payer plus cher celui qui prend plus. */}
        {campagne.paliers.length > 0 && (
          <ul className="space-y-1 text-sm">
            {campagne.paliers.map((palier) => (
              <li key={palier.id} className="flex justify-between gap-3">
                <span className="texte-doux">
                  {palier.quantite_min} pièces
                  {palier.participants_min
                    ? ` · ${palier.participants_min} participants`
                    : ""}
                </span>
                <span className="tabulaire font-semibold">
                  {francs(palier.prix_unitaire)}
                </span>
              </li>
            ))}
          </ul>
        )}

        <ZoneTexte
          etiquette="Motif, en cas de refus"
          rows={3}
          maxLength={300}
          value={motif}
          onChange={(evenement) => setMotif(evenement.target.value)}
        />
        <p className="texte-doux text-xs">
          Obligatoire pour refuser : sans motif, l'OAG ne sait pas quoi
          corriger et redépose le même groupage.
        </p>

        <Alerte>{trancher.erreur?.message}</Alerte>

        <div className="grid gap-2 sm:grid-cols-2">
          <Bouton
            pleineLargeur
            chargement={trancher.envoi}
            icone={<Check className="size-4" />}
            onClick={() => void trancher.lancer("valider")}
          >
            Mettre au catalogue
          </Bouton>
          <Bouton
            ton="danger"
            pleineLargeur
            disabled={!motif.trim()}
            chargement={trancher.envoi}
            icone={<ShieldAlert className="size-4" />}
            onClick={() => void trancher.lancer("refuser")}
          >
            Refuser
          </Bouton>
        </div>

        <p className="texte-doux flex items-start gap-2 text-xs">
          <Users className="mt-0.5 size-3.5 shrink-0" />
          Un refus rend à l'OAG la publication consommée : elle paie la mise
          en ligne, et la mise en ligne n'a pas eu lieu.
        </p>
      </div>
    </Feuille>
  );
}

function Ligne({
  intitule,
  valeur,
}: {
  intitule: string;
  valeur: React.ReactNode;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-2">
      <dt className="texte-doux">{intitule}</dt>
      <dd className="text-right font-semibold">{valeur}</dd>
    </div>
  );
}
