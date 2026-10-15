/**
 * Partager un groupage, et le retrouver depuis le lien partage.
 *
 * ## Pourquoi ce module existe
 *
 * Quatre boutons « Partager » etaient dessines — sur la fiche, sur le fil, sur
 * la gestion de campagne — et **aucun ne faisait quoi que ce soit**. Ce
 * n'etait pas qu'une negligence d'implementation : il n'y avait **rien a
 * partager**, puisque l'application ne savait pas ouvrir une fiche depuis une
 * adresse. Un lien colle dans WhatsApp ramenait sur le catalogue.
 *
 * Or le `CLAUDE.md` tient pour non negociable qu'« un groupage cloture quitte
 * le catalogue, mais **sa fiche reste atteignable par son lien** ». Le filtre
 * serveur etait bien en place — `retrieve` repond encore sur un groupage
 * ferme, et un test le verifie — mais **personne ne pouvait fabriquer ce
 * lien**. La regle existait a moitie : la moitie serveur.
 *
 * ## `?groupage=<id>`, pas un chemin
 *
 * La boutique n'a pas de routeur : la navigation est un `useState` dans
 * `ApplicationAcheteur`. Un vrai chemin (`/groupage/9`) exigerait que le
 * serveur qui sert les fichiers renvoie `index.html` sur n'importe quelle
 * adresse, ce qui est une decision de deploiement et non de code — et le
 * `?role=livreur` du §6 montre que ce produit sait deja entrer par un
 * parametre. On reste donc sur un parametre, qui marche partout sans
 * configuration.
 */

/**
 * L'identifiant lu dans l'adresse, s'il y en a un.
 *
 * ⚠️ **Il reste une chaine**, comme `Groupage.id` : c'est l'API qui decide de
 * sa forme, et le convertir en nombre ici obligerait a le reconvertir avant
 * chaque appel. On se contente donc de verifier qu'il **ressemble a un
 * identifiant** — des chiffres, et rien d'autre. Sans ce filtre, un parametre
 * bricole part tel quel dans une adresse d'API.
 */
export function groupageDepuisAdresse(): string | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  const demande = new URLSearchParams(window.location.search).get("groupage");
  return demande !== null && /^[0-9]+$/.test(demande) ? demande : undefined;
}

/** Le lien public d'un groupage, tel qu'on le colle dans une conversation. */
export function lienGroupage(identifiant: string): string {
  const { origin, pathname } = window.location;
  return `${origin}${pathname}?groupage=${identifiant}`;
}

/**
 * Inscrit le groupage ouvert dans l'adresse, **sans ajouter d'entree
 * d'historique**.
 *
 * `replaceState` et non `pushState` : le retour arriere du navigateur n'est
 * pas branche sur l'etat de l'application, donc empiler des entrees donnerait
 * un bouton « precedent » qui change l'adresse sans changer l'ecran. Ce qu'on
 * veut ici est plus modeste et suffit : que la barre d'adresse soit copiable,
 * et que recharger la page revienne sur la meme fiche.
 */
export function inscrireLeGroupageDansLAdresse(
  identifiant: string | undefined,
): void {
  if (typeof window === "undefined") {
    return;
  }
  const adresse = new URL(window.location.href);
  if (identifiant === undefined) {
    adresse.searchParams.delete("groupage");
  } else {
    adresse.searchParams.set("groupage", identifiant);
  }
  window.history.replaceState(null, "", adresse.toString());
}

/** Ce que le partage a reellement fait, pour pouvoir le dire a l'ecran. */
export type ResultatPartage = "partage" | "copie" | "echec";

/**
 * Partage un groupage par le moyen que l'appareil propose.
 *
 * Trois chemins, du meilleur au dernier recours :
 *
 * 1. **`navigator.share`** — la feuille de partage du systeme. C'est le bon
 *    geste sur un telephone : elle ouvre WhatsApp, qui est la ou se partage
 *    reellement un bon plan a Lome.
 * 2. **Le presse-papier** — sur un ordinateur, `navigator.share` n'existe
 *    souvent pas. Copier le lien est le comportement attendu, a condition de
 *    **le dire** : un bouton qui copie en silence passe pour un bouton mort,
 *    c'est-a-dire exactement le defaut qu'on corrige. D'ou le retour
 *    `"copie"`, que l'appelant affiche.
 * 3. **`"echec"`** — le presse-papier est refuse hors contexte securise, et
 *    on ne peut pas le forcer. Mieux vaut le dire que laisser croire.
 *
 * ⚠️ **Une annulation n'est pas un echec.** Fermer la feuille de partage
 * rejette la promesse avec `AbortError`. Afficher « echec » la serait
 * reprocher a quelqu'un d'avoir change d'avis.
 */
export async function partager(contenu: {
  titre: string;
  texte: string;
  lien: string;
}): Promise<ResultatPartage> {
  const charge = {
    title: contenu.titre,
    text: contenu.texte,
    url: contenu.lien,
  };

  if (typeof navigator !== "undefined" && navigator.share) {
    try {
      await navigator.share(charge);
      return "partage";
    } catch (erreur) {
      if (erreur instanceof Error && erreur.name === "AbortError") {
        return "partage";
      }
      /* Autre chose qu'une annulation : on tente quand meme le
         presse-papier plutot que d'abandonner. */
    }
  }

  try {
    await navigator.clipboard.writeText(contenu.lien);
    return "copie";
  } catch {
    return "echec";
  }
}
