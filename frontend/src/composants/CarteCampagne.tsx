import { motion } from "framer-motion";
import { BadgeCheck, Clock, MapPin, Users } from "lucide-react";
import { Link } from "react-router-dom";

import type { CampagneResume } from "@commun/api/types";
import { Jauge } from "@/composants/Jauge";
import { Etiquette } from "@commun/composants/ui";
import { Visuel } from "@/composants/Visuel";
import { francs, tempsRestant } from "@commun/outils/formats";

/** La vignette du catalogue, en grille. */
export function CarteCampagne({
  campagne,
  index = 0,
}: {
  campagne: CampagneResume;
  index?: number;
}) {
  const remise =
    campagne.prix_courant < campagne.prix_unitaire
      ? Math.round(
          ((campagne.prix_unitaire - campagne.prix_courant) / campagne.prix_unitaire) * 100,
        )
      : 0;
  const urgent = campagne.jours_restants <= 2 && campagne.statut === "en_cours";

  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      // Le décalage reste plafonné : au-delà de la huitième vignette, attendre
      // son tour donnerait l'impression que la page rame.
      transition={{ duration: 0.45, delay: Math.min(index, 8) * 0.05, ease: [0.22, 1, 0.36, 1] }}
      className="group surface overflow-hidden rounded-[var(--radius-carte)] transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-black/8"
    >
      <Link to={`/campagnes/${campagne.id}`} className="block">
        <div className="relative aspect-[4/3] overflow-hidden">
          <div className="size-full transition-transform duration-500 group-hover:scale-105">
            <Visuel source={campagne.produit.image} nom={campagne.produit.nom} />
          </div>

          <div className="absolute left-3 top-3 flex flex-wrap gap-1.5">
            {remise > 0 && (
              <Etiquette ton="sombre" className="backdrop-blur">
                −{remise} % atteint
              </Etiquette>
            )}
            {urgent && (
              <Etiquette ton="sombre" className="backdrop-blur">
                <Clock className="size-3" />
                {tempsRestant(campagne.jours_restants)}
              </Etiquette>
            )}
          </div>

          {campagne.minimum_atteint && (
            <span className="absolute right-3 top-3 rounded-full bg-emerald-500 px-2.5 py-1 text-xs font-bold text-white shadow-lg">
              Objectif atteint
            </span>
          )}
        </div>

        <div className="space-y-3 p-4">
          <div className="space-y-1">
            <p className="texte-doux text-xs font-medium uppercase tracking-wide">
              {campagne.produit.categorie_nom}
            </p>
            <h3 className="line-clamp-2 text-[0.98rem] font-bold leading-snug">
              {campagne.titre}
            </h3>
          </div>

          <div className="flex items-end justify-between gap-2">
            <div>
              <p className="tabulaire text-lg font-extrabold text-[color:var(--color-accent)]">
                {francs(campagne.prix_courant)}
              </p>
              {remise > 0 && (
                <p className="texte-doux tabulaire text-xs line-through">
                  {francs(campagne.prix_unitaire)}
                </p>
              )}
            </div>
            <span className="texte-doux flex items-center gap-1 text-xs">
              <Users className="size-3.5" />
              {campagne.nombre_participants}
            </span>
          </div>

          <div className="space-y-1.5">
            <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} compact />
            <p className="texte-doux tabulaire text-xs">
              {campagne.quantite_reservee} / {campagne.quantite_minimale} pièces
            </p>
          </div>

          <div className="flex items-center gap-1.5 border-t pt-3 text-xs">
            {campagne.groupeur.badge_confiance && (
              <BadgeCheck className="size-4 shrink-0 text-[color:var(--color-accent)]" />
            )}
            <span className="truncate font-medium">
              {campagne.groupeur.nom_commerce || campagne.groupeur.nom_complet}
            </span>
            <span className="texte-doux ml-auto flex shrink-0 items-center gap-1">
              <MapPin className="size-3" />
              {campagne.point_remise.split(",")[0]}
            </span>
          </div>
        </div>
      </Link>
    </motion.article>
  );
}

export function SqueletteCarte() {
  return (
    <div className="surface overflow-hidden rounded-[var(--radius-carte)]">
      <div className="squelette aspect-[4/3]" />
      <div className="space-y-3 p-4">
        <div className="squelette h-3 w-20 rounded-full" />
        <div className="squelette h-4 w-full rounded-full" />
        <div className="squelette h-5 w-28 rounded-full" />
        <div className="squelette h-2 w-full rounded-full" />
      </div>
    </div>
  );
}
