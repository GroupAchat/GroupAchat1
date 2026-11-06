import { motion } from "framer-motion";
import { Plus, Trash2, TrendingDown, Users } from "lucide-react";

import { Bouton, fusionner } from "@commun/composants/ui";
import { francs } from "@commun/outils/formats";

/**
 * La saisie du barème par l'OAG, en deux temps.
 *
 * **Les tranches** d'abord : « la pièce à 25 000, à partir de 12 pièces
 * 22 000 ». C'est l'acheteur seul qui décide d'y entrer, en prenant plus.
 *
 * **Les chutes** ensuite : « à 30 participants, la pièce passe à 23 000 et
 * la tranche des douze à 20 000 ». Celles-là dépendent du nombre de
 * personnes, et profitent **aussi à ceux qui ont déjà payé** — sans quoi
 * personne n'aurait de raison de partager la campagne.
 *
 * Les deux sont saisis séparément parce qu'ils ne se pensent pas pareil,
 * et assemblés en une grille au moment d'envoyer : une chute donne un prix
 * par tranche, soit une case du tableau que verra l'acheteur.
 */

export interface Tranche {
  quantite_min: string;
  prix_unitaire: string;
}

export interface Chute {
  participants_min: string;
  /** Le prix de chaque tranche à ce seuil ; la clé « 1 » est la pièce seule. */
  prix: Record<string, string>;
}

export interface PalierAEnvoyer {
  quantite_min: number;
  participants_min: number;
  prix_unitaire: number;
}

/** Met le barème à plat, tel que l'API l'attend : une ligne par case. */
export function aplatirLeBareme(
  tranches: Tranche[],
  chutes: Chute[],
): PalierAEnvoyer[] {
  const valides = tranches.filter(
    (tranche) => Number(tranche.quantite_min) > 0 && Number(tranche.prix_unitaire) > 0,
  );

  const lignes: PalierAEnvoyer[] = valides.map((tranche) => ({
    quantite_min: Number(tranche.quantite_min),
    participants_min: 0,
    prix_unitaire: Number(tranche.prix_unitaire),
  }));

  for (const chute of chutes) {
    const seuil = Number(chute.participants_min);
    if (!seuil) continue;
    for (const [quantite, prix] of Object.entries(chute.prix)) {
      if (!Number(prix)) continue;
      lignes.push({
        quantite_min: Number(quantite),
        participants_min: seuil,
        prix_unitaire: Number(prix),
      });
    }
  }
  return lignes;
}

export function EditeurBareme({
  prixAffiche,
  tranches,
  surTranches,
  chutes,
  surChutes,
}: {
  prixAffiche: number;
  tranches: Tranche[];
  surTranches: (tranches: Tranche[]) => void;
  chutes: Chute[];
  surChutes: (chutes: Chute[]) => void;
}) {
  // Les lignes du tableau de chute : la pièce seule, puis chaque tranche
  // déjà saisie. Sans tranche, il ne reste que la pièce seule à faire
  // baisser — et c'est très bien.
  const lignes = [
    { cle: "1", libelle: "La pièce seule", base: prixAffiche },
    ...tranches
      .filter((tranche) => Number(tranche.quantite_min) > 1)
      .map((tranche) => ({
        cle: tranche.quantite_min,
        libelle: `À partir de ${tranche.quantite_min} pièces`,
        base: Number(tranche.prix_unitaire) || 0,
      })),
  ];

  const majChute = (rang: number, champs: Partial<Chute>) =>
    surChutes(chutes.map((item, index) => (index === rang ? { ...item, ...champs } : item)));

  return (
    <div className="space-y-6">
      {/* ── Les tranches ──────────────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 font-bold">
              <TrendingDown className="size-4 text-[color:var(--color-accent)]" />
              Tranches de quantité
            </h3>
            <p className="texte-doux text-sm">
              Le prix baisse pour qui prend plus. « À partir de 12 pièces,
              22 000 » : celui qui en prend 14 paie 22 000 aussi.
            </p>
          </div>
          <Bouton
            type="button"
            ton="contour"
            taille="sm"
            icone={<Plus className="size-4" />}
            onClick={() => surTranches([...tranches, { quantite_min: "", prix_unitaire: "" }])}
          >
            Ajouter
          </Bouton>
        </div>

        {tranches.map((tranche, rang) => (
          <motion.div
            key={rang}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-end gap-2"
          >
            <input
              type="number"
              min={2}
              placeholder="À partir de … pièces"
              value={tranche.quantite_min}
              onChange={(evenement) =>
                surTranches(
                  tranches.map((item, index) =>
                    index === rang
                      ? { ...item, quantite_min: evenement.target.value }
                      : item,
                  ),
                )
              }
              className="surface h-12 flex-1 rounded-2xl px-4 text-sm outline-none focus:border-[color:var(--color-accent)]"
              aria-label={`Quantité de la tranche ${rang + 1}`}
            />
            <input
              type="number"
              min={1}
              placeholder="Prix FCFA"
              value={tranche.prix_unitaire}
              onChange={(evenement) =>
                surTranches(
                  tranches.map((item, index) =>
                    index === rang
                      ? { ...item, prix_unitaire: evenement.target.value }
                      : item,
                  ),
                )
              }
              className={fusionner(
                "surface h-12 flex-1 rounded-2xl px-4 text-sm outline-none focus:border-[color:var(--color-accent)]",
                prixAffiche > 0 &&
                  Number(tranche.prix_unitaire) >= prixAffiche &&
                  "border-red-500",
              )}
              aria-label={`Prix de la tranche ${rang + 1}`}
            />
            <button
              type="button"
              onClick={() => surTranches(tranches.filter((_, index) => index !== rang))}
              className="texte-doux grid size-12 shrink-0 place-items-center rounded-2xl transition-colors hover:text-red-600"
              aria-label="Supprimer cette tranche"
            >
              <Trash2 className="size-4" />
            </button>
          </motion.div>
        ))}

        {tranches.length > 0 && prixAffiche > 0 && (
          <p className="texte-doux text-xs">
            Une tranche doit être <strong>moins chère</strong> que les{" "}
            {francs(prixAffiche)} affichés, sinon prendre plus coûterait plus.
          </p>
        )}
      </div>

      {/* ── Les chutes ────────────────────────────────────────────────── */}
      <div className="space-y-3 border-t pt-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 font-bold">
              <Users className="size-4 text-[color:var(--color-accent)]" />
              Chute de prix (facultatif)
            </h3>
            <p className="texte-doux text-sm">
              Passé un nombre de participants, tous les prix descendent —{" "}
              <strong>y compris pour ceux qui ont déjà payé</strong>, à qui la
              différence est rendue. C'est ce qui donne à vos acheteurs une
              raison de partager la campagne.
            </p>
          </div>
          <Bouton
            type="button"
            ton="contour"
            taille="sm"
            icone={<Plus className="size-4" />}
            onClick={() => surChutes([...chutes, { participants_min: "", prix: {} }])}
          >
            Ajouter
          </Bouton>
        </div>

        {chutes.map((chute, rang) => (
          <motion.div
            key={rang}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="surface-douce space-y-3 rounded-2xl p-4"
          >
            <div className="flex items-center gap-2">
              <span className="texte-doux shrink-0 text-sm">À partir de</span>
              <input
                type="number"
                min={2}
                placeholder="30"
                value={chute.participants_min}
                onChange={(evenement) =>
                  majChute(rang, { participants_min: evenement.target.value })
                }
                className="surface h-11 w-24 rounded-xl px-3 text-sm outline-none focus:border-[color:var(--color-accent)]"
                aria-label={`Nombre de participants de la chute ${rang + 1}`}
              />
              <span className="texte-doux shrink-0 text-sm">participants :</span>
              <button
                type="button"
                onClick={() => surChutes(chutes.filter((_, index) => index !== rang))}
                className="texte-doux ml-auto grid size-9 shrink-0 place-items-center rounded-xl transition-colors hover:text-red-600"
                aria-label="Supprimer cette chute"
              >
                <Trash2 className="size-4" />
              </button>
            </div>

            <div className="space-y-2">
              {lignes.map((ligne) => (
                <div key={ligne.cle} className="flex items-center gap-2">
                  <span className="min-w-0 flex-1 truncate text-sm">
                    {ligne.libelle}
                    {ligne.base > 0 && (
                      <span className="texte-doux"> · {francs(ligne.base)}</span>
                    )}
                  </span>
                  <input
                    type="number"
                    min={1}
                    placeholder="Nouveau prix"
                    value={chute.prix[ligne.cle] ?? ""}
                    onChange={(evenement) =>
                      majChute(rang, {
                        prix: { ...chute.prix, [ligne.cle]: evenement.target.value },
                      })
                    }
                    className={fusionner(
                      "surface h-11 w-36 rounded-xl px-3 text-sm outline-none focus:border-[color:var(--color-accent)]",
                      ligne.base > 0 &&
                        Number(chute.prix[ligne.cle]) >= ligne.base &&
                        "border-red-500",
                    )}
                    aria-label={`Prix de « ${ligne.libelle} » à ce seuil`}
                  />
                </div>
              ))}
            </div>

            <p className="texte-doux text-xs">
              Laissez vide une tranche que vous ne voulez pas faire baisser.
            </p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
