import { motion } from "framer-motion";
import { BadgeCheck, FileCheck2, Phone, ShieldX, Wallet } from "lucide-react";
import { useState } from "react";

import type { DossierKYC, Page } from "@commun/api/types";
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
import { dateLongue, telephoneLisible } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/**
 * La vérification des dossiers de confiance.
 *
 * C'est la décision la plus engageante de la console : valider un dossier
 * autorise quelqu'un à collecter l'argent d'inconnus. Le rejet exige un
 * motif, faute de quoi le groupeur redéposerait le même dossier sans savoir
 * quoi corriger.
 */
export default function Dossiers() {
  const [filtre, setFiltre] = useState<"en_attente" | "valide" | "rejete" | "tous">(
    "en_attente",
  );
  const { donnees, chargement, recharger } = useRequete<Page<DossierKYC>>(
    `/admin/dossiers/?statut=${filtre}`,
    [filtre],
  );
  const [examine, setExamine] = useState<DossierKYC | null>(null);

  const dossiers = donnees?.results ?? [];

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold">Dossiers de confiance</h1>
        <p className="texte-doux text-sm">
          Vérifiez l'identité des groupeurs avant de leur ouvrir l'espace.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["en_attente", "À vérifier"],
            ["valide", "Validés"],
            ["rejete", "Rejetés"],
            ["tous", "Tous"],
          ] as const
        ).map(([cle, libelle]) => (
          <button
            key={cle}
            onClick={() => setFiltre(cle)}
            className={
              filtre === cle
                ? "degrade-accent rounded-full px-4 py-2 text-sm font-semibold text-white"
                : "surface rounded-full px-4 py-2 text-sm font-semibold"
            }
          >
            {libelle}
          </button>
        ))}
      </div>

      {chargement ? (
        <div className="space-y-3">
          <Squelette className="h-24" />
          <Squelette className="h-24" />
        </div>
      ) : dossiers.length === 0 ? (
        <EtatVide
          icone={<FileCheck2 className="size-7" />}
          titre="Aucun dossier"
          texte={
            filtre === "en_attente"
              ? "Tout est traité. Les nouveaux dépôts apparaîtront ici."
              : "Rien dans cette catégorie."
          }
        />
      ) : (
        <ul className="space-y-3">
          {dossiers.map((dossier, rang) => (
            <motion.li
              key={dossier.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(rang, 8) * 0.05 }}
            >
              <Carte className="flex flex-wrap items-center gap-4">
                <Avatar nom={dossier.utilisateur.nom_complet} taille={48} />
                <div className="min-w-0 flex-1">
                  <p className="font-bold">
                    {dossier.utilisateur.nom_complet}
                    {dossier.nom_commerce && (
                      <span className="texte-doux font-normal">
                        {" "}
                        · {dossier.nom_commerce}
                      </span>
                    )}
                  </p>
                  <p className="texte-doux tabulaire flex flex-wrap items-center gap-x-3 text-sm">
                    <span className="flex items-center gap-1">
                      <Phone className="size-3" />
                      {telephoneLisible(dossier.utilisateur.telephone)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Wallet className="size-3" />
                      {telephoneLisible(dossier.numero_mobile_money)}
                    </span>
                  </p>
                  <p className="texte-doux text-xs">
                    Déposé le {dateLongue(dossier.depose_le)}
                  </p>
                </div>
                {dossier.statut === "en_attente" ? (
                  <Bouton onClick={() => setExamine(dossier)}>Examiner</Bouton>
                ) : (
                  <Etiquette ton={dossier.statut === "valide" ? "succes" : "danger"}>
                    {dossier.statut === "valide" ? "Validé" : "Rejeté"}
                  </Etiquette>
                )}
              </Carte>
            </motion.li>
          ))}
        </ul>
      )}

      <FeuilleDecision
        dossier={examine}
        surFermeture={() => setExamine(null)}
        surDecision={async () => {
          setExamine(null);
          await recharger();
        }}
      />
    </div>
  );
}

function FeuilleDecision({
  dossier,
  surFermeture,
  surDecision,
}: {
  dossier: DossierKYC | null;
  surFermeture: () => void;
  surDecision: () => Promise<void>;
}) {
  const [motif, setMotif] = useState("");

  const trancher = useAction(async (decision: "valider" | "rejeter") => {
    await api.post(`/admin/dossiers/${dossier!.id}/decision/`, { decision, motif });
    setMotif("");
    await surDecision();
  });

  const pieces: Record<string, string> = {
    cni: "Carte nationale d'identité",
    passeport: "Passeport",
    carte_consulaire: "Carte consulaire",
  };

  return (
    <Feuille
      ouverte={dossier !== null}
      surFermeture={surFermeture}
      titre="Examiner le dossier"
    >
      {dossier && (
        <div className="space-y-5 py-2">
          <div className="flex items-center gap-3">
            <Avatar nom={dossier.utilisateur.nom_complet} taille={52} />
            <div>
              <p className="font-bold">{dossier.utilisateur.nom_complet}</p>
              <p className="texte-doux tabulaire text-sm">
                {telephoneLisible(dossier.utilisateur.telephone)}
              </p>
            </div>
          </div>

          <dl className="surface-douce divide-y rounded-2xl px-4 text-sm">
            <Ligne libelle="Pièce" valeur={pieces[dossier.type_piece] ?? dossier.type_piece} />
            <Ligne libelle="Numéro de pièce" valeur={dossier.numero_piece} />
            <Ligne
              libelle="Mobile Money"
              valeur={telephoneLisible(dossier.numero_mobile_money)}
            />
            <Ligne libelle="Commerce" valeur={dossier.nom_commerce || "—"} />
            <Ligne libelle="Déposé le" valeur={dateLongue(dossier.depose_le)} />
          </dl>

          {dossier.lien_recto ? (
            <img
              src={dossier.lien_recto}
              alt="Pièce d'identité"
              className="w-full rounded-2xl border"
            />
          ) : (
            <p className="surface-douce rounded-xl px-3 py-2 text-xs texte-doux">
              Démonstration : aucune pièce n'a été téléversée dans cette version.
            </p>
          )}

          <ZoneTexte
            etiquette="Motif (obligatoire en cas de rejet)"
            rows={2}
            placeholder="Pièce illisible, numéro Mobile Money incohérent…"
            value={motif}
            onChange={(evenement) => setMotif(evenement.target.value)}
          />

          <Alerte>{trancher.erreur?.message}</Alerte>

          <div className="flex gap-3">
            <Bouton
              ton="contour"
              pleineLargeur
              icone={<ShieldX className="size-4" />}
              chargement={trancher.envoi}
              onClick={() => void trancher.lancer("rejeter")}
            >
              Rejeter
            </Bouton>
            <Bouton
              pleineLargeur
              icone={<BadgeCheck className="size-4" />}
              chargement={trancher.envoi}
              onClick={() => void trancher.lancer("valider")}
            >
              Valider
            </Bouton>
          </div>

          <p className="texte-doux text-xs">
            Valider ouvre l'espace groupeur et affiche le badge de confiance sur
            toutes ses campagnes.
          </p>
        </div>
      )}
    </Feuille>
  );
}

function Ligne({ libelle, valeur }: { libelle: string; valeur: string }) {
  return (
    <div className="flex justify-between gap-4 py-2.5">
      <dt className="texte-doux">{libelle}</dt>
      <dd className="text-right font-medium">{valeur}</dd>
    </div>
  );
}
