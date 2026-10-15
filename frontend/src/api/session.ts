import { appeler } from "./client";

/**
 * Le compte acheteur : code SMS, session, reconnexion automatique.
 *
 * ## Où vit le jeton, et pourquoi là
 *
 * Dans le `localStorage`, et non le `sessionStorage` — contrairement au jeton
 * d'administration, qui lui est volontairement oublié à la fermeture de
 * l'onglet. La différence tient à ce que les deux protègent :
 *
 * | | Jeton d'administration | Jeton acheteur |
 * |---|---|---|
 * | Donne accès à | **Tous** les dossiers, noms, pièces | **Son** compte |
 * | Poste partagé | Le suivant devient administrateur | Le suivant voit ses commandes |
 * | Oublié à la fermeture | **oui** | non — c'est le but |
 *
 * Un acheteur à qui on redemanderait un code SMS à chaque visite n'aurait pas
 * de compte, il aurait une corvée. Et ce qu'il risque en cas d'appareil
 * partagé — que quelqu'un voie ses commandes — n'est pas du même ordre que de
 * donner à un inconnu l'annuaire des groupeurs.
 *
 * ⚠️ **Le jeton n'est pas un mot de passe, même depuis qu'il existe un mot de
 * passe.** Qui a l'appareil déverrouillé a le compte : le mot de passe sert à
 * **entrer** sur un appareil neuf, pas à garder la porte fermée sur celui-ci.
 * C'est le compromis assumé d'un produit dont le §1.5 interdit le mur
 * d'authentification — on ne peut pas à la fois ne rien demander à l'entrée et
 * exiger un secret à chaque visite.
 *
 * La seule conséquence pratique est dans `definirLeMotDePasse` : changer de mot
 * de passe exige **l'ancien**, justement parce que la session seule ne prouve
 * pas qu'on est le titulaire.
 *
 * ## Les deux voies d'entrée
 *
 * | | Code SMS | Mot de passe |
 * |---|---|---|
 * | Disponible | **Toujours** | S'il en a posé un |
 * | Crée le compte | **oui** | non, jamais |
 * | Verrouillable | non | 5 échecs, 15 minutes |
 *
 * ⚠️ **Le code SMS est la voie de récupération, et il lève le verrou.** C'est
 * pour cela qu'il n'y a **aucun parcours « mot de passe oublié »** à écrire :
 * pas de lien à durée de vie, pas de courriel à attendre — et le courriel est
 * justement facultatif sur ce marché. On redemande un code, et c'est tout.
 */

const CLE = "groupachat.jeton-acheteur";

export function lireLeJeton(): string {
  try {
    return localStorage.getItem(CLE) ?? "";
  } catch {
    /* Navigation privée, stockage bloqué : la session vivra le temps de
       l'onglet, et il faudra refaire un code à la prochaine visite. Dégradé,
       jamais cassé. */
    return "";
  }
}

export function retenirLeJeton(jeton: string): void {
  try {
    localStorage.setItem(CLE, jeton);
  } catch {
    /* Voir ci-dessus. L'appel en mémoire prend le relais. */
  }
}

export function oublierLeJeton(): void {
  try {
    localStorage.removeItem(CLE);
  } catch {
    /* Rien à retirer s'il n'a jamais pu être écrit. */
  }
}

// ── Ce que le serveur sait de l'acheteur ───────────────────────────────────

export interface Profil {
  id: number;
  telephone: string;
  nom: string;
  /**
   * Facultatif, et jamais demandé pour commander — il ne se renseigne que
   * depuis l'écran de profil. Une partie du public à Lomé n'a pas d'adresse
   * de messagerie consultée mais répond au téléphone.
   *
   * ⚠️ **Il n'identifie pas le compte.** C'est le numéro, et lui seul.
   */
  courriel: string;
  /** La **dernière** adresse de livraison, pour pré-remplir la suivante. */
  quartier: string;
  repere: string;
  /**
   * ⚠️ **Un booléen, et le serveur n'en dira jamais plus.** L'empreinte du
   * mot de passe ne sort pas de l'API : la publier offrirait de quoi
   * l'attaquer hors ligne, sans limite d'essais ni verrou. Ce booléen suffit
   * à l'écran, qui n'a qu'un choix à faire — écrire « Définir » ou
   * « Modifier ».
   */
  a_un_mot_de_passe: boolean;
}

/** Ce que `preparerLaConnexion` apprend sur un numéro. */
export interface VoiesDeConnexion {
  compte_existe: boolean;
  a_un_mot_de_passe: boolean;
}

export interface CodeEnvoye {
  envoye: boolean;
  /** L'écran sait alors s'il devra demander le nom à l'étape suivante. */
  compte_existe: boolean;
  /**
   * ⚠️ **Rempli uniquement en développement.** Le serveur refuse de servir un
   * code fixe en production : voir `comptes/sessions.py`. L'écran l'affiche
   * plutôt que de laisser chercher — un SMS réel suppose un fournisseur, qui
   * n'est pas branché (§18.2).
   */
  code_de_demonstration: string | null;
}

export interface SessionOuverte {
  jeton: string;
  expire_le: string;
  acheteur: Profil;
  compte_cree: boolean;
}

/** Demande l'envoi d'un code à quatre chiffres. */
export function demanderUnCode(
  telephone: string,
  signal?: AbortSignal,
): Promise<CodeEnvoye> {
  return appeler("/comptes/code/", {
    methode: "POST",
    corps: { telephone },
    signal,
  });
}

/**
 * Vérifie le code et ouvre la session. **Crée le compte s'il manque.**
 *
 * ⚠️ `quartier` et `repere` sont ceux que l'acheteur **vient de saisir** à
 * l'écran de commande. On ne les lui redemande pas : les envoyer ici les
 * enregistre sur son compte, et sa prochaine commande arrivera pré-remplie.
 * Ajouter un champ adresse à cette feuille serait un écran de formulaire de
 * plus au moment précis où il s'apprête à payer.
 */
export function ouvrirUneSession(
  entree: {
    telephone: string;
    code: string;
    nom?: string;
    courriel?: string;
    /**
     * ⚠ **Rempli par l'inscription, jamais par une reconnexion.**
     *
     * L'inscription classique récolte tout en un écran, puis vérifie le
     * numéro par un code : le mot de passe voyage donc avec le code. Le
     * serveur ne l'accepte **qu'à la création** du compte et refuse un
     * numéro déjà inscrit — sinon le code SMS deviendrait une remise à
     * zéro silencieuse du mot de passe, là où en changer exige l'ancien.
     */
    mot_de_passe?: string;
    quartier?: string;
    repere?: string;
  },
  signal?: AbortSignal,
): Promise<SessionOuverte> {
  return appeler("/comptes/session/", {
    methode: "POST",
    corps: entree,
    signal,
  });
}

/**
 * Le formulaire d'inscription est-il bon ? **Aucun compte, aucun SMS.**
 *
 * ⚠️ **À appeler avant `demanderUnCode`, et ce n'est pas un luxe.** Sans
 * elle, un mot de passe trop court n'est refusé qu'à l'ouverture de session,
 * c'est-à-dire **après** l'envoi du code : l'acheteur a reçu un SMS, il est
 * devant les quatre cases, et il doit revenir corriger un champ. C'est la
 * façon sûre de faire abandonner une inscription.
 *
 * Elle refuse aussi un numéro **déjà inscrit**, et l'écran bascule alors sur
 * la connexion : c'est le prix du modèle classique, où deux parcours
 * distincts existent et où il faut dire lequel est le bon.
 *
 * ⚠️ **Elle ne remplace aucun contrôle du serveur**, qui revérifie tout à
 * l'ouverture de session. Un contrôle qui ne vit que dans l'écran se
 * contourne par un appel direct.
 */
export function controlerLInscription(
  entree: {
    telephone: string;
    nom: string;
    courriel?: string;
    /** Facultatif : le formulaire d'inscription n'en demande plus. */
    mot_de_passe?: string;
  },
  signal?: AbortSignal,
): Promise<{ valide: boolean }> {
  return appeler("/comptes/inscription/controler/", {
    methode: "POST",
    corps: entree,
    signal,
  });
}

/**
 * **Par quelle voie ce numéro peut-il entrer ?** N'envoie aucun SMS.
 *
 * ⚠️ **À appeler avant `demanderUnCode`, pas après.** Sans elle, la feuille
 * devait envoyer un SMS **pour savoir quoi afficher** : quelqu'un qui a posé
 * un mot de passe et s'en souvient recevait un code dont il n'avait aucun
 * besoin. Le jour où un fournisseur sera branché (§18.2), ce serait un SMS
 * facturé à chaque ouverture de la feuille.
 */
export function preparerLaConnexion(
  telephone: string,
  signal?: AbortSignal,
): Promise<VoiesDeConnexion> {
  return appeler("/comptes/preparer/", {
    methode: "POST",
    corps: { telephone },
    signal,
  });
}

/**
 * La seconde voie d'entrée. **Elle ne crée aucun compte.**
 *
 * C'est la différence de fond avec `ouvrirUneSession`, et elle n'est pas
 * négociable : un compte naît d'un numéro **prouvé** par un code SMS. Un mot
 * de passe qui créerait le compte permettrait d'en ouvrir un sur le numéro de
 * quelqu'un d'autre, et de recevoir à sa place ses notifications de livraison.
 *
 * Un numéro inconnu et un compte sans mot de passe rendent **la même erreur**,
 * parce que l'écran doit faire la même chose dans les deux cas : basculer sur
 * le code SMS.
 */
export function ouvrirUneSessionParMotDePasse(
  entree: { telephone: string; mot_de_passe: string },
  signal?: AbortSignal,
): Promise<SessionOuverte> {
  return appeler("/comptes/session-mot-de-passe/", {
    methode: "POST",
    corps: entree,
    signal,
  });
}

/**
 * Poser un mot de passe, ou en changer. **Appel authentifié.**
 *
 * ⚠️ **`ancien_mot_de_passe` est exigé dès qu'il y en a un**, et il faut
 * résister à la tentation de l'omettre : la session est déjà ouverte, donc
 * techniquement elle suffirait. Mais le jeton vit dans le `localStorage` et
 * survit à la fermeture de l'onglet (voir l'en-tête). La différence est celle
 * entre **voir** les commandes de quelqu'un et **lui prendre son compte
 * définitivement** : sans l'ancien mot de passe, un téléphone prêté cinq
 * minutes suffit à verrouiller son propriétaire dehors pour de bon.
 *
 * À la première définition, rien d'autre n'est demandé : la session a été
 * ouverte par un code SMS, donc le numéro a été prouvé.
 */
export function definirLeMotDePasse(
  entree: { mot_de_passe: string; ancien_mot_de_passe?: string },
  signal?: AbortSignal,
): Promise<Profil> {
  return appeler("/comptes/moi/mot-de-passe/", {
    methode: "POST",
    corps: entree,
    signal,
  });
}

/**
 * Le profil, avec le jeton retenu. **C'est la reconnexion automatique.**
 *
 * Appelée au lancement : si elle répond, l'acheteur est connecté sans rien
 * faire ; si elle répond 401, le jeton est périmé et on l'oublie.
 */
export function lireMonProfil(signal?: AbortSignal): Promise<Profil> {
  return appeler("/comptes/moi/", { signal });
}

/** Révoque **cette** session côté serveur, et oublie le jeton ici. */
export async function seDeconnecter(): Promise<void> {
  try {
    await appeler("/comptes/deconnexion/", { methode: "POST", corps: {} });
  } catch {
    /* Le serveur est injoignable : on oublie quand même le jeton localement.
       Mieux vaut une session orpheline côté serveur — qui expirera — qu'un
       acheteur qui croit s'être déconnecté et ne l'est pas. */
  }
  oublierLeJeton();
}

/**
 * Complete son profil — le nom, l'adresse. **Appel authentifie.**
 *
 * Elle existe parce que le nom est demande *apres* le code : prouver qu'on a
 * le telephone est la seule chose qui engage, et un formulaire pose avant
 * cette preuve serait rempli par n'importe qui. Mais une fois le code valide,
 * la session est ouverte et le code consomme — il faut donc un second appel.
 *
 * ⚠️ **Seuls les champs fournis changent.** Envoyer `{nom}` n'efface pas
 * l'adresse : quelqu'un qui se reconnecte depuis un autre appareil ne doit pas
 * decouvrir son adresse perdue au moment de commander.
 */
export function completerMonProfil(
  champs: {
    nom?: string;
    courriel?: string;
    quartier?: string;
    repere?: string;
  },
  signal?: AbortSignal,
): Promise<Profil> {
  return appeler("/comptes/moi/profil/", {
    methode: "PATCH",
    corps: champs,
    signal,
  });
}
