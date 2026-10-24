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

export function initiales(nom: string): string {
  return nom
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((morceau) => morceau[0]?.toUpperCase() ?? "")
    .join("");
}

/** Une couleur stable par personne, pour les pastilles d'avatar. */
export function teinteDe(graine: string): string {
  let somme = 0;
  for (const caractere of graine) somme = (somme * 31 + caractere.charCodeAt(0)) % 360;
  return `hsl(${somme} 62% 46%)`;
}
