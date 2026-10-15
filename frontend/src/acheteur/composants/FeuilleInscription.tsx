import { useEffect, useRef, useState } from "react";
import { poserLeJetonAcheteur } from "../../api/client";
import {
  controlerLInscription,
  demanderUnCode,
  ouvrirUneSession,
  retenirLeJeton,
} from "../../api/session";
import { useAction } from "../../api/useRequete";
import Bouton from "../../ui/Bouton";
import Champ from "../../ui/Champ";
import FeuilleRemontante from "../../ui/FeuilleRemontante";
import { IconeProfil } from "../../ui/Icones";
import type { Identite } from "./FeuilleConnexion";
import { ACHETEUR_DEMO, DEMONSTRATION, valeurDemo } from "../../domaine/demonstration";

/**
 * L'inscription classique de l'acheteur — nom, numéro, courriel, mot de passe.
 *
 * ## Les deux étapes, et pourquoi il y en a deux et pas une
 *
 * ```
 * 1. Le formulaire ──▶ controlerLInscription()  (ni compte ni SMS)
 *                        │
 *                        ├─ numéro déjà pris ──▶ on renvoie vers la connexion
 *                        └─ bon ──▶ demanderUnCode()
 *
 * 2. Les quatre cases ──▶ ouvrirUneSession({…, mot_de_passe})
 *                           └─▶ le compte est créé, la session ouverte
 * ```
 *
 * ⚠️ **La vérification du numéro par SMS n'est pas une étape de trop, et il ne
 * faut pas la retirer pour « faire plus classique ».** Le numéro *est*
 * l'identifiant du compte, et c'est par lui que partent les notifications de
 * livraison. Sans preuve, n'importe qui s'inscrit sur le numéro d'un voisin et
 * reçoit à sa place l'annonce que son colis est arrivé — en choisissant le mot
 * de passe au passage. Beaucoup de sites marchands vérifient d'ailleurs par
 * SMS ou par courriel ; ce qui serait inhabituel, c'est de ne rien vérifier.
 *
 * ⚠️ **Le contrôle du formulaire précède l'envoi du code, et l'ordre compte.**
 * Sans lui, un mot de passe trop court n'est refusé qu'à la dernière requête :
 * l'acheteur a reçu un SMS, il est devant les quatre cases, et il doit revenir
 * corriger un champ. C'est la façon sûre de faire abandonner une inscription —
 * et, le jour où un fournisseur sera branché (§18.2), de payer un SMS pour
 * rien.
 *
 * ## Ce que ce formulaire ne demande pas
 *
 * **Aucune adresse.** Elle se saisit à l'écran de commande, où elle sert à
 * calculer les frais de livraison, et elle devient alors l'adresse par défaut
 * du compte. La demander ici obligerait à la donner même pour poser une
 * question.
 *
 * **Le courriel reste facultatif**, et il le restera : une partie du cœur de
 * cible à Lomé n'a pas d'adresse de messagerie consultée mais répond au
 * téléphone (§10.5 pour le même raisonnement côté groupeur). L'exiger
 * écarterait exactement ces gens-là.
 *
 * **Aucun mot de passe.** ⚠️ Cette feuille en demandait un, avec sa
 * confirmation ; l'utilisateur a décrit le parcours sans lui. Il reste
 * **posable depuis la page Profil**, pour qui veut se reconnecter sans
 * attendre de SMS — ce qui ne coûte rien puisque c'est déjà construit, et
 * n'alourdit pas le chemin vers la commande. Chaque champ posé devant
 * quelqu'un qui s'apprête à payer est un acheteur perdu.
 *
 * ## Le mode démonstration
 *
 * ⚠️ **Les champs arrivent pré-remplis, et les quatre cases du code aussi**,
 * quand `VITE_DEMONSTRATION=1`. C'est pour montrer les écrans sans taper au
 * clavier devant un jury. **Le code reste vérifié par le serveur** : on le
 * pré-remplit, on ne le contourne pas. Et le numéro est tiré à chaque
 * chargement, sans quoi la deuxième démonstration tomberait sur « ce numéro a
 * déjà un compte ».
 */

const SECONDES_AVANT_RENVOI = 42;

export default function FeuilleInscription({
  motif,
  onFermer,
  onSeConnecter,
  onInscrit,
}: {
  /** « Vous rejoignez : Écouteurs filaires avec micro — 4 000 F la part » */
  motif?: string;
  onFermer: () => void;
  /** Le numéro est déjà pris, ou l'acheteur se reconnaît : on bascule. */
  onSeConnecter: () => void;
  onInscrit: (identite: Identite) => void;
}) {
  const [etape, setEtape] = useState<"formulaire" | "code">("formulaire");

  const [nom, setNom] = useState(valeurDemo(ACHETEUR_DEMO.prenom));
  const [telephone, setTelephone] = useState(
    valeurDemo(ACHETEUR_DEMO.telephone),
  );
  const [courriel, setCourriel] = useState(valeurDemo(ACHETEUR_DEMO.courriel));

  /** Les erreurs par champ, fusionnées du serveur et des contrôles d'écran. */
  const [erreurs, setErreurs] = useState<Record<string, string>>({});

  /* Pré-remplies en démonstration : la validation automatique ne part qu'à la
     saisie de la quatrième case, donc rien ne s'envoie tout seul — il reste un
     geste à faire devant le jury, et c'est voulu. */
  const [code, setCode] = useState<string[]>(
    DEMONSTRATION ? ACHETEUR_DEMO.code.split("") : ["", "", "", ""],
  );
  const [secondes, setSecondes] = useState(SECONDES_AVANT_RENVOI);
  const [codeDemo, setCodeDemo] = useState<string>();

  const controle = useAction(controlerLInscription);
  const envoi = useAction(demanderUnCode);
  const ouverture = useAction(ouvrirUneSession);

  const cases = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (etape !== "code" || secondes <= 0) {
      return;
    }
    const minuteur = window.setTimeout(() => setSecondes(secondes - 1), 1000);
    return () => window.clearTimeout(minuteur);
  }, [etape, secondes]);

  const numeroComplet = () => `+228${telephone.replace(/\D/g, "")}`;

  /** Étape 1 — contrôler le formulaire, puis envoyer le code. */
  async function continuer() {
    const locales: Record<string, string> = {};
    if (nom.trim() === "") {
      locales.nom = "Votre prénom est nécessaire pour la livraison.";
    }
    setErreurs(locales);
    if (Object.keys(locales).length > 0) {
      return;
    }

    const verdict = await controle.executer({
      telephone: numeroComplet(),
      nom: nom.trim(),
      courriel: courriel.trim(),
    });
    if (!verdict) {
      /* ⚠️ **On ne lit pas `controle.erreur` juste après le `await`.** Cette
         closure voit encore la valeur précédente — `undefined` — parce que
         `setErreur` vient d'être appelée à l'intérieur de `executer` et que
         React n'a pas encore re-rendu. C'est un défaut déjà payé dans
         `FeuilleConnexion`, invisible au typage, et qui ne se voit qu'en
         soumettant un formulaire invalide : le message ne s'affichait jamais.
         Le rendu, lui, lit `erreursServeur` plus bas, où elle est à jour. */
      return;
    }

    const resultat = await envoi.executer(numeroComplet());
    if (!resultat) {
      return;
    }
    setCodeDemo(resultat.code_de_demonstration ?? undefined);
    setCode(["", "", "", ""]);
    setEtape("code");
    setSecondes(SECONDES_AVANT_RENVOI);
  }

  async function renvoyerLeCode() {
    const resultat = await envoi.executer(numeroComplet());
    if (resultat) {
      setCodeDemo(resultat.code_de_demonstration ?? undefined);
      setSecondes(SECONDES_AVANT_RENVOI);
    }
  }

  function saisirCase(indice: number, valeur: string) {
    const chiffre = valeur.replace(/\D/g, "").slice(-1);
    const suivant = [...code];
    suivant[indice] = chiffre;
    setCode(suivant);

    if (chiffre && indice < 3) {
      cases.current[indice + 1]?.focus();
      return;
    }
    if (indice === 3 && suivant.every((c) => c !== "")) {
      void terminer(suivant.join(""));
    }
  }

  /**
   * Étape 2 — le code crée le compte, avec son mot de passe.
   *
   * ⚠️ **C'est le serveur qui vérifie le code.** Le comparer à une constante
   * ici donnerait un contrôle qu'il suffit de contourner par un appel direct —
   * et un compte se prend par un appel direct.
   */
  async function terminer(saisi: string) {
    const session = await ouverture.executer({
      telephone: numeroComplet(),
      code: saisi,
      nom: nom.trim(),
      courriel: courriel.trim(),
    });

    if (!session) {
      setCode(["", "", "", ""]);
      cases.current[0]?.focus();
      return;
    }

    retenirLeJeton(session.jeton);
    poserLeJetonAcheteur(session.jeton);
    onInscrit({
      telephone: session.acheteur.telephone,
      nom: session.acheteur.nom || undefined,
    });
  }

  /** Les erreurs de champ renvoyées par le serveur, à l'une ou l'autre étape. */
  const erreursServeur: Record<string, string[]> = {
    ...(controle.erreur?.estRefusDeSaisie ? controle.erreur.champs : {}),
    ...(ouverture.erreur?.estRefusDeSaisie ? ouverture.erreur.champs : {}),
  };
  const erreurDe = (champ: string) =>
    erreurs[champ] ?? erreursServeur[champ]?.[0];

  /**
   * ⚠️ **Un numéro déjà pris n'est pas une erreur de saisie**, c'est un
   * aiguillage. On le détecte pour proposer la connexion au lieu de laisser
   * l'acheteur corriger un champ qui est juste.
   */
  const numeroDejaPris = (erreurDe("telephone") ?? "").includes("déjà un compte");

  const numeroValide = telephone.replace(/\D/g, "").length >= 8;
  const formulaireRempli = nom.trim() !== "" && numeroValide;

  return (
    <FeuilleRemontante titre="Créer un compte" onFermer={onFermer}>
      {/* L'indicateur d'étape. Décoratif pour l'œil, **annoncé pour un lecteur
          d'écran** : deux barres colorées ne disent rien à qui ne les voit
          pas, d'où la phrase en `sr-only`. */}
      <div className="mt-2 flex items-center gap-2" aria-hidden="true">
        <span className="h-1 flex-1 rounded-full bg-primaire" />
        <span
          className={`h-1 flex-1 rounded-full ${
            etape === "code" ? "bg-primaire" : "bg-bordure"
          }`}
        />
      </div>
      <p className="sr-only">
        Étape {etape === "formulaire" ? 1 : 2} sur 2.
      </p>

      {etape === "formulaire" ? (
        <div className="mt-5 space-y-4">
          <div className="flex flex-col items-center text-center">
            <span
              aria-hidden="true"
              className="flex size-14 items-center justify-center rounded-full bg-primaire-fond text-primaire-texte-sur-fond"
            >
              <IconeProfil taille={26} />
            </span>
            <h2 className="mt-3 font-titre text-xl font-semibold text-texte">
              Créer votre compte
            </h2>
            <p className="mt-1 text-sm text-texte-secondaire">
              Une minute, et c&apos;est fait pour toutes vos commandes.
            </p>
          </div>

          {/* « Prénom » et non « Nom » : c'est tout ce dont le livreur a
              besoin le jour de la remise, et un champ de moins à remplir au
              pouce. Le modèle, lui, garde le champ `nom` — le renommer
              imposerait une migration pour un libellé. */}
          <Champ
            libelle="Votre prénom"
            valeur={nom}
            onChanger={setNom}
            autoComplete="given-name"
            exemple="Akosua"
            erreur={erreurDe("nom")}
            aide="Il n'est montré qu'au livreur, le jour de la livraison."
            autoFocus
          />

          <Champ
            libelle="Numéro de téléphone"
            valeur={telephone}
            onChanger={setTelephone}
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            prefixe="+228"
            exemple="90 12 34 56"
            erreur={erreurDe("telephone")}
            aide="Nous ne le communiquons jamais au groupeur."
          />

          {/* ⚠️ **Le numéro déjà pris mène à la connexion, pas à une
              correction.** Le champ est juste : c'est le parcours qui est le
              mauvais. Laisser le message d'erreur seul enverrait l'acheteur
              modifier un numéro qui est bien le sien. */}
          {numeroDejaPris ? (
            <div className="rounded-xl bg-primaire-fond p-4">
              <p className="text-sm font-medium text-texte">
                Vous avez déjà un compte avec ce numéro.
              </p>
              <div className="mt-3">
                <Bouton style="secondaire" onClick={onSeConnecter}>
                  Se connecter plutôt
                </Bouton>
              </div>
            </div>
          ) : null}

          <Champ
            libelle="Courriel (facultatif)"
            valeur={courriel}
            onChanger={setCourriel}
            type="email"
            inputMode="email"
            autoComplete="email"
            exemple="akosua@example.tg"
            erreur={erreurDe("courriel")}
          />

          {/* Pas de champ de mot de passe : voir l'en-tête. Il se pose
              depuis la page Profil, plus tard. */}

          <Bouton
            desactive={!formulaireRempli}
            chargement={controle.enCours || envoi.enCours}
            onClick={continuer}
          >
            Continuer
          </Bouton>

          <p className="text-center text-sm text-texte-secondaire">
            Vous avez déjà un compte ?{" "}
            <button
              type="button"
              onClick={onSeConnecter}
              className="min-h-12 font-medium text-primaire"
            >
              Se connecter
            </button>
          </p>

          {motif ? (
            <p className="text-center text-xs text-texte-mention">{motif}</p>
          ) : null}
        </div>
      ) : null}

      {etape === "code" ? (
        <div className="mt-5 space-y-4">
          <div className="text-center">
            <h2 className="font-titre text-xl font-semibold text-texte">
              Vérifions votre numéro
            </h2>
            <p className="mt-1 text-texte-secondaire">
              Code envoyé au +228 {telephone}{" "}
              <button
                type="button"
                onClick={() => setEtape("formulaire")}
                className="font-medium text-primaire"
              >
                Modifier
              </button>
            </p>
          </div>

          <div className="flex justify-center gap-3">
            {code.map((chiffre, indice) => (
              <input
                key={indice}
                ref={(element) => {
                  cases.current[indice] = element;
                }}
                value={chiffre}
                onChange={(evenement) =>
                  saisirCase(indice, evenement.target.value)
                }
                inputMode="numeric"
                autoComplete={indice === 0 ? "one-time-code" : undefined}
                maxLength={1}
                aria-label={`Chiffre ${indice + 1} sur 4`}
                autoFocus={indice === 0}
                className={`size-14 rounded-[10px] border bg-white text-center text-2xl font-semibold text-texte outline-none focus:border-2 focus:border-primaire ${
                  ouverture.erreur ? "border-danger" : "border-bordure-champ"
                }`}
              />
            ))}
          </div>

          {/* **Le message vient du serveur**, qui sait combien d'essais
              restent — un compteur d'interface repartirait à trois au
              rechargement de la page, ce qui revient à ne rien compter. */}
          {ouverture.erreur ? (
            <p role="alert" className="text-center text-sm text-danger">
              {ouverture.erreur.estRefusDeSaisie
                ? (Object.values(ouverture.erreur.champs)[0]?.[0] ??
                  "Code incorrect.")
                : ouverture.erreur.messageLisible}
            </p>
          ) : null}

          <p className="text-center text-sm text-texte-secondaire">
            {secondes > 0 ? (
              <>Renvoyer le code dans 00:{secondes.toString().padStart(2, "0")}</>
            ) : (
              <button
                type="button"
                onClick={renvoyerLeCode}
                className="font-medium text-primaire"
              >
                Renvoyer le code
              </button>
            )}
          </p>

          {/* ⚠️ Affiché **seulement si le serveur l'a renvoyé**, c'est-à-dire
              en développement. En production il n'y a rien à montrer : le code
              est parti par SMS, ou la demande a été refusée. */}
          {codeDemo ? (
            <p className="text-center text-xs text-texte-mention">
              Démonstration — aucun SMS n&apos;est envoyé. Le code est{" "}
              <strong className="font-semibold text-texte-secondaire">
                {codeDemo}
              </strong>
              .
            </p>
          ) : null}
        </div>
      ) : null}
    </FeuilleRemontante>
  );
}
