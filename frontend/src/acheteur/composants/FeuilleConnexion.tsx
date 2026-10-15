import { useEffect, useRef, useState } from "react";
import { poserLeJetonAcheteur } from "../../api/client";
import {
  completerMonProfil,
  demanderUnCode,
  ouvrirUneSession,
  ouvrirUneSessionParMotDePasse,
  preparerLaConnexion,
  type Profil,
  retenirLeJeton,
} from "../../api/session";
import { useAction } from "../../api/useRequete";
import Bouton from "../../ui/Bouton";
import Champ from "../../ui/Champ";
import FeuilleRemontante from "../../ui/FeuilleRemontante";

/**
 * Ecran 4 — Connexion. SPEC_ECRANS_FIGMA.md, ecran 4.
 *
 * **Declenchee par le paiement, jamais par l'ouverture** (§1.5). La mecanique
 * de la feuille — voile, poignee, croix, touche Echap — est dans
 * `ui/FeuilleRemontante` ; ce fichier ne porte que les trois etapes.
 *
 * Fermer la feuille ramene a l'ecran 5 **intact**, quantite, repere et
 * position conserves — parce que c'est `App` qui garde cet etat et que
 * l'ecran 5 n'est jamais demonte. Apres le code, la feuille redescend et
 * **l'action reprend seule**.
 *
 * **Aucun second bouton** : pas de « Creer un compte » a cote de « Se
 * connecter ». Si le numero est inconnu, le compte se cree, et l'etape du nom
 * est la seule question de plus.
 *
 * ⚠️ **La phrase « ni e-mail, ni mot de passe » etait ici, et elle est
 * fausse depuis que le compte acheteur est un vrai compte.** Elle est
 * reproduite pour que personne ne la restaure en croyant reparer une
 * regression. Son argument reste respecte autrement, et c'est le point
 * important : **aucun champ n'a ete ajoute a ce parcours.** Le mot de passe ne
 * se pose pas ici, il se pose depuis l'ecran de profil, plus tard, quand plus
 * rien n'est en jeu. Ce qui change ici est qu'on peut desormais **entrer**
 * avec lui.
 *
 * ## Les deux voies, et comment la feuille choisit
 *
 * ```
 * numero ──▶ preparerLaConnexion()
 *              │
 *              ├─ a un mot de passe ──▶ etape « mot-de-passe »
 *              │                          └─ lien : recevoir plutot un code
 *              │
 *              └─ sinon ──────────────▶ envoi du code ──▶ etape « code »
 * ```
 *
 * ⚠️ **C'est `preparerLaConnexion` qui decide, et elle n'envoie aucun SMS.**
 * Avant elle, la feuille devait envoyer un code **pour savoir quoi afficher** :
 * quelqu'un qui connait son mot de passe recevait un SMS inutile, et le jour
 * ou un fournisseur sera branche (§18.2) ce serait un SMS facture a chaque
 * ouverture de cette feuille.
 *
 * ⚠️ **Le code SMS reste accessible depuis l'etape du mot de passe**, en
 * lien secondaire. C'est la voie de recuperation, et c'est elle qui leve le
 * verrou de cinq echecs cote serveur. Elle est ce qui dispense d'ecrire un
 * parcours « mot de passe oublie » : pas de lien a duree de vie, pas de
 * courriel a attendre — et le courriel est justement facultatif sur ce marche.
 *
 * Pas de fleche de retour : on superpose, on ne navigue pas.
 *
 * ## Le code n'est plus simule — seul son envoi manque
 *
 * Le serveur **genere** un code, le **stocke hache**, le fait **expirer** au
 * bout de dix minutes et n'en accepte que **trois essais**. Ce qui manque est
 * le SMS : Group Achat n'a pas de fournisseur (§18.2). En developpement le
 * code vaut `1234` et le serveur le renvoie dans sa reponse, que l'ecran
 * affiche plutot que de laisser chercher.
 *
 * ⚠️ **En production, le serveur refuse de servir un code fixe** : sans
 * fournisseur SMS configure, la demande de code repond 503. C'est voulu — un
 * code fixe mis en ligne donnerait a n'importe qui le compte de n'importe quel
 * numero.
 *
 * ## Ce que la feuille enregistre sans le demander
 *
 * **L'adresse.** Au moment ou elle s'ouvre, l'acheteur vient de saisir son
 * quartier et son repere a l'ecran precedent : on les transmet avec le code,
 * et ils deviennent son adresse par defaut. Ses commandes suivantes arrivent
 * pre-remplies.
 *
 * Ajouter un champ adresse ici ferait l'inverse : un ecran de formulaire de
 * plus au moment precis ou il sort sa carte.
 *
 * ## Pourquoi le nom vient apres le code, et pas avant
 *
 * Prouver qu'on a le telephone est la seule chose qui engage ; un formulaire
 * pose avant cette preuve serait rempli par n'importe qui. Le code valide
 * ouvre donc la session, **puis** l'ecran demande le nom — qui part par un
 * appel authentifie ordinaire.
 */

const SECONDES_AVANT_RENVOI = 42;

export interface Identite {
  telephone: string;
  nom?: string;
}

export default function FeuilleConnexion({
  rappelContexte,
  adresse,
  onFermer,
  onConnecte,
}: {
  /** « Vous commandez : Écouteurs filaires avec micro — 1 part, 4 000 F CFA » */
  rappelContexte: string;
  /**
   * L'adresse que l'acheteur vient de saisir à l'écran de commande.
   *
   * Elle part avec le code et devient son adresse par défaut. On ne la lui
   * demande pas ici : elle est à l'écran, derrière la feuille.
   */
  adresse?: { quartier: string; repere: string };
  onFermer: () => void;
  onConnecte: (identite: Identite) => void;
}) {
  const [etape, setEtape] = useState<
    "numero" | "mot-de-passe" | "code" | "nom"
  >("numero");
  const [telephone, setTelephone] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [code, setCode] = useState(["", "", "", ""]);
  const [erreurCode, setErreurCode] = useState<string>();
  const [secondes, setSecondes] = useState(SECONDES_AVANT_RENVOI);
  const [nom, setNom] = useState("");
  /** Le code servi par le serveur en développement, affiché à l'écran. */
  const [codeDemo, setCodeDemo] = useState<string>();
  /** Le profil renvoyé à l'ouverture de session. */
  const [profil, setProfil] = useState<Profil>();

  const envoi = useAction(demanderUnCode);
  const preparation = useAction(preparerLaConnexion);
  const ouverture = useAction(ouvrirUneSession);
  const entreeParMotDePasse = useAction(ouvrirUneSessionParMotDePasse);
  const majProfil = useAction(completerMonProfil);

  const cases = useRef<(HTMLInputElement | null)[]>([]);

  // Compte a rebours du renvoi, actif seulement a l'etape du code.
  useEffect(() => {
    if (etape !== "code" || secondes <= 0) {
      return;
    }
    const minuteur = window.setTimeout(() => setSecondes(secondes - 1), 1000);
    return () => window.clearTimeout(minuteur);
  }, [etape, secondes]);

  function saisirCase(indice: number, valeur: string) {
    const chiffre = valeur.replace(/\D/g, "").slice(-1);
    const suivant = [...code];
    suivant[indice] = chiffre;
    setCode(suivant);
    setErreurCode(undefined);

    if (chiffre && indice < 3) {
      cases.current[indice + 1]?.focus();
      return;
    }

    // Validation automatique a la quatrieme case — pas de bouton (ecran 4).
    if (indice === 3 && suivant.every((c) => c !== "")) {
      verifier(suivant.join(""));
    }
  }

  const numeroComplet = () => `+228${telephone.replace(/\D/g, "")}`;

  /**
   * Demande l'envoi du code.
   *
   * ⚠️ **On n'avance qu'une fois le serveur ayant répondu.** Passer tout de
   * suite à l'écran des quatre cases serait plus fluide et mentirait : si
   * l'envoi échoue — pas de fournisseur SMS, réseau coupé — l'acheteur
   * attendrait devant quatre cases un code qui n'arrive jamais.
   */
  async function envoyerLeCode() {
    const resultat = await envoi.executer(numeroComplet());
    if (!resultat) {
      return;
    }
    setCodeDemo(resultat.code_de_demonstration ?? undefined);
    setCode(["", "", "", ""]);
    setErreurCode(undefined);
    setEtape("code");
    setSecondes(SECONDES_AVANT_RENVOI);
  }

  /**
   * L'aiguillage, après le numéro. **Aucun SMS n'est envoyé ici.**
   *
   * ⚠️ **En cas d'échec de `preparerLaConnexion`, on envoie le code.** Ce
   * repli compte : la question à laquelle elle répond est un confort —
   * « faut-il montrer le champ de mot de passe ? » — et une panne dessus ne
   * doit pas empêcher de se connecter. Le code SMS marche pour **tout le
   * monde**, avec ou sans mot de passe, donc c'est le repli sûr.
   */
  async function continuerDepuisLeNumero() {
    const voies = await preparation.executer(numeroComplet());
    if (voies?.a_un_mot_de_passe) {
      setMotDePasse("");
      setEtape("mot-de-passe");
      return;
    }
    await envoyerLeCode();
  }

  /** Pose le jeton et rend la main à l'écran appelant. */
  function terminer(telephoneCompte: string, nomCompte?: string) {
    onConnecte({ telephone: telephoneCompte, nom: nomCompte || undefined });
  }

  /**
   * Retient le jeton d'une session qui vient de s'ouvrir, par l'une ou l'autre
   * voie, puis termine ou demande le nom.
   *
   * Mis en commun dès qu'il y a eu deux voies : dupliquer ces quatre lignes
   * aurait laissé passer, un jour, une voie qui oublie `poserLeJetonAcheteur`
   * — et un jeton retenu mais non posé donne une session qui survit au
   * rechargement et ne marche pas avant.
   */
  function accueillir(session: { jeton: string; acheteur: Profil }) {
    retenirLeJeton(session.jeton);
    poserLeJetonAcheteur(session.jeton);
    setProfil(session.acheteur);

    if (session.acheteur.nom) {
      terminer(session.acheteur.telephone, session.acheteur.nom);
      return;
    }
    setEtape("nom");
  }

  /**
   * La seconde voie. **Le serveur verrouille après cinq échecs**, et son
   * message dit alors d'essayer le code SMS — qui lève le verrou.
   */
  async function entrerAvecLeMotDePasse() {
    const session = await entreeParMotDePasse.executer({
      telephone: numeroComplet(),
      mot_de_passe: motDePasse,
    });
    if (!session) {
      /* Comme pour le code : on ne recopie pas l'erreur dans un état local.
         Juste après le `await`, cette closure voit encore la valeur
         précédente. C'est le JSX qui lit `entreeParMotDePasse.erreur` au
         re-rendu suivant. */
      return;
    }
    accueillir(session);
  }

  /**
   * ⚠️ **C'est le serveur qui vérifie le code, pas cet écran.**
   *
   * Le comparer à une constante ici donnerait un contrôle qu'il suffit de
   * contourner par un appel direct — et un compte se prend par un appel
   * direct. Le serveur compte aussi les essais : trois, puis le code meurt.
   */
  async function verifier(saisi: string) {
    const session = await ouverture.executer({
      telephone: numeroComplet(),
      code: saisi,
      ...(adresse ?? {}),
    });

    if (!session) {
      /* ⚠️ **On ne recopie pas l'erreur dans un état local ici.**
         `ouverture.erreur` vient d'être posée par `setErreur` à l'intérieur de
         `executer` : juste après le `await`, cette closure voit encore la
         valeur *précédente*, c'est-à-dire `undefined`. Le message ne
         s'affichait jamais — un défaut invisible au typage, et qui ne se voit
         qu'en entrant un mauvais code.

         Le rendu, lui, lit `ouverture.erreur` au re-rendu suivant, où elle est
         à jour. C'est donc le JSX qui l'affiche, pas un miroir. */
      setCode(["", "", "", ""]);
      cases.current[0]?.focus();
      return;
    }

    /* La session est ouverte : le jeton part avec tous les appels suivants,
       et il survit à la fermeture de l'onglet. C'est ça, la reconnexion
       automatique. */
    accueillir(session);
  }

  /** Pose le nom sur le compte — appel authentifié, le code est consommé. */
  async function enregistrerLeNom() {
    const mis = await majProfil.executer({ nom: nom.trim() });
    terminer(profil?.telephone ?? numeroComplet(), mis?.nom ?? nom.trim());
  }

  const numeroValide = telephone.replace(/\D/g, "").length >= 8;

  /**
   * Le message sous les quatre cases.
   *
   * **Il vient du serveur**, qui sait combien d'essais restent — un compteur
   * d'interface repartirait à trois au rechargement de la page, ce qui
   * reviendrait à ne rien compter.
   */
  const messageCode = ouverture.erreur
    ? ouverture.erreur.estRefusDeSaisie
      ? (Object.values(ouverture.erreur.champs)[0]?.[0] ?? "Code incorrect.")
      : ouverture.erreur.messageLisible
    : erreurCode;

  /** Le message sous le champ de mot de passe. **Il vient du serveur.** */
  const messageMotDePasse = entreeParMotDePasse.erreur
    ? entreeParMotDePasse.erreur.estRefusDeSaisie
      ? (Object.values(entreeParMotDePasse.erreur.champs)[0]?.[0] ??
        "Mot de passe incorrect.")
      : entreeParMotDePasse.erreur.messageLisible
    : undefined;

  return (
    <FeuilleRemontante titre="Connexion" onFermer={onFermer}>
        {etape === "numero" ? (
          <div className="mt-4 space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-texte">
                Votre numéro de téléphone
              </h2>
              <p className="mt-1 text-texte-secondaire">
                Pour sécuriser votre commande et suivre votre livraison.
              </p>
            </div>

            <Champ
              libelle="Numéro de téléphone"
              valeur={telephone}
              onChanger={setTelephone}
              type="tel"
              inputMode="tel"
              prefixe="+228"
              exemple="90 12 34 56"
              aide="Nous ne communiquons jamais votre numéro au groupeur."
              autoFocus
            />

            {envoi.erreur ? (
              <p role="alert" className="text-sm font-medium text-danger">
                {envoi.erreur.estRefusDeSaisie
                  ? Object.values(envoi.erreur.champs)[0]?.[0]
                  : envoi.erreur.messageLisible}
              </p>
            ) : null}

            {/* ⚠️ « Continuer » et non « Recevoir mon code » : à cet instant
                **la feuille ne sait pas encore** par quelle voie ce numéro
                entre. Promettre un SMS à quelqu'un qui verra ensuite un champ
                de mot de passe le ferait attendre un code qui n'arrive pas.
                C'est aussi ce qui évite le second bouton que le §1.5 interdit :
                un seul chemin, et le serveur choisit. */}
            <Bouton
              desactive={!numeroValide}
              chargement={preparation.enCours || envoi.enCours}
              onClick={continuerDepuisLeNumero}
            >
              Continuer
            </Bouton>

            {/* 7 — Rappel de contexte : on sait toujours ce qu'on est en train
                de commander. */}
            <p className="text-center text-xs text-texte-secondaire">
              {rappelContexte}
            </p>
          </div>
        ) : null}

        {etape === "mot-de-passe" ? (
          <div className="mt-4 space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-texte">
                Votre mot de passe
              </h2>
              <p className="mt-1 text-texte-secondaire">
                +228 {telephone}{" "}
                <button
                  type="button"
                  onClick={() => setEtape("numero")}
                  className="font-medium text-primaire"
                >
                  Modifier
                </button>
              </p>
            </div>

            <Champ
              libelle="Mot de passe"
              valeur={motDePasse}
              onChanger={setMotDePasse}
              type="password"
              /* `current-password` et non `new-password` : c'est un champ de
                 connexion, et la valeur proposée doit être celle qui est
                 enregistrée. */
              autoComplete="current-password"
              erreur={messageMotDePasse}
              autoFocus
            />

            <Bouton
              desactive={motDePasse === ""}
              chargement={entreeParMotDePasse.enCours}
              onClick={entrerAvecLeMotDePasse}
            >
              Se connecter
            </Bouton>

            {/* ⚠️ **C'est tout le parcours « mot de passe oublié »**, et il
                tient en un lien. Le code SMS marche pour tout le monde, et il
                **lève le verrou** des cinq échecs côté serveur : personne ne
                reste enfermé dehors. Pas de lien à durée de vie à écrire, pas
                de courriel à attendre — et le courriel est facultatif ici. */}
            <button
              type="button"
              onClick={envoyerLeCode}
              disabled={envoi.enCours}
              className="mx-auto block min-h-12 text-sm font-medium text-primaire"
            >
              Mot de passe oublié ? Recevoir un code par SMS
            </button>

            <p className="text-center text-xs text-texte-secondaire">
              {rappelContexte}
            </p>
          </div>
        ) : null}

        {etape === "code" ? (
          <div className="mt-4 space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-texte">
                Entrez le code reçu
              </h2>
              <p className="mt-1 text-texte-secondaire">
                Code envoyé au +228 {telephone}{" "}
                <button
                  type="button"
                  onClick={() => setEtape("numero")}
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
                  maxLength={1}
                  aria-label={`Chiffre ${indice + 1} sur 4`}
                  autoFocus={indice === 0}
                  className={`size-14 rounded-[10px] border text-center text-2xl font-semibold text-texte outline-none focus:border-2 focus:border-primaire ${
                    messageCode ? "border-danger" : "border-bordure"
                  }`}
                />
              ))}
            </div>

            {messageCode ? (
              <p role="alert" className="text-center text-sm text-danger">
                {messageCode}
              </p>
            ) : null}

            <p className="text-center text-sm text-texte-secondaire">
              {secondes > 0 ? (
                <>
                  Renvoyer le code dans 00:
                  {secondes.toString().padStart(2, "0")}
                </>
              ) : (
                <button
                  type="button"
                  onClick={envoyerLeCode}
                  className="font-medium text-primaire"
                >
                  Renvoyer le code
                </button>
              )}
            </p>

            {/* ⚠️ Affiché **seulement si le serveur l'a renvoyé**, c'est-à-dire
                en développement. En production il n'y a rien à montrer : le
                code est parti par SMS, ou la demande a été refusée. */}
            {codeDemo ? (
              <p className="text-center text-xs text-texte-secondaire">
                Démonstration — aucun SMS n&apos;est envoyé. Le code est{" "}
                <strong className="font-semibold">{codeDemo}</strong>.
              </p>
            ) : null}
          </div>
        ) : null}

        {etape === "nom" ? (
          <div className="mt-4 space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-texte">Votre nom</h2>
              <p className="mt-1 text-texte-secondaire">
                Le livreur en a besoin pour vous remettre votre commande.
              </p>
            </div>

            <Champ
              libelle="Votre nom"
              valeur={nom}
              onChanger={setNom}
              exemple="Akosua Doe"
              autoFocus
            />

            <Bouton
              desactive={nom.trim() === ""}
              chargement={majProfil.enCours}
              onClick={enregistrerLeNom}
            >
              Continuer
            </Bouton>

            {/* Le compte existe déjà : « plus tard » n'annule rien, il saute
                seulement cette dernière question. Le livreur demandera le nom
                à la remise. */}
            <button
              type="button"
              onClick={() => terminer(profil?.telephone ?? numeroComplet())}
              className="mx-auto block min-h-12 text-sm font-medium text-primaire"
            >
              Plus tard
            </button>
          </div>
        ) : null}
    </FeuilleRemontante>
  );
}
