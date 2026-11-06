import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect } from "react";
import { createPortal } from "react-dom";

import { fusionner } from "@commun/composants/ui";

/**
 * Une feuille modale responsive contrainte au format mobile.
 *
 * Sur téléphone, elle monte du bas de l'écran comme un bottom-sheet natif.
 * Sur grand écran / desktop, elle reste centrée dans le gabarit mobile (max-w-md),
 * évitant ainsi d'exploser sur toute la largeur de l'écran.
 */
export function Feuille({
  ouverte,
  surFermeture,
  titre,
  className,
  children,
}: {
  ouverte: boolean;
  surFermeture: () => void;
  titre?: string;
  className?: string;
  children: React.ReactNode;
}) {
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
        <div className="fixed inset-0 z-50 flex items-end justify-center">
          {/* Arrière-plan semi-transparent flouté */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={surFermeture}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />

          {/* Boîte de dialogue contrainte strictement à la colonne mobile max-w-md */}
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
              if (info.offset.y > 110 || info.velocity.y > 650) surFermeture();
            }}
            className={fusionner(
              "relative max-h-[92dvh] w-full max-w-md overflow-y-auto rounded-t-3xl shadow-2xl",
              "border-t border-x border-slate-200/80 bg-white",
              className,
            )}
            style={{ background: "var(--fond-carte, #ffffff)" }}
          >
            {/* Barre d'en-tête avec poignée tactile et bouton de fermeture */}
            <div
              className="sticky top-0 z-10 flex items-center justify-between gap-3 rounded-t-3xl px-5 pb-2.5 pt-3 border-b border-slate-100"
              style={{ background: "var(--fond-carte, #ffffff)" }}
            >
              <span
                className="absolute left-1/2 top-2 h-1 w-10 -translate-x-1/2 rounded-full bg-slate-300"
                aria-hidden
              />
              <h2 className="mt-2 text-base font-bold text-slate-900">{titre}</h2>
              <button
                onClick={surFermeture}
                className="mt-2 grid size-8 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-900"
                aria-label="Fermer"
              >
                <X className="size-4" />
              </button>
            </div>

            <div className="px-5 py-4 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
              {children}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
