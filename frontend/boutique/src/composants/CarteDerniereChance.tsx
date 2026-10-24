import { motion } from "framer-motion";
import { ArrowRight, Flame, Users } from "lucide-react";
import { Link } from "react-router-dom";

import type { CampagneResume } from "@commun/api/types";
import { Jauge } from "@/composants/Jauge";
import { Visuel } from "@/composants/Visuel";
import { fusionner } from "@commun/composants/ui";
import { francs } from "@commun/outils/formats";

/**
 * La carte des campagnes qui se terminent bientôt.
 *
 * **Volontairement différente de la vignette du catalogue** : ici, ce n'est
 * pas le produit qu'on met en avant mais le **temps qui reste**. La carte
 * est donc horizontale, le compte à rebours occupe le coin le plus visible,
 * et le visuel est réduit à une vignette — on sait déjà ce qu'on regarde,
 * la question est de savoir s'il faut se décider maintenant.
 *
 * Le rouge n'apparaît qu'au dernier jour. Utilisé partout, il ne voudrait
 * plus rien dire.
 */
export function CarteDerniereChance({
  campagne,
  index = 0,
}: {
  campagne: CampagneResume;
  index?: number;
}) {
  const dernierJour = campagne.jours_restants <= 0;
  const presse = campagne.jours_restants <= 1;
  const manque = Math.max(0, campagne.quantite_minimale - campagne.quantite_reservee);

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45, delay: Math.min(index, 6) * 0.06 }}
      className={fusionner(
        "group relative overflow-hidden rounded-[var(--radius-carte)] border transition-all duration-300",
        "hover:-translate-y-1 hover:shadow-2xl hover:shadow-black/10",
        dernierJour
          ? "border-red-300 dark:border-red-900/70"
          : "border-[color:var(--bordure)]",
      )}
      style={{ background: "var(--fond-carte)" }}
    >
      {/* Un liseré coloré sur la tranche : il situe l'urgence avant même
          qu'on ait lu le compte à rebours. */}
      <span
        className={fusionner(
          "absolute inset-y-0 left-0 w-1",
          dernierJour ? "bg-red-500" : "degrade-accent",
        )}
        aria-hidden
      />

      <Link to={`/campagnes/${campagne.id}`} className="flex gap-4 p-4 pl-5">
        <div className="size-24 shrink-0 overflow-hidden rounded-2xl lg:size-28">
          <div className="size-full transition-transform duration-500 group-hover:scale-110">
            <Visuel source={campagne.produit.image} nom={campagne.produit.nom} />
          </div>
        </div>

        <div className="flex min-w-0 flex-1 flex-col justify-between gap-2">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="texte-doux text-xs font-medium uppercase tracking-wide">
                {campagne.produit.categorie_nom}
              </p>
              <h3 className="line-clamp-1 font-bold leading-snug">{campagne.titre}</h3>
            </div>

            {/* Le compte à rebours, au coin le plus regardé. */}
            <span
              className={fusionner(
                "flex shrink-0 flex-col items-center rounded-xl px-2.5 py-1 text-center leading-none",
                dernierJour
                  ? "bg-red-500 text-white"
                  : "bg-accent-doux text-[color:var(--color-accent-fort)]",
              )}
            >
              {presse ? (
                <>
                  <motion.span
                    animate={{ opacity: [1, 0.55, 1] }}
                    transition={{ duration: 1.6, repeat: Infinity }}
                    className="text-[0.68rem] font-extrabold uppercase tracking-wide"
                  >
                    {dernierJour ? "Dernier jour" : "Demain"}
                  </motion.span>
                </>
              ) : (
                <>
                  <span className="tabulaire text-lg font-extrabold">
                    {campagne.jours_restants}
                  </span>
                  <span className="text-[0.6rem] font-semibold uppercase">jours</span>
                </>
              )}
            </span>
          </div>

          <div className="space-y-1.5">
            <Jauge
              pourcentage={campagne.pourcentage}
              atteint={campagne.minimum_atteint}
              compact
            />
            <p className="tabulaire text-xs">
              {campagne.minimum_atteint ? (
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  Objectif atteint — la campagne partira
                </span>
              ) : (
                <>
                  <strong className="text-[color:var(--color-accent)]">
                    {manque} pièce{manque > 1 ? "s" : ""}
                  </strong>{" "}
                  <span className="texte-doux">manquantes pour que ça parte</span>
                </>
              )}
            </p>
          </div>

          <div className="flex items-end justify-between gap-3">
            <div>
              <p className="tabulaire text-lg font-extrabold">
                {francs(campagne.prix_courant)}
              </p>
              <span className="texte-doux flex items-center gap-1 text-xs">
                <Users className="size-3" />
                {campagne.nombre_participants} participants
              </span>
            </div>
            <span className="flex items-center gap-1 text-sm font-semibold text-[color:var(--color-accent)]">
              Rejoindre
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
            </span>
          </div>
        </div>
      </Link>
    </motion.article>
  );
}

/** L'en-tête de la section, avec son compteur. */
export function TitreDerniereChance({ nombre }: { nombre: number }) {
  return (
    <div className="flex items-end justify-between gap-4">
      <div className="flex items-center gap-3">
        <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-red-50 text-red-600 dark:bg-red-950/60 dark:text-red-400">
          <motion.span
            animate={{ scale: [1, 1.12, 1] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            <Flame className="size-5" />
          </motion.span>
        </span>
        <div>
          <h2 className="text-xl font-bold">Dernière chance</h2>
          <p className="texte-doux text-sm">
            {nombre} campagne{nombre > 1 ? "s" : ""} se termine
            {nombre > 1 ? "nt" : ""} bientôt — après, il faudra attendre le
            prochain arrivage.
          </p>
        </div>
      </div>
      <Link
        to="/catalogue?tri=fin_proche"
        className="hidden shrink-0 text-sm font-semibold text-[color:var(--color-accent)] hover:underline sm:block"
      >
        Tout voir
      </Link>
    </div>
  );
}
