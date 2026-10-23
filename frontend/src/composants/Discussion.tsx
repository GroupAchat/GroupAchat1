import { AnimatePresence, motion } from "framer-motion";
import { BadgeCheck, Heart, MessageCircle, Send } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import type { Commentaire, Page } from "@/api/types";
import { Avatar, Bouton, EtatVide, fusionner, Squelette } from "@/composants/ui";
import { useSession } from "@/contexte/Session";
import { depuis } from "@/outils/formats";
import { api, useAction, useRequete } from "@/outils/requetes";

/**
 * Le fil de discussion sous une campagne.
 *
 * Tout le monde le lit, **y compris sans compte** : c'est lui qui rassure
 * l'acheteur hésitant, et le cacher derrière une inscription le priverait de
 * sa raison d'être. Écrire demande un numéro vérifié.
 */
export function Discussion({ campagneId }: { campagneId: number }) {
  const { peutAgir } = useSession();
  const chemin = `/campagnes/${campagneId}/commentaires/`;
  const { donnees, chargement, recharger } = useRequete<Page<Commentaire>>(chemin);
  const [texte, setTexte] = useState("");
  const [repondA, setRepondA] = useState<Commentaire | null>(null);

  const publication = useAction(async (contenu: string) => {
    await api.post(chemin, { texte: contenu, reponse_a: repondA?.id ?? null });
    setTexte("");
    setRepondA(null);
    await recharger();
  });

  const messages = donnees?.results ?? [];

  return (
    <section id="discussion" className="space-y-4 scroll-mt-20">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        <MessageCircle className="size-5" />
        Questions et avis
        {donnees && (
          <span className="texte-doux text-sm font-normal">({donnees.count})</span>
        )}
      </h2>

      {peutAgir ? (
        <form
          onSubmit={(evenement) => {
            evenement.preventDefault();
            if (texte.trim()) void publication.lancer(texte.trim());
          }}
          className="space-y-2"
        >
          <AnimatePresence>
            {repondA && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="surface-douce flex items-center justify-between gap-2 rounded-xl px-3 py-2 text-sm"
              >
                <span className="truncate">
                  Réponse à <strong>{repondA.auteur.nom_affiche}</strong>
                </span>
                <button
                  type="button"
                  onClick={() => setRepondA(null)}
                  className="texte-doux shrink-0 text-xs font-semibold"
                >
                  Annuler
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="surface flex items-end gap-2 rounded-2xl p-2 focus-within:border-[color:var(--color-accent)]">
            <textarea
              value={texte}
              onChange={(evenement) => setTexte(evenement.target.value)}
              placeholder="Posez votre question au groupeur…"
              rows={1}
              maxLength={1000}
              className="max-h-32 min-h-10 flex-1 resize-none bg-transparent px-2 py-2 text-[0.95rem] outline-none"
            />
            <Bouton
              type="submit"
              taille="sm"
              chargement={publication.envoi}
              disabled={!texte.trim()}
              className="size-10 !px-0"
              aria-label="Publier"
            >
              {!publication.envoi && <Send className="size-4" />}
            </Bouton>
          </div>
          {publication.erreur && (
            <p className="text-sm text-red-600">{publication.erreur.message}</p>
          )}
        </form>
      ) : (
        <div className="surface-douce flex flex-wrap items-center justify-between gap-3 rounded-2xl p-4 text-sm">
          <span className="texte-doux">
            Vérifiez votre numéro pour poser une question.
          </span>
          <Link to="/connexion">
            <Bouton taille="sm">Se connecter</Bouton>
          </Link>
        </div>
      )}

      {chargement ? (
        <div className="space-y-3">
          <Squelette className="h-20" />
          <Squelette className="h-20" />
        </div>
      ) : messages.length === 0 ? (
        <EtatVide
          icone={<MessageCircle className="size-7" />}
          titre="Pas encore de message"
          texte="Posez la première question — le groupeur reçoit une notification."
        />
      ) : (
        <ul className="space-y-4">
          {messages.map((message) => (
            <Message
              key={message.id}
              message={message}
              surReponse={peutAgir ? setRepondA : undefined}
              surChangement={recharger}
              campagneId={campagneId}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

function Message({
  message,
  surReponse,
  surChangement,
  campagneId,
  imbrique,
}: {
  message: Commentaire;
  surReponse?: (message: Commentaire) => void;
  surChangement: () => void;
  campagneId: number;
  imbrique?: boolean;
}) {
  const { peutAgir } = useSession();
  // Optimiste : le cœur réagit tout de suite, l'API confirme derrière. Sur une
  // connexion lente, attendre la réponse donnerait un bouton qui semble mort.
  const [aime, setAime] = useState(message.jaime_par_moi);
  const [compte, setCompte] = useState(message.nombre_jaime);

  const basculer = async () => {
    if (!peutAgir) return;
    const avant = { aime, compte };
    setAime(!aime);
    setCompte(compte + (aime ? -1 : 1));
    try {
      const retour = await api.post<{ jaime_par_moi: boolean; nombre_jaime: number }>(
        `/campagnes/${campagneId}/commentaires/${message.id}/jaime/`,
      );
      setAime(retour.jaime_par_moi);
      setCompte(retour.nombre_jaime);
    } catch {
      setAime(avant.aime);
      setCompte(avant.compte);
    }
  };

  return (
    <motion.li
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={fusionner("flex gap-3", imbrique && "ml-10")}
    >
      <Avatar nom={message.auteur.nom_affiche} taille={imbrique ? 30 : 38} />
      <div className="min-w-0 flex-1">
        <div
          className={fusionner(
            "rounded-2xl rounded-tl-sm px-4 py-3",
            message.est_du_groupeur
              ? "bg-accent-doux"
              : "surface-douce",
          )}
        >
          <div className="mb-1 flex flex-wrap items-center gap-1.5 text-sm">
            <span className="font-semibold">{message.auteur.nom_affiche}</span>
            {message.est_du_groupeur && (
              <span className="flex items-center gap-0.5 rounded-full bg-[color:var(--color-accent)] px-1.5 py-0.5 text-[0.6rem] font-bold text-white">
                <BadgeCheck className="size-2.5" />
                Groupeur
              </span>
            )}
            <span className="texte-doux text-xs">{depuis(message.cree_le)}</span>
          </div>
          <p className="whitespace-pre-wrap text-[0.95rem] leading-relaxed">
            {message.texte}
          </p>
        </div>

        <div className="mt-1.5 flex items-center gap-4 px-1">
          <button
            onClick={basculer}
            disabled={!peutAgir}
            className={fusionner(
              "flex items-center gap-1 text-xs font-semibold transition-colors disabled:opacity-50",
              aime ? "text-[color:var(--color-mangue-500)]" : "texte-doux",
            )}
            aria-pressed={aime}
          >
            <motion.span animate={aime ? { scale: [1, 1.35, 1] } : {}}>
              <Heart className="size-4" fill={aime ? "currentColor" : "none"} />
            </motion.span>
            {compte > 0 && compte}
          </button>
          {surReponse && !imbrique && (
            <button
              onClick={() => surReponse(message)}
              className="texte-doux text-xs font-semibold"
            >
              Répondre
            </button>
          )}
        </div>

        {message.reponses.length > 0 && (
          <ul className="mt-3 space-y-3">
            {message.reponses.map((reponse) => (
              <Message
                key={reponse.id}
                message={reponse}
                surChangement={surChangement}
                campagneId={campagneId}
                imbrique
              />
            ))}
          </ul>
        )}
      </div>
    </motion.li>
  );
}
