import { motion } from "framer-motion";

import { fusionner } from "@commun/composants/ui";

/**
 * La jauge de collecte — l'élément le plus regardé de toute l'application.
 *
 * Elle s'anime depuis zéro à l'apparition : voir la barre monter dit en un
 * geste « ça avance », là où une barre déjà remplie ne dit rien.
 */
export function Jauge({
  pourcentage,
  atteint,
  compact,
  className,
}: {
  pourcentage: number;
  atteint?: boolean;
  compact?: boolean;
  className?: string;
}) {
  const valeur = Math.min(100, Math.max(0, pourcentage));
  return (
    <div
      className={fusionner(
        "relative w-full overflow-hidden rounded-full",
        compact ? "h-1.5" : "h-2.5",
        className,
      )}
      style={{ background: "color-mix(in srgb, var(--texte) 10%, transparent)" }}
      role="progressbar"
      aria-valuenow={valeur}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <motion.div
        className={fusionner(
          "h-full rounded-full",
          atteint ? "bg-emerald-500" : "degrade-accent",
        )}
        initial={{ width: 0 }}
        animate={{ width: `${valeur}%` }}
        transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
      />
      {/* Un reflet qui balaie la barre tant que l'objectif n'est pas atteint :
          discret, mais il attire l'œil là où se joue la décision d'achat. */}
      {!atteint && valeur > 4 && valeur < 100 && (
        <motion.span
          className="pointer-events-none absolute inset-y-0 w-16 bg-gradient-to-r from-transparent via-white/45 to-transparent"
          initial={{ x: "-4rem" }}
          animate={{ x: ["-4rem", "100%"] }}
          transition={{ duration: 2.4, repeat: Infinity, repeatDelay: 1.6, ease: "easeInOut" }}
        />
      )}
    </div>
  );
}

/** Anneau de progression, pour les tableaux de bord. */
export function Anneau({
  pourcentage,
  taille = 72,
  epaisseur = 7,
  children,
}: {
  pourcentage: number;
  taille?: number;
  epaisseur?: number;
  children?: React.ReactNode;
}) {
  const rayon = (taille - epaisseur) / 2;
  const circonference = 2 * Math.PI * rayon;
  const valeur = Math.min(100, Math.max(0, pourcentage));

  return (
    <div className="relative grid place-items-center" style={{ width: taille, height: taille }}>
      <svg width={taille} height={taille} className="-rotate-90">
        <circle
          cx={taille / 2}
          cy={taille / 2}
          r={rayon}
          fill="none"
          strokeWidth={epaisseur}
          stroke="color-mix(in srgb, var(--texte) 10%, transparent)"
        />
        <motion.circle
          cx={taille / 2}
          cy={taille / 2}
          r={rayon}
          fill="none"
          strokeWidth={epaisseur}
          strokeLinecap="round"
          stroke="var(--color-accent)"
          strokeDasharray={circonference}
          initial={{ strokeDashoffset: circonference }}
          animate={{ strokeDashoffset: circonference * (1 - valeur / 100) }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <span className="absolute grid place-items-center text-center">{children}</span>
    </div>
  );
}
