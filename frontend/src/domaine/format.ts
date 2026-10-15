/**
 * Mise en forme des montants, des dates et du temps restant.
 *
 * Le vocabulaire visible est fixe par SPEC_ECRANS_FIGMA.md §3 : « 4 000 F CFA »
 * et « Il reste 2 jours ». Les variantes de couleur du badge viennent du §2.4.
 */

/** Espace fine insecable, pour que « 4 000 » ne se coupe jamais en fin de ligne. */
const ESPACE_FINE = " ";
/** Espace insecable, entre le nombre et son unite. */
const ESPACE_INSECABLE = " ";

/**
 * « 4 000 F CFA ». Le prix complet partout ou l'utilisateur lit un montant
 * (§3) — le `F` seul reste reserve aux tableaux denses et a l'administration.
 *
 * `Intl` n'est pas utilise ici : son separateur de milliers varie selon
 * l'implementation de la WebView Android, et on veut un rendu identique
 * partout.
 */
export function formaterFrancs(montant: number): string {
  const entier = Math.round(montant).toString();
  const groupes: string[] = [];
  for (let fin = entier.length; fin > 0; fin -= 3) {
    groupes.unshift(entier.slice(Math.max(0, fin - 3), fin));
  }
  return `${groupes.join(ESPACE_FINE)}${ESPACE_INSECABLE}F${ESPACE_INSECABLE}CFA`;
}

/** « 12 octobre » — le mois en entier, l'annee est toujours l'annee en cours. */
export function formaterDateCourte(dateISO: string): string {
  const date = new Date(`${dateISO}T12:00:00`);
  if (Number.isNaN(date.getTime())) {
    return dateISO;
  }
  const mois = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
  ];
  return `${date.getDate()}${ESPACE_INSECABLE}${mois[date.getMonth()]}`;
}

/** Les quatre etats du `CompteurTemps` (§2.4). */
export type UrgenceTemps = "large" | "proche" | "derniere-heure" | "terminee";

export interface TempsRestant {
  urgence: UrgenceTemps;
  /**
   * « Il reste 3 jours » — une phrase, pas un cri.
   *
   * ⚠️ **Plus de capitales.** Le libelle etait « RESTE 2 JOURS », et les
   * capitales se justifiaient quand le compteur etait pose nu sur une photo.
   * Il est desormais dans un **badge** qui porte son propre fond, donc la
   * lisibilite vient du contraste du badge et non de la casse. Les capitales
   * ne faisaient plus que durcir le ton sur un produit qui vend la confiance.
   */
  libelle: string;
  /** Version lue a voix haute par un lecteur d'ecran. */
  libelleAccessible: string;
}

/**
 * Traduit un nombre d'heures en libelle et en niveau d'urgence.
 *
 * Les seuils : moins de 24 h est une urgence reelle (`danger`), jusqu'a
 * 72 h la cloture est proche (orange), au-dela le compteur reste sobre.
 * C'est le seul element de pression de l'application (§2.4) — il n'y a ni
 * minimum ni places limitees, donc il ne faut pas le banaliser.
 */
export function decrireTempsRestant(heuresRestantes: number): TempsRestant {
  /*
   * ⚠️ **L'acheteur ne voit jamais cet etat.** Le catalogue ne sert plus que
   * les groupages ouverts dont la date n'est pas passee : un groupage cloture
   * n'est plus sur la plateforme. Le cas reste traite parce que **le groupeur**
   * voit les siens, clotures compris, sur ses propres ecrans.
   */
  if (heuresRestantes <= 0) {
    return {
      urgence: "terminee",
      libelle: "Groupage clôturé",
      libelleAccessible: "Groupage clôturé",
    };
  }

  /*
   * **Sous 48 h, on compte en heures.** « Il reste 0 jour » ne veut rien dire,
   * et « il reste 1 jour » pour cinq heures serait faux dans le sens qui
   * coute : l'acheteur remettrait sa commande au lendemain.
   *
   * ⚠️ **Le seuil est passe de 24 h a 48 h**, et ce n'est pas un detail de
   * formulation. La rangee « Se termine bientot » est definie par « moins de
   * 48 h » : avec l'ancien seuil, un groupage a 29 h, un a 35 h et un a 47 h
   * affichaient tous les trois **« Il reste 1 jour »**. Trois cartes
   * identiques dans la rangee qui existe pour dire l'urgence — elle ne disait
   * donc plus rien, et « 1 jour » pour 47 h est en plus presque le double de
   * la verite.
   *
   * Au-dela de 48 h, le jour reprend : « il reste 73 heures » ne se lit pas,
   * et a cette distance personne ne compte en heures.
   */
  if (heuresRestantes < 48) {
    const heures = Math.max(1, Math.round(heuresRestantes));
    return {
      /* ⚠️ **L'echelle des couleurs ne bouge pas**, seule la formulation
         change. Faire passer tout ce qui est sous 48 h en « derniere heure »
         aplatirait le signal : si tout est rouge, plus rien ne l'est. */
      urgence: heuresRestantes < 24 ? "derniere-heure" : "proche",
      libelle: `Il reste ${heures}${ESPACE_INSECABLE}h`,
      libelleAccessible: `Il reste ${heures} heure${heures > 1 ? "s" : ""}`,
    };
  }

  const jours = Math.floor(heuresRestantes / 24);
  return {
    urgence: heuresRestantes <= 72 ? "proche" : "large",
    libelle: `Il reste ${jours}${ESPACE_INSECABLE}jour${jours > 1 ? "s" : ""}`,
    libelleAccessible: `Il reste ${jours} jour${jours > 1 ? "s" : ""}`,
  };
}
