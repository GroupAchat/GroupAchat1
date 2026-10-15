/**
 * La barre de progression d'un groupage vers l'objectif de son groupeur.
 *
 * SPEC_ECRANS_FIGMA.md §2.5.
 *
 * ## ⚠️ Ce que cette barre n'est pas
 *
 * Le §2.5 interdisait toute jauge, et pour une raison qui etait juste a
 * l'epoque : **un groupage n'avait ni plafond ni minimum**, donc aucun
 * denominateur. Le groupeur declare desormais combien de personnes il veut
 * reunir, et c'est ce chiffre que la barre remplit.
 *
 * Trois choses qu'elle ne dit pas, et qui ne doivent jamais s'ecrire autour
 * d'elle :
 *
 * - **ce ne sont pas des places.** Depasser l'objectif est permis et normal.
 *   Jamais « places disponibles », jamais « complet », jamais « il reste 3
 *   places » ;
 * - **ce n'est pas un minimum.** Un groupage a 14 sur 20 peut parfaitement
 *   aboutir : a la cloture, c'est le groupeur qui decide (§7 du cahier des
 *   charges). Jamais « il manque 6 personnes pour que le groupage parte » ;
 * - **elle ne declenche rien.** Atteindre l'objectif ne cloture pas le
 *   groupage ; seule la date le fait.
 *
 * ## Le depassement
 *
 * La barre s'arrete a plein et **le nombre ecrit continue de monter** : « 24
 * acheteurs confirmes » sur un objectif de 20. Une barre qui deborderait de sa
 * gouttiere serait un defaut d'affichage, et la plafonner en silence ferait
 * disparaitre une bonne nouvelle.
 *
 * ## Le chiffre est ecrit, toujours
 *
 * La barre seule ne se lit pas : 60 % de quoi ? Le texte porte le sens, la
 * barre ne fait que le rendre immediat. C'est aussi ce qui la rend lisible aux
 * lecteurs d'ecran sans que l'`aria-label` ait a repeter autre chose.
 *
 * ## Le vocabulaire
 *
 * « **acheteurs confirmes** », jamais « participants » ni « commandes » (§3) :
 * « confirmes » dit que ces gens ont paye, c'est rassurant, et c'est vrai. Le
 * champ cote serveur s'appelle `objectif_participants`, mais c'est un nom
 * interne — il ne sort pas a l'ecran.
 */
export default function JaugeParticipants({
  acheteursConfirmes,
  objectif,
  progression,
  taille = "normale",
  fond = "clair",
}: {
  acheteursConfirmes: number;
  objectif: number;
  /**
   * Le pourcentage de remplissage, **tel que le serveur l'a calcule**.
   *
   * ⚠️ **Ne pas le recalculer ici.** Il l'etait, et les deux cotes ne
   * tombaient pas d'accord : le serveur arrondit vers le bas — une barre ne
   * doit jamais surestimer — tandis que `Math.round` arrondissait au plus
   * proche. Sur un groupage a 1 acheteur sur 40, l'API disait 2 % et la barre
   * en affichait 3. Un seul calcul, cote serveur, et quatre ecrans qui s'y
   * fient.
   */
  progression: number;
  /** `compacte` sur une ligne de liste, `normale` sur une carte ou un detail. */
  taille?: "compacte" | "normale";
  /**
   * `sombre` pour une carte posee **sur un media sombre** — le fil (ecran 1) et
   * la carte urgente.
   *
   * ⚠️ Le remplissage reste `marque`, et c'est permis : sur un aplat sombre
   * l'orange vif ne sert ici que de **bloc plein**, jamais de texte (§1.2).
   * Ce qui change est le texte, qui passe en blanc, et la gouttiere, qui
   * devient un blanc transparent — `surface-douce` disparaitrait sur une photo
   * claire comme sur une photo foncee.
   */
  fond?: "clair" | "sombre";
}) {
  /* Borne par securite : une valeur hors de [0, 100] viendrait d'une reponse
     inattendue, et elle ferait deborder la barre de sa gouttiere. */
  const part = Math.max(0, Math.min(100, progression));
  const atteint = objectif > 0 && acheteursConfirmes >= objectif;
  const sombre = fond === "sombre";

  const confirmes = `${acheteursConfirmes} acheteur${
    acheteursConfirmes > 1 ? "s" : ""
  } confirmé${acheteursConfirmes > 1 ? "s" : ""}`;

  /* Une fois l'objectif atteint, le denominateur ne sert plus a rien : ce qui
     compte est que le but est passe. Avant, c'est lui qui donne l'echelle. */
  const texte = atteint ? confirmes : `${confirmes} sur ${objectif}`;

  return (
    <div>
      <p
        className={`flex items-baseline justify-between gap-2 ${
          taille === "compacte" ? "text-xs" : "text-sm"
        } ${sombre ? "text-white/85" : "text-texte-secondaire"}`}
      >
        <span className="min-w-0 truncate">
          <strong
            className={`font-semibold ${sombre ? "text-white" : "text-texte"}`}
          >
            {acheteursConfirmes}
          </strong>
          {/* ⚠️ **Le denominateur ne s'affiche que s'il existe et que l'objectif
              n'est pas atteint.**

              Le gabarit ecrivait ` sur {objectif} acheteurs` sans condition. Deux
              consequences : une fois l'objectif passe, il continuait d'afficher
              « sur 30 » alors que `texte` ci-dessus avait justement prevu de
              l'enlever ; et surtout, quand `objectif` arrivait vide — ce qui
              arrive des qu'un ecran oublie de passer la propriete — la ligne se
              lisait « **23 sur  acheteurs** », une phrase cassee en pleine carte.

              Un groupage n'a ni plafond ni minimum (§2.5) : un objectif absent
              est un cas normal, pas une anomalie. On affiche alors le compte
              seul, qui se suffit. */}
          {objectif > 0 && !atteint ? (
            <> sur {objectif} acheteurs</>
          ) : (
            <> acheteur{acheteursConfirmes > 1 ? "s" : ""} confirmé{acheteursConfirmes > 1 ? "s" : ""}</>
          )}
        </span>
        {atteint ? (
          /* ⚠️ **Le couple déjà calculé du §1.2**, et non `marque` : l'orange
             vif ne porte que du texte sombre (blanc dessus donne 2,87:1, ce qui
             est interdit), et il n'existe pas d'aplat pâle pour lui. Ce couple
             `primaire-texte-sur-fond` sur `primaire-fond` est celui dont le
             contraste est vérifié pour un texte sur teinte. */
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${
              sombre
                ? "bg-white/15 text-white"
                : "bg-primaire-fond text-primaire-texte-sur-fond"
            }`}
          >
            Objectif atteint
          </span>
        ) : null}
      </p>

      <div
        className={`mt-1.5 overflow-hidden rounded-full ${
          sombre ? "bg-white/25" : "bg-surface-douce"
        } ${taille === "compacte" ? "h-1.5" : "h-2"}`}
        role="progressbar"
        aria-valuenow={acheteursConfirmes}
        aria-valuemin={0}
        aria-valuemax={objectif}
        aria-label={`${texte} acheteurs`}
      >
        <div
          className="h-full rounded-full bg-marque transition-[width] duration-500"
          style={{ width: `${part}%` }}
        />
      </div>
    </div>
  );
}
