import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect } from "react";
import { createPortal } from "react-dom";

import { fusionner } from "@commun/composants/ui";

/**
 * Une feuille qui monte du bas de l'écran.
 *
 * Sur téléphone c'est le bon endroit pour une décision : elle arrive sous le
 * pouce, laisse voir le contexte derrière, et se referme d'un geste. Sur
 * grand écran elle se recentre et devient une boîte de dialogue ordinaire.
 */
export function Feuille({
  ouverte,
  surFermeture,
  titre,
  children,
}: {
  ouverte: boolean;
  surFermeture: () => void;
  titre?: string;
  children: React.ReactNode;
}) {
  // La page de dessous ne doit pas défiler pendant qu'on décide, sinon on
  // perd sa place dans le catalogue en fermant la feuille.
  useEffect(() => {
    if (!ouverte) return;
    const avant = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const auClavier = (evenement: KeyboardEvent) => {
      if (evenement.key === "Escape") surFermeture();
    };
    window.addEventListener("keydown", auClavier);
    return () => {
      document.body.style.overflow = avant;
      window.removeEventListener("keydown", auClavier);
    };
  }, [ouverte, surFermeture]);

  return createPortal(
    <AnimatePresence>
      {ouverte && (
        <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={surFermeture}
            className="absolute inset-0 bg-black/45 backdrop-blur-sm"
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label={titre}
            initial={{ y: "100%", opacity: 0.6 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: "100%", opacity: 0.6 }}
            transition={{ type: "spring", stiffness: 360, damping: 34 }}
            drag="y"
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={{ top: 0, bottom: 0.45 }}
            onDragEnd={(_, info) => {
              // Un geste franc vers le bas ferme ; un frôlement, non.
              if (info.offset.y > 110 || info.velocity.y > 650) surFermeture();
            }}
            className={fusionner(
              "relative max-h-[92dvh] w-full overflow-y-auto rounded-t-[1.75rem] sm:max-w-lg sm:rounded-[1.75rem]",
              "shadow-2xl",
            )}
            style={{ background: "var(--fond-carte)" }}
          >
            <div className="sticky top-0 z-10 flex items-center justify-between gap-3 rounded-t-[1.75rem] px-5 pb-2 pt-3"
                 style={{ background: "var(--fond-carte)" }}>
              <span
                className="absolute left-1/2 top-2 h-1 w-10 -translate-x-1/2 rounded-full sm:hidden"
                style={{ background: "var(--bordure)" }}
                aria-hidden
              />
              <h2 className="mt-3 text-lg font-bold">{titre}</h2>
              <button
                onClick={surFermeture}
                className="mt-3 grid size-9 shrink-0 place-items-center rounded-full transition-colors hover:surface-douce"
                aria-label="Fermer"
              >
                <X className="size-4" />
              </button>
            </div>
            <div className="px-5 pb-[max(1.25rem,env(safe-area-inset-bottom))]">
              {children}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
