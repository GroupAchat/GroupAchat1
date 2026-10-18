import type { SessionAdmin } from "../api/sessionAdmin";

/**
 * La session d'administration gardee dans le navigateur : ou elle vit.
 *
 * ## ⚠️ Rien n'est **dans le paquet construit**, et ce n'est pas negociable
 *
 * La solution evidente, du temps du jeton partage, aurait ete une variable
 * `VITE_JETON_ADMIN` lue a la construction. **Elle etait fausse**, et d'une
 * facon qui ne se voyait pas : tout ce que Vite remplace dans le code se
 * retrouve **en clair dans le JavaScript livre**. N'importe qui ouvrant la
 * page d'administration — ou simplement son fichier `.js` — aurait lu le
 * jeton, puis appele `/api/dossiers/` depuis n'importe ou pour lire des noms,
 * des numeros de telephone et des references de pieces d'identite.
 *
 * Mettre un secret dans un paquet front, c'est le publier. Le fait que la
 * page soit servie sur un autre port n'y change rien : elle est servie a qui
 * la demande.
 *
 * ⚠️ **Ce piege a disparu avec le jeton partage**, mais la regle reste : ce
 * qui est garde ici est obtenu **a l'execution**, contre un mot de passe, et
 * n'existe que dans le navigateur de la personne connectee.
 *
 * ## Le `sessionStorage`, et pas le `localStorage`
 *
 * | | `sessionStorage` | `localStorage` |
 * |---|---|---|
 * | Ferme l'onglet | oublie | **garde pour toujours** |
 * | Poste partage | sur | le suivant est administrateur |
 *
 * Sur un poste partage, et plus encore sur un portable qu'on emporte, un acces
 * qui survit a la fermeture de l'onglet est un acces qu'on a oublie avoir
 * laisse. Le serveur pose deja une limite de douze heures ; celle-ci est
 * complementaire, parce qu'elle ne depend pas du temps mais du geste.
 *
 * ## ⚠️ Ce que ce fichier ne garantit pas, et n'a pas a garantir
 *
 * **Ce qui est ici n'est pas une preuve d'identite, c'est un cache.** Le
 * serveur revalide la session a chaque requete — expiration, et `is_staff`
 * relu a chaque fois, pour qu'une revocation prenne effet tout de suite. Un
 * jeton garde ici apres une revocation ne vaut donc rien : il produira un 401,
 * que `main.tsx` traduit en reouverture de la feuille de connexion.
 *
 * ⚠️ Ce fichier annoncait sa propre disparition : *« le jour ou les comptes
 * existent, ce fichier disparait au profit d'une session »*. Il ne disparait
 * pas, il change d'objet — il faut toujours un endroit ou garder la session
 * entre deux rendus. Ce qu'il gardait etait un **secret partage** ; ce qu'il
 * garde est **le jeton personnel d'une session**, avec le nom qui signera les
 * decisions KYC.
 */

const CLE = "groupachat.session-admin";

/** La session de cet onglet, si quelqu'un s'est connecte. */
export function lireLaSession(): SessionAdmin | null {
  try {
    const brut = sessionStorage.getItem(CLE);
    if (!brut) {
      return null;
    }
    const session = JSON.parse(brut) as SessionAdmin;
    /* ⚠️ On verifie la forme plutot que de faire confiance au contenu. Ce
       n'est pas de la paranoia : la cle a change de contenu (une chaine
       autrefois, un objet maintenant), donc un onglet ouvert au moment du
       deploiement peut relire l'ancien format. Sans ce controle, `session.nom`
       vaudrait `undefined` et la barre laterale afficherait un vide a
       l'endroit exact ou elle doit dire qui signe. */
    return typeof session?.jeton === "string" && session.jeton
      ? session
      : null;
  } catch {
    /* Navigation privee, stockage bloque par une politique d'entreprise, JSON
       corrompu : on redemande la connexion plutot que de planter.
       L'administrateur la refera a chaque ouverture, ce qui est penible mais
       pas bloquant. */
    return null;
  }
}

export function retenirLaSession(session: SessionAdmin): void {
  try {
    sessionStorage.setItem(CLE, JSON.stringify(session));
  } catch {
    /* Sans stockage, la session vit dans l'etat React de la page : elle marche
       jusqu'au rechargement. */
  }
}

/** Oublie la session — le « Fermer la session » de l'administration.
 *
 * ⚠️ **Oublier ne ferme pas.** C'est `seDeconnecter` qui detruit la session
 * cote serveur, et c'est la seule chose qui la rend reellement inutilisable.
 * Appeler celle-ci seule laisserait un jeton valide douze heures entre les
 * mains de qui l'aurait note. `main.tsx` appelle les deux.
 */
export function oublierLaSession(): void {
  try {
    sessionStorage.removeItem(CLE);
  } catch {
    /* Rien a oublier si rien n'a jamais pu etre ecrit. */
  }
}
