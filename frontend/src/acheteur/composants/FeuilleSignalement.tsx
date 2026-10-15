import { useState } from "react";
import {
  MOTIFS_DE_SIGNALEMENT,
  type MotifDeSignalement,
  signalerUneQuestion,
} from "../../api/campagnes";
import { ErreurApi } from "../../api/client";
import Bouton from "../../ui/Bouton";
import Encart from "../../ui/Encart";
import FeuilleRemontante from "../../ui/FeuilleRemontante";

/**
 * Signaler un message public. §15, niveau 3 — l'humain, apres publication.
 *
 * ## Ce que ce niveau repare
 *
 * Le §15 pose trois niveaux de moderation. Les deux premiers sont
 * automatiques — le filtre de `domaine/moderation.ts` cote client, et
 * `moderation.verifier` cote serveur, qui tient meme contre un appel direct a
 * l'API. Le troisieme est un humain, **apres** publication, et c'est celui
 * qui attrape ce qu'une liste de motifs ne peut pas attraper : un numero
 * ecrit en lettres, une invitation a traiter en dehors de la plateforme
 * formulee sans aucun mot suspect.
 *
 * L'icone de drapeau existait sur chaque message et **n'allait nulle part**.
 * Le niveau 3 n'avait donc aucun moyen d'etre saisi : un message qui passe le
 * filtre et qu'un lecteur voit pourtant comme un contournement restait en
 * ligne sans recours.
 *
 * ## ⚠️ Trois motifs, et pas de champ libre
 *
 * C'est la regle du §15, et sa raison est concrete : un champ libre
 * contiendrait au bout de six mois quarante formulations du meme probleme. On
 * ne saurait plus **quoi** le filtre automatique laisse passer, donc plus quoi
 * corriger dans `moderation.ts`. La file de moderation doit rester comptable.
 *
 * ## ⚠️ Et le message reste en ligne
 *
 * On ne promet pas une suppression, on promet un examen. Depublier sur
 * signalement donnerait a n'importe qui le pouvoir de faire taire n'importe
 * qui — il suffirait de signaler la question genante pour l'effacer du seul
 * canal public du produit. L'ecran doit donc dire la verite sur ce qui va se
 * passer, sans quoi le signalant revient verifier et croit que rien n'a
 * marche.
 */
export default function FeuilleSignalement({
  question,
  onFermer,
  onSeConnecter,
}: {
  /** L'identifiant du message signale. */
  question: string;
  onFermer: () => void;
  /** Signaler demande un compte, comme poser une question (§1.5). */
  onSeConnecter: () => void;
}) {
  const [motif, setMotif] = useState<MotifDeSignalement>();
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState<string>();
  const [envoye, setEnvoye] = useState(false);

  const envoyer = async () => {
    if (motif === undefined) {
      return;
    }
    setEnvoi(true);
    setErreur(undefined);
    try {
      await signalerUneQuestion(question, motif);
      setEnvoye(true);
    } catch (cause) {
      /* 401 : la session a expire entre l'ouverture de la feuille et l'envoi.
         On ouvre la connexion plutot que d'afficher une erreur — c'est la
         meme regle qu'a l'envoi d'une question (§1.5). */
      if (cause instanceof ErreurApi && cause.statut === 401) {
        onFermer();
        onSeConnecter();
        return;
      }
      setErreur(
        cause instanceof ErreurApi
          ? cause.message
          : "Le signalement n'a pas pu être envoyé. Réessayez.",
      );
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <FeuilleRemontante titre="Signaler ce message" onFermer={onFermer}>
      {envoye ? (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-texte">
            Votre signalement est enregistré
          </h2>
          {/* ⚠️ On dit exactement ce qui va se passer : un examen, pas une
              suppression. Promettre le retrait du message et le laisser en
              ligne ferait revenir le signalant pour rien. */}
          <p className="text-texte-secondaire">
            Group Achat examine ce message. Il reste visible le temps de cet
            examen.
          </p>
          <Bouton onClick={onFermer}>Fermer</Bouton>
        </div>
      ) : (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-texte">
            Signaler ce message
          </h2>

          <fieldset className="space-y-2">
            <legend className="text-sm text-texte-secondaire">
              Pourquoi signalez-vous ce message ?
            </legend>
            {MOTIFS_DE_SIGNALEMENT.map((choix) => (
              <label
                key={choix.cle}
                className={`flex min-h-12 cursor-pointer items-center gap-3 rounded-[10px] border px-3 text-sm ${
                  motif === choix.cle
                    ? "border-2 border-primaire bg-primaire-fond text-primaire-texte-sur-fond"
                    : "border-bordure-champ text-texte"
                }`}
              >
                <input
                  type="radio"
                  name="motif-du-signalement"
                  value={choix.cle}
                  checked={motif === choix.cle}
                  onChange={() => setMotif(choix.cle)}
                  className="size-4 accent-primaire"
                />
                {choix.libelle}
              </label>
            ))}
          </fieldset>

          {erreur ? <Encart variante="attention">{erreur}</Encart> : null}

          {/* Desactive sans motif : les trois motifs **sont** le formulaire,
              et envoyer sans choix ne voudrait rien dire pour la file. */}
          <Bouton onClick={envoyer} desactive={motif === undefined || envoi}>
            {envoi ? "Envoi…" : "Signaler"}
          </Bouton>
        </div>
      )}
    </FeuilleRemontante>
  );
}
