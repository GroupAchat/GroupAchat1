/**
 * Le mode démonstration — **les deux inscriptions, acheteur et groupeur**.
 *
 * ## Ce qu'il fait
 *
 * Il permet de traverser l'inscription groupeur **en appuyant sur
 * « Continuer »**, sans rien saisir, jusqu'à l'espace groupeur. Les champs
 * restent à l'écran, pré-remplis, et aucun bouton n'est grisé : on montre les
 * écrans sans taper au clavier devant quelqu'un qui regarde.
 *
 * Côté serveur, le réglage `DEMONSTRATION` valide le dossier sur-le-champ —
 * sinon on arriverait sur le tableau de bord en attente, celui où la création
 * de groupage est fermée.
 *
 * ## Ce qu'il suspend, et c'est sérieux
 *
 * L'**examen du dossier par un humain** (§10.5). C'est lui qui donne son sens
 * à « vous êtes livré, ou remboursé », la phrase qui s'affiche à
 * l'acheteur sur presque chaque écran et sur laquelle repose son acceptation
 * de payer d'avance.
 *
 * ⚠️ **Ce paragraphe disait : « Rien ici ne touche au parcours acheteur ».**
 * Ce n'est plus vrai : le formulaire d'inscription acheteur est pré-rempli lui
 * aussi, et les quatre cases du code le sont à l'arrivée sur l'étape 2. La
 * phrase est reproduite pour qu'on ne la restaure pas par réflexe.
 *
 * **Ce qui n'a pas changé et ne doit pas changer** : le code est toujours
 * **vérifié par le serveur**. On le pré-remplit, on ne le contourne pas. Les
 * conditions de vente et l'adresse de livraison restent demandées comme
 * avant.
 *
 * ## Comment on rallume la sécurité
 *
 * `VITE_DEMONSTRATION=0` et `DEMONSTRATION=0` dans le `.env` de la racine —
 * l'un pour l'interface, l'autre pour le serveur.
 *
 * ⚠️ **Éteint tant qu'on ne l'allume pas.** Un drapeau de démonstration
 * oublié à `true` est l'accident classique, et celui-ci ferait entrer
 * n'importe qui dans l'espace groupeur. Il se demande donc, comme son jumeau
 * côté serveur.
 *
 * ⚠️ **Les deux vont par paire.** L'interface allumée sans le serveur
 * déposerait un dossier qui part vraiment en file d'attente, et on arriverait
 * sur le tableau de bord en attente — l'état le plus déroutant des deux.
 */

export const DEMONSTRATION = import.meta.env.VITE_DEMONSTRATION === "1";

/**
 * Le dossier pré-rempli de l'inscription groupeur.
 *
 * ⚠️ **Le numéro est tiré à chaque chargement de la page**, et ce n'est pas un
 * détail : le téléphone est l'identifiant d'un compte groupeur, donc un numéro
 * fixe ferait échouer la deuxième démonstration avec « ce numéro est déjà
 * utilisé » — exactement au moment où quelqu'un regarde.
 *
 * `91` en tête pour rester hors des numéros du jeu de démonstration, qui
 * commencent par `9100000…`.
 */
function numeroLibre(): string {
  const suite = String(Date.now()).slice(-6);
  return `9${suite.slice(0, 1)} ${suite.slice(1, 3)} ${suite.slice(3, 5)} ${suite.slice(5)}4`;
}

const NUMERO = numeroLibre();

export const GROUPEUR_DEMO = {
  /** Un pseudonyme reconnaissable : on doit voir que c'est une démonstration. */
  pseudonyme: `Démo ${NUMERO.slice(0, 2)}${NUMERO.slice(3, 5)}`,
  nomComplet: "Kodjo Adanlété",
  /** Sans le `+228`, comme le champ l'attend. */
  telephone: NUMERO,
  courriel: "demo@exemple.tg",
  numeroPiece: "1234567890",
  /**
   * Le titulaire Mobile Money **doit concorder** avec le nom complet : c'est
   * le contrôle n° 2 du §10.5, et le serveur le refuse sinon. Écrit dans
   * l'autre ordre exprès — la concordance doit le tolérer.
   */
  titulaire: "ADANLÉTÉ Kodjo",
  code: "1234",
} as const;

/**
 * Le formulaire d'inscription acheteur, pré-rempli.
 *
 * ⚠️ **Son numéro est tiré à chaque chargement, pour la même raison que celui
 * du groupeur** : le téléphone identifie le compte, donc un numéro fixe ferait
 * échouer la deuxième démonstration sur « ce numéro a déjà un compte » — et
 * l'écran basculerait vers la connexion, exactement au moment où un jury
 * regarde. Il réutilise `numeroLibre()`, et les deux tirages diffèrent parce
 * qu'ils sont faits à deux instants.
 *
 * **Un prénom, pas un nom complet** : c'est ce que le formulaire demande, et
 * c'est tout ce dont le livreur a besoin le jour de la remise.
 */
export const ACHETEUR_DEMO = {
  prenom: "Akosua",
  /** Sans le `+228`, comme le champ l'attend. */
  telephone: numeroLibre(),
  courriel: "akosua@exemple.tg",
  /** Le même code fixe que le serveur sert en mode démonstration. */
  code: "1234",
} as const;

/** La valeur de départ d'un champ : vide hors démonstration. */
export function valeurDemo(valeur: string): string {
  return DEMONSTRATION ? valeur : "";
}
