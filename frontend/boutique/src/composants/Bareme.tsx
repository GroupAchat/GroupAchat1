import { TrendingDown, Users } from "lucide-react";

import type { Campagne, PalierPrix } from "@commun/api/types";
import { fusionner } from "@commun/composants/ui";
import { francs } from "@commun/outils/formats";

/**
 * Le barème de prix d'une campagne, à deux axes.
 *
 * - **La tranche**, en lignes : ce que prend un seul acheteur. « La pièce à
 *   25 000, à partir de 12 pièces 22 000 » — celui qui en prend 14 paie
 *   22 000, celui qui en prend une paie 25 000.
 * - **La chute**, en colonnes : passé un nombre de participants, chaque
 *   tranche descend encore. Elle profite **aussi à ceux qui ont déjà
 *   payé** ; c'est pour cela qu'on a intérêt à faire venir ses amis.
 *
 * Le calcul est refait ici plutôt que demandé au serveur : l'acheteur change
 * sa quantité avec un bouton « + », et attendre une réponse réseau à chaque
 * clic rendrait le prix poussif. La règle est la même des deux côtés —
 * **le meilleur prix auquel on a droit**.
 */

export function prixPour(
  campagne: Pick<Campagne, "prix_unitaire" | "paliers">,
  quantite: number,
  participants: number,
): number {
  const ouverts = campagne.paliers
    .filter(
      (palier) =>
        palier.quantite_min <= quantite && palier.participants_min <= participants,
    )
    .map((palier) => palier.prix_unitaire);
  return ouverts.length ? Math.min(...ouverts) : campagne.prix_unitaire;
}

/** Les seuils de quantité du barème, « 1 » compris. */
function tranches(paliers: PalierPrix[]): number[] {
  return [...new Set([1, ...paliers.map((palier) => palier.quantite_min)])].sort(
    (a, b) => a - b,
  );
}

/** Les seuils de participants, « au départ » compris. */
function chutes(paliers: PalierPrix[]): number[] {
  return [...new Set([0, ...paliers.map((palier) => palier.participants_min)])].sort(
    (a, b) => a - b,
  );
}

function libelleTranche(seuil: number, suivant: number | undefined): string {
  if (suivant === undefined) return `${seuil} et plus`;
  if (suivant - seuil === 1) return `${seuil}`;
  return `${seuil} à ${suivant - 1}`;
}

export function Bareme({
  campagne,
  quantite,
}: {
  campagne: Campagne;
  /** La quantité que l'acheteur a sous les yeux : sa ligne est surlignée. */
  quantite: number;
}) {
  const lignes = tranches(campagne.paliers);
  const colonnes = chutes(campagne.paliers);
  const participants = campagne.nombre_participants;

  if (campagne.paliers.length === 0) return null;

  // La ligne où se trouve l'acheteur, et la colonne où en est la campagne.
  const ligneActive = [...lignes].reverse().find((seuil) => seuil <= quantite) ?? 1;
  const colonneActive =
    [...colonnes].reverse().find((seuil) => seuil <= participants) ?? 0;

  return (
    <div className="space-y-2">
      <div className="overflow-x-auto rounded-2xl border">
        <table className="w-full min-w-[22rem] text-sm">
          <thead>
            <tr className="surface text-left">
              <th className="px-3 py-2 font-semibold">Vous prenez</th>
              {colonnes.map((seuil) => (
                <th
                  key={seuil}
                  className={fusionner(
                    "px-3 py-2 text-right font-semibold",
                    seuil === colonneActive &&
                      "text-[color:var(--color-accent-fort)]",
                  )}
                >
                  {seuil === 0 ? (
                    "Prix du jour"
                  ) : (
                    <span className="inline-flex items-center gap-1">
                      <Users className="size-3.5" />
                      {seuil} participants
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {lignes.map((seuil, rang) => (
              <tr
                key={seuil}
                className={fusionner(
                  "border-t",
                  seuil === ligneActive && "bg-accent-doux",
                )}
              >
                <td className="px-3 py-2.5">
                  <span
                    className={fusionner(
                      seuil === ligneActive &&
                        "font-semibold text-[color:var(--color-accent-fort)]",
                    )}
                  >
                    {libelleTranche(seuil, lignes[rang + 1])} pièce
                    {(lignes[rang + 1] ?? seuil + 1) - seuil > 1 || !lignes[rang + 1]
                      ? "s"
                      : ""}
                  </span>
                </td>
                {colonnes.map((chute) => {
                  const prix = prixPour(campagne, seuil, chute);
                  const courant = seuil === ligneActive && chute === colonneActive;
                  const aVenir = chute > participants;
                  return (
                    <td
                      key={chute}
                      className={fusionner(
                        "tabulaire px-3 py-2.5 text-right",
                        courant &&
                          "font-bold text-[color:var(--color-accent-fort)]",
                        // Une chute non atteinte reste lisible mais en
                        // retrait : c'est une promesse, pas le prix du jour.
                        aVenir && "texte-doux",
                      )}
                    >
                      {francs(prix)}
                      {courant && (
                        <span className="ml-1.5 text-[0.65rem] font-bold uppercase">
                          votre prix
                        </span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Incitations campagne={campagne} quantite={quantite} />
    </div>
  );
}

/**
 * Les deux leviers, dits séparément parce qu'ils ne se jouent pas pareil.
 *
 * Le premier ne dépend que de l'acheteur : prendre quelques pièces de plus.
 * Le second dépend des autres, et c'est celui qui fait partager la campagne.
 */
function Incitations({ campagne, quantite }: { campagne: Campagne; quantite: number }) {
  const participants = campagne.nombre_participants;
  const prixActuel = prixPour(campagne, quantite, participants);

  const tranche = campagne.paliers
    .filter(
      (palier) =>
        palier.quantite_min > quantite &&
        palier.participants_min <= participants &&
        palier.prix_unitaire < prixActuel,
    )
    .sort((a, b) => a.quantite_min - b.quantite_min)[0];

  const chute = campagne.paliers
    .filter(
      (palier) =>
        palier.participants_min > participants &&
        palier.quantite_min <= quantite &&
        palier.prix_unitaire < prixActuel,
    )
    .sort((a, b) => a.participants_min - b.participants_min)[0];

  if (!tranche && !chute) return null;

  return (
    <div className="space-y-1.5">
      {tranche && (
        <p className="flex items-start gap-2 text-sm">
          <TrendingDown className="mt-0.5 size-4 shrink-0 text-[color:var(--color-accent)]" />
          <span>
            Prenez{" "}
            <strong className="text-[color:var(--color-accent)]">
              {tranche.quantite_min - quantite} pièce
              {tranche.quantite_min - quantite > 1 ? "s" : ""} de plus
            </strong>{" "}
            et la vôtre tombe à {francs(tranche.prix_unitaire)}.
          </span>
        </p>
      )}
      {chute && (
        <p className="flex items-start gap-2 text-sm">
          <Users className="mt-0.5 size-4 shrink-0 text-[color:var(--color-accent)]" />
          <span>
            Encore{" "}
            <strong className="text-[color:var(--color-accent)]">
              {chute.participants_min - participants} participant
              {chute.participants_min - participants > 1 ? "s" : ""}
            </strong>{" "}
            et le prix tombe à {francs(chute.prix_unitaire)}{" "}
            <span className="texte-doux">
              pour tout le monde — y compris ceux qui ont déjà payé. Partagez
              la campagne, la différence vous sera rendue.
            </span>
          </span>
        </p>
      )}
    </div>
  );
}
