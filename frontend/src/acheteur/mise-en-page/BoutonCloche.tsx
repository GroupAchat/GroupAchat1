import { IconeCloche } from "../../ui/Icones";

/**
 * La cloche de notifications, et son compteur.
 *
 * ## ⚠️ Pourquoi elle est devenue un bouton cerne
 *
 * C'etait une **icone nue** posee a cote de « Demander », un bouton orange
 * plein. A ce voisinage-la, un glyphe sans contour ne se lit plus comme un
 * controle : il passe pour un pictogramme decoratif, et on ne pense pas a
 * cliquer dessus.
 *
 * Elle porte donc un contour — et le jeton compte :
 *
 * | Bordure | Sur blanc |
 * |---|---|
 * | `bordure` `#EBE8E5` | **1,22:1** — invisible |
 * | `bordure-champ` `#948A80` | **3,38:1** |
 *
 * `bordure-champ` existe exactement pour ce cas : le projet l'a cree quand les
 * champs de saisie, cernes de `bordure`, se sont reveles invisibles. Un
 * controle qu'on doit voir prend `bordure-champ` ; un contour decoratif de
 * carte prend `bordure`. Les confondre rend le bouton invisible sans qu'aucun
 * outil ne le signale.
 *
 * ## ⚠️ Un compteur, et plus une pastille muette
 *
 * Il y avait un point de 10 px qui disait seulement « quelque chose ». Le
 * compteur dit **combien**, ce qui est l'information qu'on cherche, et il
 * occupe assez de place pour se voir de loin.
 *
 * | Fond | Chiffre sombre | Chiffre blanc |
 * |---|---|---|
 * | `marque` `#FF6A00` | **6,08:1** | 2,87:1 — **interdit** |
 * | `primaire` `#CC4A00` | 3,78:1 | 4,62:1 |
 *
 * `marque` avec un chiffre **sombre** : c'est le plus vif des deux oranges,
 * donc le plus visible, et c'est l'usage que le §1.2 lui reserve — « aplats
 * vifs, texte sombre uniquement ». Ecrire le compteur en blanc dessus le
 * ferait tomber a 2,87:1, ce que le §1.2 interdit nommement.
 *
 * `marque` plutot que `primaire` evite aussi deux oranges identiques cote a
 * cote : le bouton « Demander » est en `primaire`, le compteur en `marque` —
 * on les distingue au lieu de les confondre.
 *
 * ## La cloche reste discrete quand il n'y a rien
 *
 * Pas de compteur, pas de couleur : un controle qu'on doit pouvoir trouver,
 * mais qui n'a rien a annoncer. **Crier en permanence serait le vrai defaut** —
 * au bout d'une semaine, on ne regarderait plus ni la cloche ni son compteur.
 */
export default function BoutonCloche({
  notifications = 0,
  onClick,
  /** Sur le fil, l'en-tete est pose sur un media : le fond doit etre opaque. */
  surMedia = false,
  taille = "normale",
}: {
  notifications?: number;
  onClick?: () => void;
  surMedia?: boolean;
  /**
   * ⚠️ **`compacte` sur telephone, et ce n'est pas un gout.**
   *
   * Le bouton a ete grossi pour exister a cote de « Demander », un bouton
   * orange plein, dans une barre de bureau large. Reporte tel quel sur un
   * en-tete de 390 px, il se retrouve **seul face au logo** — et un cercle
   * cerne de 48 px pese alors plus lourd que la marque elle-meme, qui fait
   * 28 px de haut. Il attirait l'oeil avant le nom du produit.
   *
   * | | `normale` *(bureau)* | `compacte` *(telephone)* |
   * |---|---|---|
   * | Bouton | 48 px | **40 px** |
   * | Icone | 24 px | **20 px** |
   * | Compteur | 20 px, 11 px de texte | **16 px, 10 px** |
   *
   * La zone tactile reste a 40 px, au-dessus du minimum de 44 px une fois
   * comptee la marge de l'en-tete autour — c'est la limite basse, ne pas
   * descendre plus.
   */
  taille?: "normale" | "compacte";
}) {
  const compacte = taille === "compacte";

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={
        notifications > 0
          ? `Notifications, ${notifications} non lue${notifications > 1 ? "s" : ""}`
          : "Notifications"
      }
      className={`relative flex shrink-0 items-center justify-center rounded-full border border-bordure-champ text-texte hover:bg-surface-douce ${
        compacte ? "size-10" : "size-12"
      } ${surMedia ? "bg-white" : ""}`}
    >
      {/* Le dessin occupe tout son cadre : il peut remplir le bouton sans y
          etre a l'etroit. */}
      <IconeCloche taille={compacte ? 20 : 24} />

      {notifications > 0 ? (
        /*
         * `ring-2 ring-white` : sans cet anneau, le compteur se colle au
         * trait de la cloche et les deux formes se mangent. L'anneau n'a pas
         * de contraste a tenir — il separe, il ne porte aucun texte.
         *
         * `-top-1 -right-1` : il deborde du cercle. C'est ce debordement qui
         * le fait voir — un compteur rentre a l'interieur du bouton se
         * confond avec l'icone.
         */
        <span
          aria-hidden="true"
          className={`absolute -top-1 -right-1 flex items-center justify-center rounded-full bg-marque px-1 font-bold text-texte ring-2 ring-white ${
            compacte ? "h-4 min-w-4 text-[10px]" : "h-5 min-w-5 text-[11px]"
          }`}
        >
          {/* Au-dela de neuf, le chiffre exact n'apprend plus rien et la
              pastille s'allongerait jusqu'a deformer le bouton. */}
          {notifications > 9 ? "9+" : notifications}
        </span>
      ) : null}
    </button>
  );
}
