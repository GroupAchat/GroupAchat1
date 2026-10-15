/**
 * La couche d'appel a l'API Django. **Le seul endroit du front qui fasse un
 * `fetch`.**
 *
 * ## Pourquoi tout passe par ici
 *
 * Trois choses doivent etre traitees **une fois** et de la meme facon partout,
 * sans quoi elles sont traitees vingt fois et mal :
 *
 * - **l'adresse du serveur**, qui change entre la machine du developpeur et le
 *   VPS. Elle se lit dans `VITE_API_URL` et nulle part ailleurs ;
 * - **les erreurs de champ** que DRF renvoie en 400. Elles arrivent sous la
 *   forme `{"quartier": ["..."]}` et doivent remonter aux formulaires telles
 *   quelles, pour s'afficher **sous la bonne case** plutot que dans un bandeau
 *   generique ;
 * - **la coupure reseau**, qui n'est pas un cas limite ici. Le §5 du cahier
 *   des charges part d'un forfait de donnees limite et d'une connexion
 *   irreguliere : un `fetch` qui echoue est l'ordinaire, pas l'accident. Il
 *   doit produire un message en francais qui dit quoi faire, jamais un
 *   « Failed to fetch » dans la console.
 *
 * ## Ce que cette couche ne fait pas
 *
 * **Elle ne met rien en cache et ne reessaie pas toute seule.** Un reessai
 * automatique sur un `POST` doublerait une commande ; un cache invisible
 * ferait afficher un groupage cloture comme ouvert. Les deux se decident au
 * cas par cas, par l'ecran qui sait ce qu'il affiche.
 */

/**
 * L'adresse de l'API.
 *
 * `VITE_API_URL` se renseigne dans `frontend/.env.local` (ignore par git) ou
 * dans l'environnement de construction. Le defaut vise le `runserver` local,
 * ce qui permet de cloner le depot et de travailler sans rien configurer.
 */
export const BASE_API: string =
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api";

/**
 * Le jeton de session de l'acheteur, attache a **tous** les appels.
 *
 * ⚠️ **Gardé ici plutôt que passé en paramètre à chaque fonction**, et c'est
 * un choix : passé en paramètre, il serait oublié une fois — et cet oubli ne
 * se verrait pas, puisque l'appel aboutirait quand même (en anonyme), avec
 * une liste vide ou un 401 selon la route. Un trou de ce genre se cherche
 * longtemps.
 *
 * Ce n'est pas un etat partage au sens de React : rien ne se re-rend quand il
 * change. C'est l'appelant — `App` — qui tient l'etat visible, et qui pose ce
 * jeton quand il change.
 */
let jetonAcheteur = "";

/** Pose le jeton employe par les appels suivants. Vide = anonyme. */
export function poserLeJetonAcheteur(jeton: string): void {
  jetonAcheteur = jeton;
}

/** Les erreurs de champ renvoyees par DRF : `{"quartier": ["..."]}`. */
export type ErreursDeChamp = Record<string, string[]>;

/**
 * Une requete qui n'a pas abouti.
 *
 * `statut` vaut **0 quand le serveur n'a pas repondu du tout** — coupure,
 * serveur eteint, DNS. C'est volontairement distinct d'un 500 : « vous n'avez
 * pas de connexion » et « notre serveur a un probleme » appellent deux
 * reactions differentes de la part de l'utilisateur, et une seule des deux est
 * de son ressort.
 */
export class ErreurApi extends Error {
  readonly statut: number;
  readonly champs: ErreursDeChamp;

  constructor(message: string, statut: number, champs: ErreursDeChamp = {}) {
    super(message);
    this.name = "ErreurApi";
    this.statut = statut;
    this.champs = champs;
  }

  /** Le serveur n'a pas repondu : c'est le reseau, pas l'application. */
  get estHorsLigne(): boolean {
    return this.statut === 0;
  }

  /** Une saisie a ete refusee : les messages vont sous les cases. */
  get estRefusDeSaisie(): boolean {
    return this.statut === 400;
  }

  /**
   * La session a expire, ou il n'y en a pas.
   *
   * ⚠️ **Distinct du 403**, et la distinction commande deux ecrans :
   *
   * - **401** — « je ne sais pas qui vous etes » : rouvrir la feuille de
   *   connexion, et oublier le jeton qu'on gardait ;
   * - **403** — « je sais, et c'est non » : afficher un refus.
   *
   * Les confondre laisserait quelqu'un dont la session a simplement expire
   * devant un « acces refuse », sans moyen de revenir.
   */
  get sessionExpiree(): boolean {
    return this.statut === 401;
  }

  /**
   * Le message a montrer quand on n'a pas de case ou l'accrocher.
   *
   * Il dit **ce qui s'est passe et quoi faire**, dans cet ordre. « Erreur 500 »
   * n'apprend rien a quelqu'un qui voulait acheter des ecouteurs.
   */
  get messageLisible(): string {
    if (this.estHorsLigne) {
      return "Pas de connexion. Vérifiez vos données mobiles, puis réessayez.";
    }
    if (this.statut === 404) {
      return "Cette page n'existe plus. Elle a peut-être été clôturée.";
    }
    if (this.sessionExpiree) {
      return "Votre session a expiré. Reconnectez-vous avec votre numéro.";
    }
    if (this.statut === 403) {
      return "Vous n'avez pas accès à cette page.";
    }
    if (this.statut >= 500) {
      return "Notre serveur a un problème. Réessayez dans un instant — ce n'est pas vous.";
    }
    return this.message;
  }
}

/** Ce qu'on peut passer a `appeler`. */
interface Options {
  methode?: "GET" | "POST" | "PATCH" | "DELETE";
  corps?: unknown;
  /** Les parametres d'adresse, encodes ici pour ne pas l'oublier. */
  parametres?: Record<string, string | number | undefined>;
  /**
   * Le jeton d'administration, pour les routes `/dossiers/`.
   *
   * ⚠️ **Rien à voir avec celui de l'acheteur.** Deux mécanismes distincts,
   * deux en-têtes, deux publics : `X-Jeton-Admin` ouvre les dossiers KYC de
   * tout le monde, `Authorization: Jeton` ouvre son propre compte. Les
   * confondre donnerait à un acheteur l'annuaire des groupeurs.
   */
  jetonAdmin?: string;
  /** `true` pour un appel volontairement anonyme — la connexion elle-même. */
  sansJeton?: boolean;
  /** Pour annuler une requete devenue inutile — voir `useRequete`. */
  signal?: AbortSignal;
}

/**
 * Un corps de requete : du JSON, ou un formulaire multipart.
 *
 * ⚠️ **Un `FormData` ne doit jamais etre passe a `JSON.stringify`**, qui en
 * ferait `{}` — le fichier partirait a la poubelle et le serveur repondrait
 * 201 sur une demande sans photo. C'est pour rendre cette faute impossible
 * que le type est explicite plutot que `unknown`.
 */

/**
 * Appelle l'API et rend le corps decode.
 *
 * Leve une `ErreurApi` dans tous les cas d'echec, **y compris reseau** : un
 * seul type d'erreur a attraper, donc un seul chemin a ecrire dans les
 * ecrans.
 */
export async function appeler<T>(
  chemin: string,
  options: Options = {},
): Promise<T> {
  const {
    methode = "GET",
    corps,
    parametres,
    jetonAdmin,
    sansJeton,
    signal,
  } = options;

  const adresse = new URL(`${BASE_API}${chemin}`);
  for (const [cle, valeur] of Object.entries(parametres ?? {})) {
    /* `undefined` veut dire « ne pas envoyer ce filtre », pas « envoyer le mot
       undefined » — erreur classique qui produit des filtres fantomes. */
    if (valeur !== undefined && valeur !== "") {
      adresse.searchParams.set(cle, String(valeur));
    }
  }

  const multipart = corps instanceof FormData;

  const entetes: Record<string, string> = {};
  /* ⚠️ **Aucun `Content-Type` sur un envoi multipart.** C'est le navigateur
     qui doit le poser, parce que lui seul connait la frontiere (`boundary`)
     qu'il vient de tirer au hasard. En ecrire un a la main produit un corps
     que le serveur ne sait pas decouper : DRF repond alors 400 sur un
     formulaire parfaitement valide, et l'erreur est penible a diagnostiquer
     puisque le fichier est bien parti. */
  if (corps !== undefined && !multipart) {
    entetes["Content-Type"] = "application/json";
  }
  if (jetonAdmin) {
    entetes["X-Jeton-Admin"] = jetonAdmin;
  }
  if (jetonAcheteur && !sansJeton) {
    entetes.Authorization = `Jeton ${jetonAcheteur}`;
  }

  let reponse: Response;
  try {
    reponse = await fetch(adresse, {
      method: methode,
      headers: entetes,
      body:
        corps === undefined
          ? undefined
          : multipart
            ? corps
            : JSON.stringify(corps),
      signal,
    });
  } catch (cause) {
    /* ⚠️ Une annulation volontaire n'est **pas** une panne : elle se produit a
       chaque frappe dans la barre de recherche. La laisser remonter comme une
       erreur ferait clignoter « pas de connexion » pendant qu'on tape. */
    if (cause instanceof DOMException && cause.name === "AbortError") {
      throw cause;
    }
    throw new ErreurApi("Le serveur n'a pas répondu.", 0);
  }

  if (reponse.status === 204) {
    return undefined as T;
  }

  const texte = await reponse.text();
  let donnees: unknown = undefined;
  if (texte) {
    try {
      donnees = JSON.parse(texte);
    } catch {
      /* Une page d'erreur HTML plutot que du JSON : c'est ce que renvoie
         Django en 500 avec `DEBUG=True`. On ne la montre pas a l'utilisateur,
         mais on n'avale pas le statut non plus. */
      if (!reponse.ok) {
        throw new ErreurApi("Réponse inattendue du serveur.", reponse.status);
      }
    }
  }

  if (!reponse.ok) {
    throw new ErreurApi(
      messageDepuisLeCorps(donnees),
      reponse.status,
      champsDepuisLeCorps(donnees),
    );
  }

  return donnees as T;
}

/**
 * La reponse paginee de DRF.
 *
 * `PAGE_SIZE` vaut 24 cote serveur. Les ecrans qui affichent une liste doivent
 * donc lire `results`, pas le corps entier — oubli qui produit une liste vide
 * sans erreur, et qu'on met longtemps a trouver.
 */
export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

function champsDepuisLeCorps(donnees: unknown): ErreursDeChamp {
  if (!donnees || typeof donnees !== "object" || Array.isArray(donnees)) {
    return {};
  }
  const champs: ErreursDeChamp = {};
  for (const [cle, valeur] of Object.entries(
    donnees as Record<string, unknown>,
  )) {
    if (Array.isArray(valeur)) {
      champs[cle] = valeur.map(String);
    } else if (typeof valeur === "string") {
      champs[cle] = [valeur];
    }
  }
  return champs;
}

function messageDepuisLeCorps(donnees: unknown): string {
  const champs = champsDepuisLeCorps(donnees);
  /* `detail` est la cle que DRF emploie pour une erreur qui ne vise pas un
     champ ; on la prefere si elle est la. */
  const premier = champs.detail ?? Object.values(champs)[0];
  return premier?.[0] ?? "La requête a échoué.";
}
