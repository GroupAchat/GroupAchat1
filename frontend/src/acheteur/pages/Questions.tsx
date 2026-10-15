import { useMemo, useState } from "react";
import Vignette from "../../composants/Vignette";
import { QUESTIONS_COURANTES, type Question } from "../../domaine/demande";
import { formaterDateCourte } from "../../domaine/format";
import type { Groupage } from "../../domaine/groupage";
import { expliquer, verifier } from "../../domaine/moderation";
import {
  adapterQuestion,
  listerLesQuestions,
  poserUneQuestion,
} from "../../api/campagnes";
import { useAction, useRequete } from "../../api/useRequete";
import EnTeteEcran from "../mise-en-page/EnTeteEcran";
import PiedPage from "../mise-en-page/PiedPage";
import Bouton from "../../ui/Bouton";
import Encart from "../../ui/Encart";
import EtatVide from "../../ui/EtatVide";
import { IconeDrapeau, IconeQuestion } from "../../ui/Icones";
import FeuilleSignalement from "../composants/FeuilleSignalement";

/**
 * Ecran 10 — Questions sur un groupage. SPEC_ECRANS_FIGMA.md, ecran 10.
 *
 * **Objectif : obtenir une information manquante sans jamais sortir de la
 * plateforme.** C'est ce qui rend l'anonymat du groupeur supportable : sans ce
 * canal, un acheteur qui a une question n'aurait d'autre choix que de chercher
 * a joindre le groupeur ailleurs, et tout le modele s'effondre.
 *
 * **Les questions courantes viennent avant le champ libre**, et c'est une
 * mesure de securite autant qu'un confort (§14.2 du cahier des charges) : la
 * plupart des questions legitimes n'ont alors aucun texte libre, et le texte
 * libre redevient l'exception plutot que la regle.
 *
 * **Le filtre previent avant l'envoi, jamais apres.** Des que la saisie
 * declenche la detection, « Envoyer » passe en desactive et l'encart apparait.
 * L'utilisateur n'a donc pas a echouer pour apprendre. Le message **reste dans
 * le champ**, modifiable, et le passage en cause est montre : il voit
 * exactement quoi corriger. Les deux choses arrivent **en meme temps** — le
 * message n'est pas publie, et son auteur sait pourquoi. Jamais l'un sans
 * l'autre : pas de blocage silencieux, pas de message qui part et disparait.
 *
 * La redaction de l'encart est dictee mot pour mot par la spec et vit dans
 * `domaine/moderation.ts`. **Ne pas la reecrire sans relire le tableau de
 * l'ecran 10** : chaque mot y est justifie.
 *
 * **La connexion est demandee au bouton « Envoyer », pas a l'ouverture** : la
 * lecture est libre (§1.5).
 */
export default function Questions({
  groupage,
  estBureau,
  telephone,
  onRetour,
  onSeConnecter,
  variante = "page",
}: {
  groupage: Groupage;
  estBureau: boolean;
  /** Le numero du compte. **La connexion est demandee a l'envoi** (§1.5). */
  telephone?: string;
  onRetour: () => void;
  onSeConnecter: () => void;
  /**
   * `panneau` rend **le corps seul**, sans en-tete ni pied de page, pour le
   * panneau flottant de `PanneauQuestions`.
   *
   * ⚠️ **Une variante plutot qu'un second composant.** Tout ce qui est
   * delicat ici — le filtre de moderation du §15, la connexion demandee au
   * bouton et non a l'ouverture (§1.5), le refus du serveur affiche sous le
   * champ — n'existe qu'une fois. Un panneau qui reecrirait ce formulaire
   * finirait par laisser passer un numero de telephone que la page, elle,
   * bloque encore.
   */
  variante?: "page" | "panneau";
}) {
  const [brouillon, setBrouillon] = useState("");

  /** Le message dont la feuille de signalement est ouverte (§15, niveau 3). */
  const [signalee, setSignalee] = useState<Question>();

  const requete = useRequete(
    (signal) => listerLesQuestions(groupage.id, signal),
    [groupage.id],
  );

  /* Le serveur trie deja de la plus recente a la plus ancienne (`ordering`
     sur le modele). On ne retrie pas : deux tris a tenir d'accord, c'est un
     tri de trop. */
  const questions = useMemo(
    () =>
      (requete.donnees?.results ?? []).map((brute) =>
        adapterQuestion(brute, groupage.groupeur),
      ),
    [requete.donnees, groupage.groupeur],
  );

  const envoi = useAction(poserUneQuestion);

  /**
   * ⚠️ **Le filtre local ne remplace pas celui du serveur, il le double.**
   *
   * Celui-ci desactive « Envoyer » des la saisie, pour que personne n'ait a
   * echouer pour comprendre (§15). Mais c'est **le serveur qui decide** : un
   * filtre d'interface se contourne en une requete, et c'est le modele de
   * la plateforme qu'il protege. Un refus du serveur s'affiche donc aussi,
   * juste en dessous.
   */
  const verdict = verifier(brouillon);
  const bloque = brouillon.trim() !== "" && !verdict.publiable;
  const explication = verdict.motif ? expliquer(verdict.motif) : undefined;

  const envoyer = async () => {
    /* La connexion est demandee **au bouton**, pas a l'ouverture : lire les
       questions des autres ne demande aucun compte. */
    if (!telephone) {
      onSeConnecter();
      return;
    }
    const posee = await envoi.executer({
      campagne: groupage.id,
      texte: brouillon.trim(),
    });
    if (posee) {
      setBrouillon("");
      requete.recharger();
    }
  };

  const corps = (
    <div className="space-y-6">
      {/* Rappel du groupage : on sait toujours sur quoi on pose la question. */}
      <div className="flex items-center gap-3">
        <Vignette photo={groupage.photo} alt={groupage.photoAlt} taille={48} />
        <p className="min-w-0 font-medium text-texte">{groupage.produit}</p>
      </div>

      {/*
        Les questions courantes, avant le champ libre.

        ⚠️ **Un appui remplit le champ, il n'envoie pas.** Le commentaire
        d'origine disait l'inverse de ce que fait le code, et c'est le code qui
        a raison : publier d'un seul appui une question qu'on a effleurée par
        erreur est irrattrapable — elle est publique, et elle porte le
        pseudonyme de son auteur. On remplit, il relit, il envoie.
      */}
      <section>
        <h2 className="text-sm font-medium text-texte-secondaire">
          Questions courantes
        </h2>
        <div className="defilement-discret -mx-4 mt-2 flex gap-2 overflow-x-auto px-4">
          {QUESTIONS_COURANTES.map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => setBrouillon(question)}
              className="inline-flex min-h-12 shrink-0 items-center rounded-full border border-bordure px-4 text-sm font-medium whitespace-nowrap text-texte active:bg-surface-douce"
            >
              {question}
            </button>
          ))}
          {/* ⚠️ Ce bouton n'avait **aucun `onClick`** : il ne faisait rien.
              Son role est d'amener au champ libre, donc il y amene — et il
              vide le brouillon, sinon appuyer dessus apres avoir choisi une
              question courante laisserait le texte de celle-ci dans le
              champ. */}
          <button
            type="button"
            onClick={() => {
              setBrouillon("");
              document.getElementById("question")?.focus();
            }}
            className="inline-flex min-h-12 shrink-0 items-center rounded-full border border-bordure px-4 text-sm font-medium whitespace-nowrap text-texte active:bg-surface-douce"
          >
            Autre question
          </button>
        </div>
      </section>

      {/* Le champ libre. */}
      <section>
        <label
          htmlFor="question"
          className="block text-sm font-medium text-texte"
        >
          Votre question
        </label>
        <textarea
          id="question"
          rows={2}
          value={brouillon}
          onChange={(evenement) => setBrouillon(evenement.target.value)}
          placeholder="Posez votre question sur ce produit…"
          aria-invalid={bloque || undefined}
          aria-describedby="mention-publique"
          className={`mt-1.5 w-full resize-none rounded-[10px] border bg-white px-3 py-2.5 outline-none placeholder:text-texte-secondaire ${
            bloque
              ? "border-danger bg-danger-fond"
              : "border-bordure focus:border-2 focus:border-primaire"
          }`}
        />

        {/* A lire avant d'ecrire, pas apres. */}
        <p id="mention-publique" className="mt-1 text-xs text-texte-secondaire">
          Votre question et la réponse seront visibles par tout le monde.
        </p>

        {bloque && explication ? (
          <div className="mt-3 space-y-3">
            <Encart variante="danger" titre={explication.titre}>
              {explication.corps}
            </Encart>

            {verdict.passage ? (
              <p className="text-xs text-texte-secondaire">
                Passage en cause :{" "}
                <mark className="rounded bg-danger-fond px-1 text-danger">
                  {verdict.passage}
                </mark>
              </p>
            ) : null}

            {explication.rassurance ? (
              <p className="text-sm text-texte-secondaire italic">
                {explication.rassurance}
              </p>
            ) : null}
          </div>
        ) : null}

        {/* Le refus du serveur, s'il a vu ce que le filtre local a laisse
            passer — par exemple un numero ecrit en lettres, que seul le
            niveau 2 du §15 attrape. */}
        {envoi.erreur ? (
          <p role="alert" className="mt-3 text-sm font-medium text-danger">
            {envoi.erreur.estRefusDeSaisie
              ? Object.values(envoi.erreur.champs)[0]?.[0]
              : envoi.erreur.messageLisible}
          </p>
        ) : null}

        <div className="mt-3 flex gap-3">
          <Bouton
            desactive={bloque || brouillon.trim() === ""}
            chargement={envoi.enCours}
            onClick={envoyer}
          >
            {bloque ? "Modifier votre message" : "Envoyer"}
          </Bouton>
          {bloque ? (
            <Bouton style="secondaire" onClick={() => setBrouillon("")}>
              Annuler
            </Bouton>
          ) : null}
        </div>
      </section>

      {/* La liste, la plus recente en haut. */}
      <section>
        <h2 className="text-lg font-semibold text-texte">
          {questions.length} question{questions.length > 1 ? "s" : ""}
        </h2>

        {questions.length === 0 ? (
          <EtatVide
            titre="Aucune question pour le moment"
            explication="Soyez le premier à poser une question sur ce groupage."
            actionLibelle="Poser une question"
            registre="attente"
            onAction={() => document.getElementById("question")?.focus()}
          />
        ) : (
          <ul className="mt-3 space-y-5">
            {questions.map((question) => (
              <FilQuestion
                key={question.id}
                question={question}
                onSignaler={setSignalee}
              />
            ))}
          </ul>
        )}
      </section>

      {signalee !== undefined ? (
        <FeuilleSignalement
          question={signalee.id}
          onFermer={() => setSignalee(undefined)}
          onSeConnecter={onSeConnecter}
        />
      ) : null}

      {/* A dessiner, pas a sous-entendre (§1.7). */}
      <Encart variante="attention">
        N&apos;échangez jamais de numéro de téléphone. Votre paiement
        n&apos;est protégé que sur Group Achat.
      </Encart>
    </div>
  );

  if (variante === "panneau") return corps;

  if (estBureau) {
    return (
      <>
        <div className="mx-auto max-w-3xl px-4 py-8 lg:px-8">
          <h1 className="mb-6 text-2xl font-semibold text-texte lg:text-3xl">
            Questions
          </h1>
          {corps}
        </div>
        <PiedPage />
      </>
    );
  }

  return (
    <div className="pb-10">
      <EnTeteEcran titre="Questions" onRetour={onRetour} />
      <div className="px-4 pt-5">{corps}</div>
    </div>
  );
}

/** Une question et sa reponse. */
function FilQuestion({
  question,
  onSignaler,
}: {
  question: Question;
  /**
   * Ouvre la feuille de signalement (§15, niveau 3).
   *
   * ⚠️ **Tenu par l'ecran, pas par la ligne.** Une feuille par message
   * donnerait autant de voiles superposes qu'il y a de questions, et il n'y
   * en a qu'une d'ouverte a la fois de toute facon.
   */
  onSignaler: (question: Question) => void;
}) {
  return (
    <li>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-texte">{question.texte}</p>
          <p className="mt-0.5 text-xs text-texte-secondaire">
            {question.auteur}
            <span aria-hidden="true"> · </span>
            {formaterDateCourte(question.poseeLe)}
          </p>
        </div>

        {/* Signalement : une icone discrete, pas un bouton qui attire. */}
        <button
          type="button"
          onClick={() => onSignaler(question)}
          aria-label="Signaler ce message"
          className="flex size-10 shrink-0 items-center justify-center text-texte-secondaire"
        >
          <IconeDrapeau taille={16} />
        </button>
      </div>

      {question.etat === "en-verification" ? (
        <p className="mt-2 inline-flex h-6 items-center rounded-full bg-surface-douce px-2.5 text-xs font-medium text-texte-secondaire">
          En vérification — visible de vous seul
        </p>
      ) : null}

      {question.reponse ? (
        /* Le gris separe deux voix, donc il informe : c'est l'un des trois
           usages autorises de `surface-douce` (§1.2). */
        <div className="mt-2 ml-4 rounded-xl bg-surface-douce p-3">
          <p className="text-xs font-semibold text-texte">
            {question.reponse.auteur}
            <span className="ml-1.5 font-normal text-texte-secondaire">
              {formaterDateCourte(question.reponse.repondueLe)}
            </span>
          </p>
          <p className="mt-1 text-sm text-texte-secondaire">
            {question.reponse.texte}
          </p>
        </div>
      ) : (
        <p className="mt-2 ml-4 inline-flex h-6 items-center gap-1.5 rounded-full bg-surface-douce px-2.5 text-xs font-medium text-texte-secondaire">
          <IconeQuestion taille={13} />
          En attente de réponse
        </p>
      )}
    </li>
  );
}
