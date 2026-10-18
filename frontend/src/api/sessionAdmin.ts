import { appeler } from "./client";

/**
 * La connexion a l'administration.
 *
 * ## ⚠️ Ce que ce fichier remplace
 *
 * L'administration etait ouverte par un **jeton unique et partage**, pose dans
 * le `.env` du serveur sous `JETON_ADMIN` et recopie a la main par chaque
 * administrateur. `jeton.ts` l'admettait lui-meme : *« ce n'est toujours pas
 * de l'authentification [...] le jour ou les comptes existent, ce fichier
 * disparait au profit d'une session »*. Les comptes existent.
 *
 * | | Le jeton partage | La session |
 * |---|---|---|
 * | Distingue deux administrateurs | non | **oui** |
 * | Se revoque pour une personne | non — il fallait le changer pour tous | **oui** |
 * | Resiste a l'essai systematique | rien ne comptait les echecs | **cinq essais, puis quinze minutes** |
 * | « decide par » sur une decision KYC | ce qu'on voulait bien saisir | **le compte connecte** |
 *
 * ## ⚠️ L'en-tete n'a pas change de nom, mais a change de nature
 *
 * On envoie toujours `X-Jeton-Admin`, et c'est delibere : l'en-tete n'a jamais
 * ete autre chose qu'un transport, et le renommer aurait touche les vingt-deux
 * endroits du client qui le posent deja. **Mais ce qu'il porte n'est plus un
 * secret partage** : c'est un jeton de session personnel, tire au hasard sur
 * 256 bits, qui expire au bout de douze heures et se revoque tout seul si le
 * compte perd `is_staff`.
 */

/** Ce que le serveur rend a une connexion reussie. */
export interface SessionAdmin {
  jeton: string;
  /** Le nom tel qu'il sera inscrit sur les decisions KYC. */
  nom: string;
  expire_le: string;
}

export function seConnecter(
  identifiant: string,
  motDePasse: string,
  signal?: AbortSignal,
): Promise<SessionAdmin> {
  return appeler<SessionAdmin>("/session-admin/connexion/", {
    methode: "POST",
    corps: { identifiant, mot_de_passe: motDePasse },
    /* ⚠️ **Sans le jeton acheteur.** Le navigateur de la personne qui
       administre peut tres bien porter une session acheteur — c'est le cas sur
       le poste de developpement, et ce sera le cas d'un administrateur qui a
       aussi un compte. L'envoyer ici melangerait les deux publics sur une
       route qui ne parle pas d'acheteurs. */
    sansJeton: true,
    signal,
  });
}

/*
 * ⚠️ **Il n'y a volontairement pas de `lireMonIdentiteAdmin` ici**, alors que
 * la route `/session-admin/moi/` existe cote serveur.
 *
 * J'en avais ecrit une, en annoncant que l'ecran l'appelait au chargement pour
 * valider le jeton garde dans le `sessionStorage`. **C'etait faux** : rien ne
 * l'appelait, et le paquet construit le prouvait — `session-admin/moi`
 * n'apparaissait pas dans le JavaScript produit alors que `connexion` et
 * `deconnexion` y etaient, Rollup l'ayant eliminee comme inutilisee.
 *
 * Et elle n'a pas de raison d'etre appelee : la premiere chose que fait
 * l'administration apres l'ouverture est de charger son tableau de bord. Si
 * la session est morte, cet appel revient en 401, `main.tsx` oublie la session
 * et rouvre la feuille de connexion. Ajouter `moi/` ferait **une requete de
 * plus pour apprendre ce que la suivante allait dire de toute facon**.
 *
 * La route reste cote serveur : elle est testee, et c'est elle qui permet de
 * verifier une session a la main sans toucher a des donnees personnelles.
 */

/**
 * Ferme cette session cote serveur.
 *
 * ⚠️ **Oublier le jeton dans le navigateur ne suffisait pas** : avec le jeton
 * partage, il n'y avait rien a fermer — la valeur restait valable pour qui
 * l'avait notee. Ici la session est detruite en base, donc un jeton recopie
 * ailleurs cesse de fonctionner.
 *
 * Les autres sessions du meme compte survivent : fermer l'onglet du poste
 * partage ne doit pas deconnecter la meme personne de son propre telephone.
 */
export function seDeconnecter(jetonAdmin: string): Promise<void> {
  return appeler<void>("/session-admin/deconnexion/", {
    methode: "POST",
    jetonAdmin,
    sansJeton: true,
  });
}
