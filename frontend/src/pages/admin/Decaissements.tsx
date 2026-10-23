import { motion } from "framer-motion";
import { Banknote, Check, EyeOff, MessageSquareWarning, RotateCcw } from "lucide-react";
import { useState } from "react";

import type { Commentaire, Decaissement, Page } from "@/api/types";
import {
  Alerte,
  Avatar,
  Bouton,
  Carte,
  Etiquette,
  EtatVide,
  Squelette,
} from "@/composants/ui";
import { dateLongue, depuis, francs, telephoneLisible } from "@/outils/formats";
import { api, useAction, useRequete } from "@/outils/requetes";

/**
 * La libération des fonds.
 *
 * L'administrateur détient l'argent des acheteurs ; c'est lui qui le verse au
 * groupeur une fois la campagne financée. Chaque versement est tracé avec son
 * auteur.
 */
export default function Decaissements() {
  const { donnees, chargement, recharger } = useRequete<Page<Decaissement>>(
    "/admin/decaissements/",
  );
  const [encours, setEncours] = useState<number | null>(null);

  const executer = useAction(async (identifiant: number) => {
    setEncours(identifiant);
    try {
      await api.post(`/admin/decaissements/${identifiant}/executer/`);
      await recharger();
    } finally {
      setEncours(null);
    }
  });

  const demandes = donnees?.results ?? [];
  const aTraiter = demandes.filter((item) => item.statut === "demande");
  const faits = demandes.filter((item) => item.statut !== "demande");

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold">Décaissements</h1>
        <p className="texte-doux text-sm">
          Libérez les fonds du séquestre vers le Mobile Money des groupeurs.
        </p>
      </header>

      <Alerte>{executer.erreur?.message}</Alerte>

      {chargement ? (
        <div className="space-y-3">
          <Squelette className="h-28" />
          <Squelette className="h-28" />
        </div>
      ) : demandes.length === 0 ? (
        <EtatVide
          icone={<Banknote className="size-7" />}
          titre="Aucune demande"
          texte="Les groupeurs demandent leurs fonds une fois leur campagne financée."
        />
      ) : (
        <>
          {aTraiter.length > 0 && (
            <section className="space-y-3">
              <h2 className="font-bold">À libérer ({aTraiter.length})</h2>
              {aTraiter.map((demande, rang) => (
                <LigneDecaissement
                  key={demande.id}
                  demande={demande}
                  index={rang}
                  action={
                    <Bouton
                      chargement={encours === demande.id}
                      onClick={() => void executer.lancer(demande.id)}
                    >
                      Libérer {francs(demande.montant_net)}
                    </Bouton>
                  }
                />
              ))}
            </section>
          )}

          {faits.length > 0 && (
            <section className="space-y-3">
              <h2 className="font-bold">Historique</h2>
              {faits.map((demande, rang) => (
                <LigneDecaissement key={demande.id} demande={demande} index={rang} />
              ))}
            </section>
          )}
        </>
      )}
    </div>
  );
}

function LigneDecaissement({
  demande,
  index,
  action,
}: {
  demande: Decaissement;
  index: number;
  action?: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index, 8) * 0.05 }}
    >
      <Carte className="flex flex-wrap items-center gap-4">
        <div className="min-w-0 flex-1">
          <p className="font-bold">{demande.campagne_titre}</p>
          <p className="texte-doux text-sm">
            {demande.groupeur} · {telephoneLisible(demande.numero_mobile_money)}
          </p>
          <p className="texte-doux tabulaire text-xs">
            Demandé le {dateLongue(demande.demande_le)}
            {demande.execute_le && ` · versé le ${dateLongue(demande.execute_le)}`}
          </p>
        </div>

        <div className="tabulaire text-right text-sm">
          <p className="texte-doux">
            Brut {francs(demande.montant_brut)} − frais {francs(demande.frais)}
          </p>
          <p className="text-lg font-extrabold text-[color:var(--color-accent)]">
            {francs(demande.montant_net)}
          </p>
        </div>

        {action ?? (
          <Etiquette ton={demande.statut === "execute" ? "succes" : "danger"}>
            {demande.statut === "execute" ? (
              <>
                <Check className="size-3" />
                Versé
              </>
            ) : (
              "Refusé"
            )}
          </Etiquette>
        )}
      </Carte>
    </motion.div>
  );
}

// ── Modération du fil ──────────────────────────────────────────────────────

export function Moderation() {
  const [masques, setMasques] = useState(false);
  const { donnees, chargement, recharger } = useRequete<Page<Commentaire>>(
    `/admin/commentaires/${masques ? "?masques=1" : ""}`,
    [masques],
  );

  const basculer = useAction(async (entree: { id: number; masquer: boolean }) => {
    await api.post(
      `/admin/commentaires/${entree.id}/${entree.masquer ? "masquer" : "retablir"}/`,
      entree.masquer ? { motif: "Contraire aux règles de la plateforme" } : {},
    );
    await recharger();
  });

  const messages = donnees?.results ?? [];

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-extrabold">Modération</h1>
        <p className="texte-doux text-sm">
          Un message retiré est <strong>masqué, jamais supprimé</strong> : la trace
          reste en cas de contestation.
        </p>
      </header>

      <div className="flex gap-2">
        {(
          [
            [false, "Fil public"],
            [true, "Messages masqués"],
          ] as const
        ).map(([valeur, libelle]) => (
          <button
            key={String(valeur)}
            onClick={() => setMasques(valeur)}
            className={
              masques === valeur
                ? "degrade-accent rounded-full px-4 py-2 text-sm font-semibold text-white"
                : "surface rounded-full px-4 py-2 text-sm font-semibold"
            }
          >
            {libelle}
          </button>
        ))}
      </div>

      <Alerte>{basculer.erreur?.message}</Alerte>

      {chargement ? (
        <div className="space-y-3">
          <Squelette className="h-20" />
          <Squelette className="h-20" />
        </div>
      ) : messages.length === 0 ? (
        <EtatVide
          icone={<MessageSquareWarning className="size-7" />}
          titre={masques ? "Aucun message masqué" : "Le fil est vide"}
          texte={
            masques
              ? "Rien n'a été retiré du fil public."
              : "Les questions des acheteurs apparaîtront ici."
          }
        />
      ) : (
        <ul className="space-y-3">
          {messages.map((message, rang) => (
            <motion.li
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(rang, 8) * 0.04 }}
            >
              <Carte className="flex gap-3">
                <Avatar nom={message.auteur.nom_affiche} taille={38} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm">
                    <strong>{message.auteur.nom_affiche}</strong>{" "}
                    <span className="texte-doux">· {depuis(message.cree_le)}</span>
                  </p>
                  <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed">
                    {message.texte}
                  </p>
                </div>
                <Bouton
                  ton={masques ? "contour" : "fantome"}
                  taille="sm"
                  icone={
                    masques ? <RotateCcw className="size-4" /> : <EyeOff className="size-4" />
                  }
                  chargement={basculer.envoi}
                  onClick={() =>
                    void basculer.lancer({ id: message.id, masquer: !masques })
                  }
                >
                  {masques ? "Rétablir" : "Masquer"}
                </Bouton>
              </Carte>
            </motion.li>
          ))}
        </ul>
      )}
    </div>
  );
}
