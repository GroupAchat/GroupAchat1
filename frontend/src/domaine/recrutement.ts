/**
 * Le recrutement d'un groupeur, vu des deux cotes de l'ecran.
 *
 * ⚠️ **Ce fichier est le jumeau de `backend/groupachat/notifications.py`.**
 * Les motifs, les issues et les canaux y sont definis une seconde fois, en
 * TypeScript, et les deux listes doivent rester identiques. C'est une
 * duplication assumee, pas un oubli — et voici pourquoi, parce que la question
 * se reposera :
 *
 * - l'interface doit pouvoir **proposer la liste des motifs** dans un menu
 *   deroulant avant d'avoir appele quoi que ce soit, et afficher le texte que
 *   le groupeur recevra **avant** de trancher. Aller chercher ces libelles par
 *   une requete ferait attendre l'administrateur pour un contenu qui ne change
 *   jamais entre deux versions ;
 * - l'API refuse de toute facon un motif hors liste (`ChoiceField` sur
 *   `notifications.MOTIFS`). **La verite reste cote serveur** : si les deux
 *   listes divergent, c'est l'interface qui a tort, et elle recoit un 400.
 *
 * Le jour ou cette liste bouge souvent, elle sera servie par l'API. Tant
 * qu'elle bouge une fois par an, la dupliquer coute moins que de la charger.
 *
 * ## Le parcours
 *
 * ```
 *  Groupeur                   Administrateur              Groupeur
 *  ────────                   ──────────────              ────────
 *  Inscription (4 etapes)     File d'attente (A2)
 *  + depot des pieces    ──▶  Il etudie le dossier
 *  = dossier en attente       Il tranche + choisit     ──▶ courriel
 *                             le canal d'annonce           ou appel
 *                                                      ──▶ et il relit
 *                                                          son dossier
 * ```
 *
 * **Rien n'est automatique entre les deux colonnes.** Le §10.5 confie la
 * decision a un humain, et c'est le produit lui-meme : « vous etes livre, ou
 * rembourse » s'affiche a l'acheteur sur presque chaque ecran, et c'est
 * **nous** qui remboursons. Notre seul recours contre le groupeur est son
 * dossier, qui ne vaut que si quelqu'un l'a reellement ouvert.
 */

/** L'etat d'un dossier. Il decide de ce que le groupeur peut faire. */
export type EtatDossier =
  | "a-completer"
  | "en-verification"
  | "valide"
  | "refuse";

/**
 * Les trois issues possibles d'un examen.
 *
 * **Trois et non deux.** « A completer » est la plus utile des trois : la
 * plupart des dossiers qui echouent le font sur une photo floue ou une piece
 * prise de travers. Les refuser definitivement ferait perdre des groupeurs
 * recrutables, alors que le recrutement est le goulot d'etranglement du
 * lancement (§10.5).
 */
export type Issue = "valide" | "a-completer" | "refuse";

/**
 * Par ou la decision est annoncee.
 *
 * **Les deux canaux sont de rang egal, l'appel n'est pas un pis-aller.** Une
 * partie du cœur de cible — des commercants de Lome, souvent dans l'informel —
 * n'a pas d'adresse de messagerie consultee mais repond au telephone. C'est
 * pour cette raison que le courriel est facultatif a l'inscription et que le
 * telephone, lui, est obligatoire : ainsi aucun groupeur n'est injoignable.
 */
export type Canal = "courriel" | "appel";

export const LIBELLE_CANAL: Record<Canal, string> = {
  courriel: "Par courriel",
  appel: "Par téléphone",
};

/** La cle d'un motif de decision negative. */
export type Motif =
  | "piece-illisible"
  | "selfie-non-conforme"
  | "dossier-incomplet"
  | "noms-divergents"
  | "telephone-injoignable"
  | "doute-identite"
  | "autre";

interface DetailMotif {
  /** Ce que l'administrateur lit dans sa liste. */
  interne: string;
  /**
   * Ce que le groupeur recoit.
   *
   * ⚠️ Il se lit **comme une raison, pas comme un verdict** : il est insere
   * apres « Votre dossier n'a pas ete valide : ». Un motif qui repete le
   * verdict produit une tautologie — defaut reellement present dans la
   * premiere version du module backend.
   */
  public: string;
  /**
   * Ce qu'il doit faire.
   *
   * ⚠️ Ce texte **se dit autant qu'il s'ecrit** : le meme part en courriel et
   * se lit au telephone. « Repondez a ce message » est donc interdit — il n'y
   * a pas de message dans un appel.
   */
  suite: string;
}

/**
 * Les sept motifs, **liste fermee**.
 *
 * Pourquoi fermee plutot qu'un champ libre : au bout de six mois, un champ
 * libre contient quarante formulations du meme refus. On ne peut alors plus
 * compter *pourquoi* les dossiers echouent — donc plus corriger le formulaire
 * d'inscription qui les fait echouer. Or c'est la seule facon de ne pas
 * refuser indefiniment les memes gens.
 */
export const MOTIFS: Record<Motif, DetailMotif> = {
  "piece-illisible": {
    interne: "Pièce d'identité illisible",
    public:
      "la photo de votre pièce d'identité n'est pas assez lisible pour être vérifiée",
    suite:
      "Reprenez-la à plat, en pleine lumière, sans reflet du flash, et vérifiez que le numéro et la date de naissance se lisent.",
  },
  "selfie-non-conforme": {
    interne: "Selfie non conforme",
    public:
      "sur votre selfie, la pièce d'identité et votre visage ne sont pas visibles ensemble",
    suite:
      "Tenez la pièce à côté de votre visage, les deux dans le cadre, sans masquer la photo de la pièce avec vos doigts.",
  },
  "dossier-incomplet": {
    interne: "Dossier incomplet",
    public: "votre dossier est incomplet",
    suite:
      "Reprenez l'inscription : les pièces manquantes y sont indiquées.",
  },
  "noms-divergents": {
    interne: "Contrôle n° 2 — titulaire Mobile Money différent de la pièce",
    public:
      "le compte Mobile Money indiqué n'est pas à votre nom, alors que c'est sur ce compte que partirait l'argent des acheteurs",
    suite:
      "Ouvrez un compte Mobile Money à votre nom, puis reprenez une inscription. Nous ne pouvons pas verser sur le compte d'un tiers.",
  },
  "telephone-injoignable": {
    interne: "Téléphone injoignable",
    public: "nous n'avons pas réussi à vous joindre au numéro déposé",
    suite:
      "Reprenez l'inscription avec un numéro que vous consultez tous les jours.",
  },
  "doute-identite": {
    interne: "Doute sérieux sur l'identité",
    /* Volontairement sans detail : dire a quelqu'un *ce qui* a eveille le
       doute lui apprend quoi corriger pour recommencer. */
    public:
      "les éléments de votre dossier n'ont pas permis de confirmer votre identité",
    suite:
      "Si vous pensez qu'il s'agit d'une erreur, recontactez-nous : un administrateur reprendra le dossier.",
  },
  autre: {
    interne: "Autre motif",
    public: "votre dossier n'a pas pu être retenu après examen",
    suite: "Recontactez-nous pour en connaître le détail.",
  },
};

/**
 * Les motifs qui se rattrapent **sans reinscription**.
 *
 * Ils determinent l'issue que l'interface propose par defaut : un dossier dont
 * la photo est floue revient « a completer », il ne se refuse pas. C'est un
 * defaut, pas une contrainte — l'administrateur peut toujours refuser.
 */
export const MOTIFS_RATTRAPABLES: readonly Motif[] = [
  "piece-illisible",
  "selfie-non-conforme",
  "dossier-incomplet",
];

/** L'issue proposee d'emblee quand on choisit un motif. */
export function issueProposee(motif: Motif): Issue {
  return MOTIFS_RATTRAPABLES.includes(motif) ? "a-completer" : "refuse";
}

/**
 * Ce que le groupeur peut faire dans l'etat ou est son dossier.
 *
 * ⚠️ **Ce n'est qu'un confort d'affichage.** Le verrou reel est dans
 * `Campagne.save()` cote serveur, qui refuse une campagne d'un groupeur non
 * valide. Un bouton grise ne protege de rien : il suffit d'une requete directe
 * pour le contourner. Les deux existent, et dans cet ordre d'importance.
 */
export function peutLancerUnGroupage(etat: EtatDossier): boolean {
  return etat === "valide";
}

/** Le libelle de l'etat, tel que le groupeur le lit. */
export const LIBELLE_ETAT: Record<EtatDossier, string> = {
  "a-completer": "À compléter",
  "en-verification": "En vérification",
  valide: "Validé",
  refuse: "Non validé",
};

/** Le delai annonce au groupeur a l'inscription, et tenu par l'admin. */
export const DELAI_ANNONCE = "48 h ouvrées";

/**
 * Le texte exact que le groupeur recevra, compose **avant** de trancher.
 *
 * L'administrateur doit pouvoir le relire avant d'appuyer. Sans cela il
 * annonce une decision sans savoir comment elle est formulee, et ne peut pas
 * repondre quand le groupeur rappelle en citant le message.
 *
 * ⚠️ **C'est un apercu, pas la source.** Le message reellement envoye est
 * compose par le serveur (`notifications.py`) : lui seul connait le plafond
 * accorde et la date. Si les deux textes divergent un jour, c'est celui du
 * serveur qui a ete envoye.
 */
export function apercuDuMessage(issue: Issue, motif?: Motif): string {
  if (issue === "valide") {
    return "Votre dossier est validé : vous pouvez lancer votre premier groupage.";
  }
  if (!motif) {
    return "";
  }
  const detail = MOTIFS[motif];
  const premiere =
    issue === "a-completer"
      ? `Votre dossier n'est pas encore validé : ${detail.public}.`
      : `Votre dossier n'a pas été validé : ${detail.public}.`;
  return `${premiere}\n\nCe qu'il faut faire : ${detail.suite}`;
}
