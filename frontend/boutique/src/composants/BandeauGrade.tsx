import { motion } from "framer-motion";
import { Award, TrendingDown } from "lucide-react";

import { Carte } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { gradeLisible, tauxCommission } from "@commun/outils/formats";

/**
 * Le grade de l'OAG, la commission qu'il paie, et ce qui reste à parcourir.
 *
 * **Deux compteurs, affichés séparément.** Les points cumulés décident du
 * grade et ne descendent jamais ; le solde est la monnaie et descend quand on
 * dépense. Les confondre tromperait : « 940 points » et « 640 points à
 * dépenser » ne disent pas la même chose, et un OAG qui croirait perdre
 * son grade en dépensant ne dépenserait jamais rien.
 *
 * Le bandeau vit dans la boutique et non dans le socle : seul l'espace
 * OAG l'affiche, et la console d'administration a sa propre vue des
 * grades.
 */

const TEINTES: Record<string, string> = {
  nouveau: "#ea580c",
  bronze: "#a16207",
  argent: "#64748b",
  or: "#b8860b",
};

export function BandeauGrade() {
  const { utilisateur } = useSession();
  const points = utilisateur?.points;
  if (!points) return null;

  const teinte = TEINTES[points.grade] ?? TEINTES.bronze;
  const palier = points.prochain_palier;

  const avancement = palier
    ? Math.min(100, Math.round((points.cumules / (points.cumules + palier.points_restants)) * 100))
    : 100;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Carte className="space-y-4">
        <div className="flex flex-wrap items-start gap-4">
          <span
            className="grid size-12 shrink-0 place-items-center rounded-2xl text-white"
            style={{ backgroundColor: teinte }}
          >
            <Award className="size-6" />
          </span>

          <div className="min-w-0 flex-1">
            <p className="texte-doux text-sm">Votre grade</p>
            <p className="text-xl font-extrabold">{gradeLisible(points.grade)}</p>
            <p className="texte-doux flex items-center gap-1.5 text-sm">
              <TrendingDown className="size-3.5" />
              Commission de {tauxCommission(points.commission_centiemes)} sur
              chaque groupage réussi
            </p>
          </div>

          <div className="shrink-0 text-right">
            <p className="texte-doux text-xs">Points cumulés</p>
            <p className="tabulaire text-lg font-bold">{points.cumules}</p>
            <p className="texte-doux tabulaire text-xs">
              {points.solde} à dépenser
            </p>
          </div>
        </div>

        {palier ? (
          <div className="space-y-1.5">
            <div className="h-2 overflow-hidden rounded-full bg-[color:var(--color-marine-100)] dark:bg-[color:var(--color-marine-900)]">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: teinte }}
                initial={{ width: 0 }}
                animate={{ width: `${avancement}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              />
            </div>
            <p className="texte-doux text-sm">
              Encore <strong>{palier.points_restants} points</strong> pour
              passer {gradeLisible(palier.grade)} — et payer{" "}
              {tauxCommission(palier.grade === "argent" ? 250 : 130)}.
            </p>
          </div>
        ) : (
          <p className="texte-doux text-sm">
            Vous êtes au grade le plus élevé. Vos groupages passent en
            publication libre, et la commission ne descend pas plus bas.
          </p>
        )}

        <p className="texte-doux text-xs">
          Dépenser vos points ne fait pas baisser votre grade : les points
          cumulés ne descendent jamais.
        </p>
      </Carte>
    </motion.div>
  );
}
