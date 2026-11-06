/** Mises en forme partagées par toute l'interface. */

const FCFA = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });

/** « 16 500 FCFA ». L'espace est insécable : un montant ne se coupe pas. */
export function francs(montant: number): string {
  return `${FCFA.format(montant)} FCFA`;
}

/** Version courte pour les vignettes : « 16,5 k » au-delà de dix mille. */
export function francsCourt(montant: number): string {
  if (montant >= 1_000_000) {
    return `${(montant / 1_000_000).toFixed(montant % 1_000_000 === 0 ? 0 : 1)} M`;
  }
  if (montant >= 10_000) return `${Math.round(montant / 1000)} k`;
  return FCFA.format(montant);
}

/** « +228 90 00 11 22 » à partir des huit chiffres stockés. */
export function telephoneLisible(numero: string): string {
  const chiffres = numero.replace(/\D/g, "").slice(-8);
  if (chiffres.length !== 8) return numero;
  return `+228 ${chiffres.slice(0, 2)} ${chiffres.slice(2, 4)} ${chiffres.slice(4, 6)} ${chiffres.slice(6)}`;
}

const DATE_COURTE = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "short",
});

const DATE_LONGUE = new Intl.DateTimeFormat("fr-FR", {
  day: "numeric",
  month: "long",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function dateCourte(valeur: string): string {
  return DATE_COURTE.format(new Date(valeur));
}

export function dateLongue(valeur: string): string {
  return DATE_LONGUE.format(new Date(valeur));
}

/** « il y a 3 h », « hier », « il y a 2 sem ». */
export function depuis(valeur: string): string {
  const ecart = Date.now() - new Date(valeur).getTime();
  const minutes = Math.floor(ecart / 60000);
  if (minutes < 1) return "à l'instant";
  if (minutes < 60) return `il y a ${minutes} min`;
  const heures = Math.floor(minutes / 60);
  if (heures < 24) return `il y a ${heures} h`;
  const jours = Math.floor(heures / 24);
  if (jours === 1) return "hier";
  if (jours < 7) return `il y a ${jours} j`;
  const semaines = Math.floor(jours / 7);
  if (semaines < 5) return `il y a ${semaines} sem`;
  return dateCourte(valeur);
}

/** « 3 jours », « dernier jour » — ce qu'on affiche sur un compte à rebours. */
export function tempsRestant(jours: number): string {
  if (jours <= 0) return "dernier jour";
  if (jours === 1) return "1 jour";
  return `${jours} jours`;
}

export function pluriel(nombre: number, singulier: string, pluriel?: string): string {
  const forme = nombre > 1 ? (pluriel ?? `${singulier}s`) : singulier;
  return `${FCFA.format(nombre)} ${forme}`;
}

/** Le code de retrait se lit par blocs de quatre : « A9PE KDXQ ». */
export function codeLisible(code: string): string {
  return code.replace(/(.{4})(?=.)/g, "$1 ");
}

export function initiales(nom: string | null | undefined): string {
  return (nom ?? "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((morceau) => morceau[0]?.toUpperCase() ?? "")
    .join("");
}

/**
 * Palette moderne de dégradés élégants pour les avatars de profil.
 */
const PALETTE_AVATAR = [
  "linear-gradient(135deg, #f97316 0%, #ea580c 100%)", // Orange chaleureux Group Achat
  "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)", // Bleu royal éclatant
  "linear-gradient(135deg, #10b981 0%, #059669 100%)", // Émeraude fraîche
  "linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)", // Violet moderne
  "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", // Ambre doré
  "linear-gradient(135deg, #06b6d4 0%, #0284c7 100%)", // Océan cyan
  "linear-gradient(135deg, #ec4899 0%, #be185d 100%)", // Framboise
  "linear-gradient(135deg, #6366f1 0%, #4338ca 100%)", // Indigo profond
];

export function teinteDe(graine: string | null | undefined): string {
  if (!graine || graine.trim() === "") return PALETTE_AVATAR[0];
  let somme = 0;
  for (let i = 0; i < graine.length; i++) {
    somme = (somme * 31 + graine.charCodeAt(i)) >>> 0;
  }
  return PALETTE_AVATAR[somme % PALETTE_AVATAR.length];
}

/**
 * Un taux de commission, depuis les centièmes de pour-cent du serveur.
 *
 * L'API travaille en entiers — 350 pour 3,5 % — parce que tous les montants
 * de l'application sont des francs entiers et qu'un décimal rouvrirait
 * l'arrondi à chaque calcul. La conversion n'a lieu qu'ici, à l'affichage.
 */
export function tauxCommission(centiemes: number): string {
  const pourcent = centiemes / 100;
  const texte = Number.isInteger(pourcent)
    ? String(pourcent)
    : pourcent.toFixed(1).replace(".", ",");
  return `${texte} %`;
}

/** La commission due sur un montant, arrondie comme le serveur : vers le bas. */
export function commissionSur(montant: number, centiemes: number): number {
  return Math.floor((Math.max(0, montant) * Math.max(0, centiemes)) / 10000);
}

const NOMS_DE_GRADE: Record<string, string> = {
  nouveau: "Nouveau",
  bronze: "Bronze",
  argent: "Argent",
  or: "Or",
};

export function gradeLisible(grade: string): string {
  return NOMS_DE_GRADE[grade] ?? "Nouveau";
}
