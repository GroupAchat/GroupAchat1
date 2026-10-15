import { useState } from "react";
import Vignette from "../../composants/Vignette";
import { formaterDateCourte } from "../../domaine/format";
import { verifier } from "../../domaine/moderation";
import { useEspaceGroupeur } from "../../api/EspaceGroupeurContexte";
import { repondreALaQuestion } from "../../api/espaceGroupeur";
import { useAction } from "../../api/useRequete";
import { EnTeteGroupeur } from "../mise-en-page/ChromeGroupeur";
import Bouton from "../../ui/Bouton";
import Encart from "../../ui/Encart";
import FeuilleRemontante from "../../ui/FeuilleRemontante";
import { IconeBouclier } from "../../ui/Icones";

/**
 * Ecran 20 — Questions recues, cote groupeur. SPEC_ECRANS_FIGMA.md, ecran 20.
 *
 * **Une question sans reponse est une vente qui n'a pas lieu** : c'est
 * pourquoi elle figure dans « A faire aujourd'hui » de l'ecran 13.
 *
 * ⚠️ **C'est le cote risque du fil** (§14.2 du cahier des charges). L'acheteur
 * n'a rien a gagner a sortir de la plateforme ; **le groupeur, si** — il y
 * gagnerait nos frais. Le filtre de `domaine/moderation.ts` s'applique
 * donc a l'identique sur ses reponses, avec deux ajouts :
 *
 * **a) L'avertissement de premiere reponse**, affiche **une seule fois**. Son
 * second paragraphe ne menace pas, **il explique son interet** — « les
 * acheteurs paient sur Group Achat, et c'est ce qui vous garantit d'etre paye
 * a la cloture ». C'est plus efficace qu'un reglement.
 *
 * **b) La copie du refus est plus ferme que cote acheteur**, parce que la
 * bonne foi y est moins probable. On y dit que la tentative est enregistree,
 * ce qu'on ne dit jamais a un acheteur.
 */
type Filtre = "sans-reponse" | "toutes";

export default function QuestionsRecues({ onRetour }: { onRetour: () => void }) {
  const {
    telephone,
    questions: recues,
    campagnes,
    recharger,
  } = useEspaceGroupeur();
  const reponse = useAction(repondreALaQuestion);
  const [filtre, setFiltre] = useState<Filtre>("sans-reponse");
  const [brouillons, setBrouillons] = useState<Record<number, string>>({});
  /** L'avertissement de premiere reponse, affiche une seule fois. */
  const [avertissementVu, setAvertissementVu] = useState(false);
  const [avertissementOuvert, setAvertissementOuvert] = useState(false);

  const sansReponse = recues.filter((q) => !q.reponse);
  const listees = filtre === "sans-reponse" ? sansReponse : recues;

  /** Regroupees par campagne : le groupeur repond campagne par campagne. */
  const parGroupage = new Map<string, typeof listees>();
  for (const question of listees) {
    const cle = String(question.campagne);
    parGroupage.set(cle, [...(parGroupage.get(cle) ?? []), question]);
  }

  /**
   * Publie la reponse.
   *
   * ⚠️ **Le filtre local n'est qu'un avertissement ; c'est le serveur qui
   * refuse.** Le §15 agit dans les deux sens, et plus serieusement de ce
   * cote-ci : un groupeur qui glisse son numero dans une reponse publique
   * contourne la plateforme, et c'est lui qui y gagne. Un refus du serveur
   * s'affiche donc sous la question, meme si le filtre d'ici a laisse passer
   * — par exemple un numero ecrit en lettres, que seul le niveau 2 attrape.
   */
  const publier = async (identifiant: number) => {
    const texte = (brouillons[identifiant] ?? "").trim();
    if (!texte) {
      return;
    }
    const publiee = await reponse.executer({
      telephone,
      question: identifiant,
      reponse: texte,
    });
    if (publiee) {
      setBrouillons((precedents) => {
        const suite = { ...precedents };
        delete suite[identifiant];
        return suite;
      });
      recharger();
    }
  };

  const commencerAReprendre = (id: number, valeur: string) => {
    if (!avertissementVu && valeur.length === 1) {
      setAvertissementOuvert(true);
    }
    setBrouillons({ ...brouillons, [id]: valeur });
  };

  return (
    <div className="pb-18">
      <EnTeteGroupeur
        titre="Questions"
        sousTitre={`${sansReponse.length} sans réponse`}
        onRetour={onRetour}
      />

      <div className="flex gap-2 px-4 pt-4">
        {(
          [
            ["sans-reponse", `Sans réponse (${sansReponse.length})`],
            ["toutes", "Toutes"],
          ] as const
        ).map(([cle, libelle]) => (
          <button
            key={cle}
            type="button"
            aria-pressed={filtre === cle}
            onClick={() => setFiltre(cle)}
            className={`inline-flex min-h-12 items-center rounded-full border px-4 text-sm font-medium ${
              filtre === cle
                ? "border-confiance bg-confiance-fond text-confiance"
                : "border-bordure text-texte"
            }`}
          >
            {libelle}
          </button>
        ))}
      </div>

      {[...parGroupage.entries()].map(([groupageId, questions]) => {
        /* La campagne vient de **ses** campagnes, pas du catalogue public :
           le groupeur peut avoir une campagne cloturee, qui n'y figure plus. */
        const groupage = campagnes.find((c) => c.id === groupageId);
        return (
          <section key={groupageId} className="mt-6 px-4">
            <div className="flex items-center gap-3">
              <Vignette
                photo={groupage?.photo}
                alt={groupage?.produit ?? ""}
                taille={48}
              />
              <h2 className="min-w-0 truncate font-semibold text-texte">
                {/* Le titre vient de la question elle-meme : il est joint par
                    l'API, ce qui evite de dependre de la liste des campagnes
                    pour afficher un en-tete. */}
                {questions[0]?.campagne_titre ?? groupage?.produit ?? groupageId}
              </h2>
            </div>

            <ul className="mt-3 space-y-4">
              {questions.map((question) => {
                const brouillon = brouillons[question.id] ?? "";
                const verdict = verifier(brouillon);
                const bloque = brouillon.trim() !== "" && !verdict.publiable;

                return (
                  <li
                    key={question.id}
                    className="rounded-xl border border-bordure p-3"
                  >
                    <p className="text-texte">{question.texte}</p>
                    <p className="mt-0.5 text-xs text-texte-secondaire">
                      {question.auteur}
                      <span aria-hidden="true"> · </span>
                      {formaterDateCourte(question.posee_le.slice(0, 10))}
                    </p>

                    {question.reponse ? (
                      <div className="mt-2 rounded-[10px] bg-surface-douce p-2.5">
                        <p className="text-xs font-semibold text-texte">
                          Votre réponse
                        </p>
                        <p className="mt-0.5 text-sm text-texte-secondaire">
                          {question.reponse}
                        </p>
                      </div>
                    ) : (
                      <div className="mt-3">
                        <textarea
                          rows={2}
                          value={brouillon}
                          onChange={(e) =>
                            commencerAReprendre(question.id, e.target.value)
                          }
                          placeholder="Votre réponse…"
                          aria-label="Votre réponse"
                          className={`w-full resize-none rounded-[10px] border px-3 py-2.5 text-sm outline-none ${
                            bloque
                              ? "border-danger bg-danger-fond"
                              : "border-bordure focus:border-2 focus:border-confiance"
                          }`}
                        />

                        {bloque ? (
                          <div className="mt-2">
                            {/* Plus ferme que cote acheteur : la bonne foi y
                                est moins probable. */}
                            <Encart
                              variante="danger"
                              role="groupeur"
                              titre="Cette réponse ne sera pas publiée."
                            >
                              Elle contient des informations permettant de vous
                              identifier ou de vous contacter hors de Group
                              Achat. Cette tentative est enregistrée. Les
                              échanges de coordonnées peuvent entraîner la
                              suspension de votre compte.
                            </Encart>
                          </div>
                        ) : null}

                        {reponse.erreur ? (
                          <p
                            role="alert"
                            className="mt-2 text-sm font-medium text-danger"
                          >
                            {reponse.erreur.estRefusDeSaisie
                              ? Object.values(reponse.erreur.champs)[0]?.[0]
                              : reponse.erreur.messageLisible}
                          </p>
                        ) : null}

                        <div className="mt-2">
                          <Bouton
                            role="groupeur"
                            desactive={bloque || brouillon.trim() === ""}
                            chargement={reponse.enCours}
                            onClick={() => publier(question.id)}
                          >
                            Répondre
                          </Bouton>
                        </div>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </section>
        );
      })}

      <div className="px-4 pt-6">
        <Encart variante="info" role="groupeur">
          Une réponse publique profite à tous vos participants et rassure les
          visiteurs.
        </Encart>
      </div>

      {avertissementOuvert ? (
        <FeuilleRemontante
          titre="Vos réponses sont publiques"
          onFermer={() => {
            setAvertissementVu(true);
            setAvertissementOuvert(false);
          }}
        >
          <div className="mt-4 space-y-4 text-center">
            <IconeBouclier taille={40} className="mx-auto text-confiance" />
            <h2 className="text-xl font-semibold text-texte">
              Vos réponses sont publiques.
            </h2>
            <p className="text-texte-secondaire">
              Ne communiquez jamais votre numéro, votre adresse ou un lien vers
              un autre service.
            </p>
            {/* Ne menace pas : explique son interet. */}
            <p className="text-texte-secondaire">
              Les acheteurs paient sur Group Achat, et c&apos;est ce qui vous
              garantit d&apos;être payé à la clôture.
            </p>
            <Bouton
              role="groupeur"
              onClick={() => {
                setAvertissementVu(true);
                setAvertissementOuvert(false);
              }}
            >
              J&apos;ai compris
            </Bouton>
          </div>
        </FeuilleRemontante>
      ) : null}
    </div>
  );
}
