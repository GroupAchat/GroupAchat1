import { motion } from "framer-motion";
import { Eye, EyeOff } from "lucide-react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { forwardRef, useState } from "react";

import { initiales, teinteDe } from "@commun/outils/formats";

/** La petite trousse de composants partagée par les deux applications. */

export function fusionner(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

// ── Boutons ────────────────────────────────────────────────────────────────

type Ton = "accent" | "contour" | "doux" | "fantome" | "danger";
type Taille = "sm" | "md" | "lg";

const TONS: Record<Ton, string> = {
  accent:
    "degrade-accent text-white lueur-accent hover:brightness-105 active:brightness-95",
  contour:
    "surface text-[color:var(--texte)] hover:border-[color:var(--color-accent)] hover:text-[color:var(--color-accent)]",
  doux: "bg-accent-doux text-[color:var(--color-accent-fort)] hover:brightness-97",
  fantome: "text-[color:var(--texte-doux)] hover:surface-douce",
  danger: "bg-red-600 text-white hover:bg-red-700",
};

const TAILLES: Record<Taille, string> = {
  sm: "h-9 px-3.5 text-sm gap-1.5",
  md: "h-11 px-5 text-[0.95rem] gap-2",
  lg: "h-14 px-7 text-base gap-2.5",
};

interface ProprietesBouton extends ButtonHTMLAttributes<HTMLButtonElement> {
  ton?: Ton;
  taille?: Taille;
  pleineLargeur?: boolean;
  chargement?: boolean;
  icone?: ReactNode;
}

export function Bouton({
  ton = "accent",
  taille = "md",
  pleineLargeur,
  chargement,
  icone,
  children,
  className,
  disabled,
  ...reste
}: ProprietesBouton) {
  return (
    <button
      {...reste}
      disabled={disabled || chargement}
      className={fusionner(
        "inline-flex items-center justify-center rounded-full font-semibold",
        "transition-all duration-200 active:scale-[0.97]",
        "disabled:pointer-events-none disabled:opacity-55",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[color:var(--color-accent)]",
        TONS[ton],
        TAILLES[taille],
        pleineLargeur && "w-full",
        className,
      )}
    >
      {chargement ? <Tourniquet /> : icone}
      {children}
    </button>
  );
}

export function Tourniquet({ className }: { className?: string }) {
  return (
    <span
      className={fusionner(
        "inline-block size-4 animate-spin rounded-full border-2 border-current border-t-transparent",
        className,
      )}
      aria-hidden
    />
  );
}

// ── Saisies ────────────────────────────────────────────────────────────────

interface ProprietesChamp extends InputHTMLAttributes<HTMLInputElement> {
  etiquette: string;
  erreur?: string;
  aide?: string;
  prefixe?: ReactNode;
}

export const Champ = forwardRef<HTMLInputElement, ProprietesChamp>(function Champ(
  { etiquette, erreur, aide, prefixe, className, id, type, ...reste },
  ref,
) {
  const identifiant = id ?? `champ-${etiquette.replace(/\W+/g, "-").toLowerCase()}`;
  // Un mot de passe tapé à l'aveugle sur un clavier de téléphone se trompe
  // souvent, et l'erreur ne se voit qu'au refus du serveur. L'œil le rend
  // relisible avant l'envoi ; il vit ici pour servir les trois formulaires
  // (inscription, connexion boutique, connexion console) d'un seul coup.
  const estMotDePasse = type === "password";
  const [visible, setVisible] = useState(false);
  return (
    <div className="space-y-1.5">
      <label htmlFor={identifiant} className="block text-sm font-medium">
        {etiquette}
      </label>
      <div
        className={fusionner(
          "flex items-center gap-2 rounded-2xl border px-4 transition-colors",
          "focus-within:border-[color:var(--color-accent)]",
          "focus-within:ring-4 focus-within:ring-[color:var(--color-accent)]/12",
          erreur ? "border-red-500" : "surface",
        )}
        style={{ background: "var(--fond-carte)" }}
      >
        {prefixe && <span className="texte-doux text-sm">{prefixe}</span>}
        <input
          {...reste}
          type={estMotDePasse && visible ? "text" : type}
          ref={ref}
          id={identifiant}
          aria-invalid={Boolean(erreur)}
          aria-describedby={erreur ? `${identifiant}-erreur` : undefined}
          className={fusionner(
            "h-12 w-full bg-transparent text-[0.95rem] outline-none",
            "placeholder:text-[color:var(--texte-doux)]/60",
            className,
          )}
        />
        {estMotDePasse && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
            aria-pressed={visible}
            aria-controls={identifiant}
            className={fusionner(
              "texte-doux -mr-2 grid h-10 w-10 shrink-0 place-items-center rounded-full",
              "transition-colors hover:text-[color:var(--color-accent)]",
              "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[color:var(--color-accent)]",
            )}
          >
            {visible ? <EyeOff className="h-5 w-5" aria-hidden /> : <Eye className="h-5 w-5" aria-hidden />}
          </button>
        )}
      </div>
      {erreur ? (
        <p id={`${identifiant}-erreur`} className="text-sm text-red-600">
          {erreur}
        </p>
      ) : (
        aide && <p className="texte-doux text-xs">{aide}</p>
      )}
    </div>
  );
});

export function ZoneTexte({
  etiquette,
  erreur,
  ...reste
}: { etiquette: string; erreur?: string } & React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium">{etiquette}</label>
      <textarea
        {...reste}
        className={fusionner(
          "surface w-full rounded-2xl px-4 py-3 text-[0.95rem] outline-none transition-colors",
          "focus:border-[color:var(--color-accent)] focus:ring-4 focus:ring-[color:var(--color-accent)]/12",
          erreur && "border-red-500",
        )}
      />
      {erreur && <p className="text-sm text-red-600">{erreur}</p>}
    </div>
  );
}

// ── Étiquettes et avatars ──────────────────────────────────────────────────

export function Etiquette({
  children,
  ton = "neutre",
  className,
}: {
  children: ReactNode;
  ton?: "neutre" | "accent" | "succes" | "alerte" | "danger" | "sombre";
  className?: string;
}) {
  const tons = {
    neutre: "surface-douce texte-doux",
    accent: "bg-accent-doux text-[color:var(--color-accent-fort)]",
    succes: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
    alerte: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
    danger: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
    sombre: "verre-sombre text-white",
  };
  return (
    <span
      className={fusionner(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold",
        tons[ton],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Avatar({
  nom,
  taille = 40,
  className,
}: {
  nom: string;
  taille?: number;
  className?: string;
}) {
  return (
    <span
      className={fusionner(
        "inline-grid shrink-0 place-items-center rounded-full font-bold text-white",
        className,
      )}
      style={{
        width: taille,
        height: taille,
        fontSize: taille * 0.38,
        background: teinteDe(nom),
      }}
      aria-hidden
    >
      {initiales(nom)}
    </span>
  );
}

// ── États ──────────────────────────────────────────────────────────────────

export function Squelette({ className }: { className?: string }) {
  return <div className={fusionner("squelette rounded-2xl", className)} />;
}

export function EtatVide({
  icone,
  titre,
  texte,
  action,
}: {
  icone?: ReactNode;
  titre: string;
  texte?: string;
  action?: ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center gap-3 px-6 py-16 text-center"
    >
      {icone && (
        <span className="grid size-16 place-items-center rounded-3xl bg-accent-doux text-[color:var(--color-accent)]">
          {icone}
        </span>
      )}
      <h3 className="text-lg font-bold">{titre}</h3>
      {texte && <p className="texte-doux max-w-sm text-sm">{texte}</p>}
      {action && <div className="mt-2">{action}</div>}
    </motion.div>
  );
}

export function Carte({
  children,
  className,
  survol,
}: {
  children: ReactNode;
  className?: string;
  survol?: boolean;
}) {
  return (
    <div
      className={fusionner(
        "surface rounded-[var(--radius-carte)] p-5",
        survol &&
          "transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/5",
        className,
      )}
    >
      {children}
    </div>
  );
}

/** Bandeau d'erreur, pour les messages que l'API renvoie en clair. */
export function Alerte({ children, ton = "danger" }: { children: ReactNode; ton?: "danger" | "info" }) {
  if (!children) return null;
  return (
    <motion.p
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      className={fusionner(
        "rounded-2xl px-4 py-3 text-sm",
        ton === "danger"
          ? "bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-300"
          : "bg-accent-doux text-[color:var(--color-accent-fort)]",
      )}
      role={ton === "danger" ? "alert" : undefined}
    >
      {children}
    </motion.p>
  );
}
