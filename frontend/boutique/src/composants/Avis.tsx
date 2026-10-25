import { motion } from "framer-motion";
import { BadgeCheck, Star } from "lucide-react";
import { useState } from "react";

import type { Avis, Page, Participation } from "@commun/api/types";
import {
  Avatar,
  Bouton,
  Carte,
  EtatVide,
  fusionner,
  Squelette,
  ZoneTexte,
} from "@commun/composants/ui";
import { depuis } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/**
 * Les avis : ce qui remplace l'arbitrage.
 *
 * Group Achat met en relation, elle ne tranche pas les désaccords sur la
 * marchandise. Un acheteur mécontent en parle au groupeur sous la campagne
 * et le note ici ; c'est sa réputation qui en porte la trace, visible par
 * tous les acheteurs suivants.
 */

const TAILLES = { sm: "size-3.5", md: "size-5", lg: "size-7" } as const;

/** Cinq étoiles, en lecture seule. */
export function Etoiles({
  note,
  taille = "sm",
  className,
}: {
  note: number;
  taille?: keyof typeof TAILLES;
  className?: string;
}) {
  return (
    <span className={fusionner("inline-flex items-center gap-0.5", className)}>
      {[1, 2, 3, 4, 5].map((rang) => (
        <Star
          key={rang}
          className={fusionner(
            TAILLES[taille],
            rang <= Math.round(note)
              ? "text-[color:var(--color-mangue-500)]"
              : "texte-doux opacity-35",
          )}
          fill={rang <= Math.round(note) ? "currentColor" : "none"}
          aria-hidden
        />
      ))}
      <span className="sr-only">{note} sur 5</span>
    </span>
  );
}

/** Les mêmes étoiles, mais on clique dessus. */
function ChoixEtoiles({
  note,
  surChoix,
}: {
  note: number;
  surChoix: (note: number) => void;
}) {
  // Le survol montre la note qu'on s'apprête à donner : sans cela, sur un
  // écran tactile comme à la souris, on clique un peu au hasard.
  const [survol, setSurvol] = useState(0);
  const affichee = survol || note;

  return (
    <div className="flex items-center gap-1" onMouseLeave={() => setSurvol(0)}>
      {[1, 2, 3, 4, 5].map((rang) => (
        <button
          key={rang}
          type="button"
          onClick={() => surChoix(rang)}
          onMouseEnter={() => setSurvol(rang)}
          className="rounded-full p-1 transition-transform hover:scale-110 active:scale-95"
          aria-label={`${rang} étoile${rang > 1 ? "s" : ""}`}
          aria-pressed={note === rang}
        >
          <Star
            className={fusionner(
              "size-7 transition-colors",
              rang <= affichee
                ? "text-[color:var(--color-mangue-500)]"
                : "texte-doux opacity-35",
            )}
            fill={rang <= affichee ? "currentColor" : "none"}
          />
        </button>
      ))}
    </div>
  );
}

const LIBELLES = [
  "",
  "Très mauvaise expérience",
  "Décevant",
  "Correct",
  "Bien",
  "Excellent groupeur",
];

/**
 * Le formulaire de note, sur le détail d'une commande.
 *
 * Il n'apparaît qu'une fois la collecte close : avant, le groupage n'a rien
 * montré et la note ne voudrait rien dire. Après, il y a toujours quelque
 * chose à dire — y compris quand rien n'a été livré.
 */
export function FormulaireAvis({
  participation,
  surChangement,
}: {
  participation: Participation;
  surChangement: () => void;
}) {
  const existant = participation.avis;
  const [note, setNote] = useState(existant?.note ?? 0);
  const [commentaire, setCommentaire] = useState(existant?.commentaire ?? "");
  const [edition, setEdition] = useState(!existant);

  const envoi = useAction(async () => {
    if (existant) {
      await api.patch(`/avis/${existant.id}/`, { note, commentaire });
    } else {
      await api.post("/avis/", {
        participation: participation.id,
        note,
        commentaire,
      });
    }
    setEdition(false);
    surChangement();
  });

  if (!participation.peut_etre_notee && !existant) return null;

  if (existant && !edition) {
    return (
      <Carte className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-semibold">Votre avis</p>
          <button
            type="button"
            onClick={() => setEdition(true)}
            className="texte-doux text-xs font-semibold"
          >
            Modifier
          </button>
        </div>
        <Etoiles note={existant.note} taille="md" />
        {existant.commentaire && (
          <p className="whitespace-pre-wrap text-[0.95rem] leading-relaxed">
            {existant.commentaire}
          </p>
        )}
        {existant.reponse && <ReponseGroupeur avis={existant} />}
      </Carte>
    );
  }

  return (
    <Carte className="space-y-4">
      <div>
        <p className="font-bold">
          {existant ? "Modifier votre avis" : "Comment s'est passé ce groupage ?"}
        </p>
        <p className="texte-doux text-sm">
          Votre note est publique et compte dans la réputation du groupeur.
        </p>
      </div>

      <div className="space-y-1">
        <ChoixEtoiles note={note} surChoix={setNote} />
        {note > 0 && (
          <p className="texte-doux px-1 text-sm font-medium">{LIBELLES[note]}</p>
        )}
      </div>

      <ZoneTexte
        etiquette="Votre commentaire (facultatif)"
        rows={3}
        maxLength={1000}
        value={commentaire}
        onChange={(evenement) => setCommentaire(evenement.target.value)}
        placeholder="Délais tenus ? Marchandise conforme ? Dites-le aux prochains acheteurs."
      />

      {envoi.erreur && <p className="text-sm text-red-600">{envoi.erreur.message}</p>}

      <div className="flex gap-2">
        <Bouton
          onClick={() => void envoi.lancer(undefined as never)}
          disabled={note === 0}
          chargement={envoi.envoi}
        >
          {existant ? "Enregistrer" : "Publier mon avis"}
        </Bouton>
        {existant && (
          <Bouton
            ton="contour"
            onClick={() => {
              setNote(existant.note);
              setCommentaire(existant.commentaire);
              setEdition(false);
            }}
          >
            Annuler
          </Bouton>
        )}
      </div>
    </Carte>
  );
}

/**
 * Les avis reçus par le groupeur connecté, avec son droit de réponse.
 *
 * Il ne peut ni les supprimer ni les contester auprès de la plateforme — il
 * n'y a personne à saisir. Ce qu'il peut, c'est répondre publiquement une
 * fois, sous l'avis, et faire remonter sa moyenne avec les suivants.
 */
export function AvisRecus({ groupeurId }: { groupeurId: number }) {
  const { donnees, chargement, recharger } = useRequete<Page<Avis>>(
    `/avis/?groupeur=${groupeurId}`,
  );
  const avis = donnees?.results ?? [];

  if (chargement) return <Squelette className="h-24" />;
  if (avis.length === 0) return null;

  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        <Star className="size-5" />
        Avis reçus
        <span className="texte-doux text-sm font-normal">({avis.length})</span>
      </h2>
      <ul className="space-y-3">
        {avis.map((un) => (
          <li key={un.id}>
            <Carte className="space-y-3">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <Etoiles note={un.note} />
                <span className="font-semibold">{un.auteur.nom_affiche}</span>
                <span className="texte-doux text-xs">{depuis(un.cree_le)}</span>
                <span className="texte-doux ml-auto truncate text-xs">
                  {un.campagne_titre}
                </span>
              </div>
              {un.commentaire && (
                <p className="whitespace-pre-wrap text-[0.95rem] leading-relaxed">
                  {un.commentaire}
                </p>
              )}
              {un.reponse ? (
                <ReponseGroupeur avis={un} />
              ) : (
                <ChampReponse avis={un} surEnvoi={recharger} />
              )}
            </Carte>
          </li>
        ))}
      </ul>
    </section>
  );
}

function ChampReponse({ avis, surEnvoi }: { avis: Avis; surEnvoi: () => void }) {
  const [texte, setTexte] = useState("");
  const envoi = useAction(async (contenu: string) => {
    await api.post(`/avis/${avis.id}/repondre/`, { reponse: contenu });
    setTexte("");
    surEnvoi();
  });

  return (
    <form
      onSubmit={(evenement) => {
        evenement.preventDefault();
        if (texte.trim()) void envoi.lancer(texte.trim());
      }}
      className="space-y-2"
    >
      <ZoneTexte
        etiquette="Votre réponse (publique, une seule fois)"
        rows={2}
        maxLength={1000}
        value={texte}
        onChange={(evenement) => setTexte(evenement.target.value)}
        placeholder="Expliquez ce qui s'est passé — les prochains acheteurs le liront."
      />
      {envoi.erreur && <p className="text-sm text-red-600">{envoi.erreur.message}</p>}
      <Bouton type="submit" taille="sm" chargement={envoi.envoi} disabled={!texte.trim()}>
        Répondre
      </Bouton>
    </form>
  );
}

function ReponseGroupeur({ avis }: { avis: Avis }) {
  return (
    <div className="bg-accent-doux rounded-2xl px-4 py-3">
      <p className="mb-1 flex items-center gap-1.5 text-xs font-bold">
        <BadgeCheck className="size-3.5" />
        Réponse du groupeur
        {avis.repondu_le && (
          <span className="texte-doux font-normal">{depuis(avis.repondu_le)}</span>
        )}
      </p>
      <p className="whitespace-pre-wrap text-[0.95rem] leading-relaxed">
        {avis.reponse}
      </p>
    </div>
  );
}

/**
 * Les avis reçus par un groupeur, sous sa campagne.
 *
 * On les montre **avant** l'achat, pas après : c'est là qu'ils servent. Un
 * acheteur qui hésite doit pouvoir lire ce que les précédents ont vécu.
 */
export function ListeAvis({ groupeurId }: { groupeurId: number }) {
  const { donnees, chargement } = useRequete<Page<Avis>>(`/avis/?groupeur=${groupeurId}`);
  const avis = donnees?.results ?? [];

  if (chargement) {
    return (
      <div className="space-y-3">
        <Squelette className="h-20" />
        <Squelette className="h-20" />
      </div>
    );
  }

  if (avis.length === 0) {
    return (
      <EtatVide
        icone={<Star className="size-7" />}
        titre="Pas encore d'avis"
        texte="Ce groupeur n'a pas encore été noté. Les participants pourront le faire à la clôture de la collecte."
      />
    );
  }

  const moyenne = avis.reduce((somme, un) => somme + un.note, 0) / avis.length;

  return (
    <div className="space-y-4">
      <div className="surface-douce flex items-center gap-4 rounded-2xl p-4">
        <p className="tabulaire text-3xl font-extrabold">{moyenne.toFixed(1)}</p>
        <div>
          <Etoiles note={moyenne} taille="md" />
          <p className="texte-doux text-sm">
            {avis.length} avis d'acheteurs de ce groupeur
          </p>
        </div>
      </div>

      <ul className="space-y-4">
        {avis.map((un, rang) => (
          <motion.li
            key={un.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(rang, 6) * 0.04 }}
            className="flex gap-3"
          >
            <Avatar nom={un.auteur.nom_affiche} taille={38} />
            <div className="min-w-0 flex-1 space-y-2">
              <div className="surface-douce rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="mb-1 flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-semibold">{un.auteur.nom_affiche}</span>
                  <Etoiles note={un.note} />
                  <span className="texte-doux text-xs">{depuis(un.cree_le)}</span>
                </div>
                {un.commentaire ? (
                  <p className="whitespace-pre-wrap text-[0.95rem] leading-relaxed">
                    {un.commentaire}
                  </p>
                ) : (
                  <p className="texte-doux text-sm italic">Noté sans commentaire.</p>
                )}
                <p className="texte-doux mt-1.5 text-xs">{un.campagne_titre}</p>
              </div>
              {un.reponse && <ReponseGroupeur avis={un} />}
            </div>
          </motion.li>
        ))}
      </ul>
    </div>
  );
}
