/**
 * Le seul point de contact avec l'API.
 *
 * Django protège les écritures par un jeton CSRF déposé dans un cookie ; tout
 * passer par ici garantit qu'aucun appel ne l'oublie — une requête qui
 * l'oublie échoue en 403 sans rien dire d'utile.
 */

// `||` et non `??` : une chaîne vide **n'est pas nullish**. Avec
// `VITE_API_URL=` déclarée mais vide — ce qui est le cas voulu, pour passer
// par le relais — `??` aurait rendu "" et toutes les requêtes seraient
// parties sur « /comptes/moi/ » au lieu de « /api/comptes/moi/ ».
const BASE = import.meta.env.VITE_API_URL?.trim() || "/api";

export class ErreurApi extends Error {
  constructor(
    public statut: number,
    message: string,
    public champs: Record<string, string[]> = {},
  ) {
    super(message);
    this.name = "ErreurApi";
  }

  /** Le message à afficher pour un champ donné, s'il y en a un. */
  pourChamp(nom: string): string | undefined {
    return this.champs[nom]?.[0];
  }
}

function lireCookie(nom: string): string | null {
  const trouve = document.cookie
    .split("; ")
    .find((morceau) => morceau.startsWith(`${nom}=`));
  return trouve ? decodeURIComponent(trouve.split("=").slice(1).join("=")) : null;
}

function messageLisible(donnees: unknown, statut: number): string {
  if (typeof donnees === "string" && donnees) return donnees;
  if (donnees && typeof donnees === "object") {
    const objet = donnees as Record<string, unknown>;
    if (typeof objet.detail === "string") return objet.detail;
    // Erreurs de validation : on remonte la première, les autres restent
    // disponibles champ par champ pour l'affichage sous les saisies.
    const premier = Object.values(objet)[0];
    if (Array.isArray(premier) && typeof premier[0] === "string") return premier[0];
  }
  if (statut >= 500) return "Le serveur a rencontré un problème. Réessayez.";
  return "Une erreur est survenue.";
}

async function requete<T>(
  chemin: string,
  options: RequestInit & { corps?: unknown } = {},
): Promise<T> {
  const { corps, ...reste } = options;
  const entetes = new Headers(reste.headers);

  const estEcriture = !["GET", "HEAD", "OPTIONS"].includes(
    (reste.method ?? "GET").toUpperCase(),
  );
  if (estEcriture) {
    const jeton = lireCookie("csrftoken");
    if (jeton) entetes.set("X-CSRFToken", jeton);
  }

  let charge: BodyInit | undefined;
  if (corps instanceof FormData) {
    // Surtout pas de Content-Type à la main ici : le navigateur doit poser
    // lui-même la frontière multipart, sinon le fichier n'arrive pas.
    charge = corps;
  } else if (corps !== undefined) {
    entetes.set("Content-Type", "application/json");
    charge = JSON.stringify(corps);
  }

  const reponse = await fetch(`${BASE}${chemin}`, {
    ...reste,
    headers: entetes,
    body: charge,
    credentials: "include",
  });

  if (reponse.status === 204) return undefined as T;

  const texte = await reponse.text();
  const donnees = texte ? JSON.parse(texte) : null;

  if (!reponse.ok) {
    const champs =
      donnees && typeof donnees === "object" && !Array.isArray(donnees)
        ? (donnees as Record<string, string[]>)
        : {};
    throw new ErreurApi(reponse.status, messageLisible(donnees, reponse.status), champs);
  }
  return donnees as T;
}

export const api = {
  get: <T>(chemin: string) => requete<T>(chemin),
  post: <T>(chemin: string, corps?: unknown) =>
    requete<T>(chemin, { method: "POST", corps }),
  patch: <T>(chemin: string, corps?: unknown) =>
    requete<T>(chemin, { method: "PATCH", corps }),
  delete: <T>(chemin: string) => requete<T>(chemin, { method: "DELETE" }),
};

/** Construit une chaîne de requête en ignorant ce qui est vide. */
export function parametres(valeurs: Record<string, string | number | undefined>): string {
  const utiles = Object.entries(valeurs).filter(
    ([, valeur]) => valeur !== undefined && valeur !== "",
  );
  if (!utiles.length) return "";
  return `?${new URLSearchParams(utiles.map(([c, v]) => [c, String(v)])).toString()}`;
}
