import { decrireTempsRestant, type UrgenceTemps } from "../../domaine/format";
import { IconeHorloge } from "../../ui/Icones";

/**
 * `CompteurTemps` — SPEC_ECRANS_FIGMA.md §2.4.
 *
 * **Un badge** : « Il reste 3 jours », fond teinte, liseré, icone horloge.
 *
 * ## ⚠️ Pourquoi un badge et plus une puce nue
 *
 * L'etat `large` etait `bg-white` **sans liseré**, donc sur une carte blanche
 * il n'existait pas : un texte gris parmi d'autres textes gris. Le temps
 * restant est l'element de pression principal de l'application — c'est
 * l'information qui fait commander aujourd'hui plutot que la semaine
 * prochaine — et elle etait la moins visible de la carte.
 *
 * Chaque etat porte donc **un fond teinte et un liseré de la meme famille**,
 * ce qui le detache du blanc sans ombre ni cadre gris (le §1.0 interdit les
 * deux).
 *
 * ## Les contrastes, calcules
 *
 * | Etat | Texte sur fond | Rapport |
 * |---|---|---|
 * | `large` | `texte` `#1D1916` sur `surface-douce` `#FAF8F7` | 16,49:1 |
 * | `proche` | `primaire-texte-sur-fond` `#B34A00` sur `primaire-fond` `#FFF1E6` | 4,87:1 |
 * | `derniere-heure` | `danger` `#C0392B` sur `danger-fond` `#FBEAE8` | 4,67:1 |
 * | `terminee` | `texte-secondaire` `#5C544D` sur `surface-douce` | 7,01:1 |
 * | sur le fil | `texte` `#1D1916` sur `marque` `#FF6A00` | 6,08:1 |
 *
 * Tous au-dessus de 4,5:1, le seuil du texte normal. ⚠️ Les deux plus serres
 * sont `proche` et `derniere-heure`, a moins de 0,4 de marge : **changer l'un
 * de ces quatre jetons demande de refaire ce calcul**, pas de l'estimer.
 */

const STYLES: Record<UrgenceTemps, string> = {
  large: "border-bordure bg-surface-douce text-texte",
  proche: "border-primaire/25 bg-primaire-fond text-primaire-texte-sur-fond",
  "derniere-heure": "border-danger/30 bg-danger-fond text-danger",
  terminee: "border-bordure bg-surface-douce text-texte-secondaire",
};

export default function CompteurTemps({
  heuresRestantes,
  surMedia = false,
}: {
  heuresRestantes: number;
  /** Sur le fil, pose sur un media sombre (§2.4). */
  surMedia?: boolean;
}) {
  const { urgence, libelle, libelleAccessible } =
    decrireTempsRestant(heuresRestantes);

  /* §2.4 — Sur le fil, le badge devient un aplat `marque` a texte sombre.
     C'est son usage le plus visible de toute l'application, et celui ou
     l'orange de la marque travaille le mieux. Le texte y est **sombre, jamais
     blanc** : blanc sur `marque` ne tient qu'a 2,87:1, et c'est interdit
     (§1.2). Le liseré y devient l'orange lui-meme, donc invisible — le badge
     se detache deja du media par son aplat. */
  const style = surMedia
    ? "border-marque bg-marque text-texte"
    : STYLES[urgence];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${style}`}
    >
      <IconeHorloge taille={14} className="shrink-0" />
      {/* Le libelle visible est abrege sous un jour (« 5 h ») : on en donne la
          version lue en entier aux lecteurs d'ecran. */}
      <span aria-hidden="true">{libelle}</span>
      <span className="sr-only">{libelleAccessible}</span>
    </span>
  );
}
