/**
 * Exporter un tableau en CSV, depuis le navigateur.
 *
 * ## Pourquoi pas une route serveur
 *
 * Le bouton « Exporter » de l'ecran 21 ne faisait rien. Les chiffres de cet
 * ecran ne viennent d'ailleurs d'aucune route dediee : ils sont **calcules sur
 * les campagnes deja chargees**. Les redemander au serveur uniquement pour
 * fabriquer un fichier serait un aller-retour pour des donnees qu'on a sous la
 * main — et le forfait de donnees limite du §5 est une contrainte de ce
 * produit, pas un detail.
 *
 * ## Deux details qui decident si le fichier s'ouvre ou non
 *
 * Un CSV mal forme n'echoue pas : il s'ouvre **de travers**, et c'est pire.
 *
 * - **Le point-virgule, pas la virgule.** Excel en configuration francaise
 *   attend `;`. Avec `,`, tout le tableau atterrit dans une seule colonne.
 *   Et comme nos montants s'ecrivent avec une virgule decimale, la virgule
 *   comme separateur casserait en plus chaque nombre en deux.
 * - **La marque d'ordre des octets (BOM).** Sans elle, Excel lit le fichier
 *   dans l'encodage du systeme et « Écouteurs » devient « Ã‰couteurs ». Trois
 *   octets au debut suffisent a l'eviter — et sur un produit entierement
 *   francais, ce n'est pas un cas rare, c'est le cas general.
 */

/** Echappe une cellule : guillemets doubles, et guillemet double a l'interieur. */
function cellule(valeur: string | number): string {
  const texte = String(valeur);
  /* On encadre des qu'il y a un separateur, un guillemet ou un retour a la
     ligne. Un nom de produit peut contenir les trois — « Chemise homme, lot
     de 3 » en contient deja un. */
  return /[";\r\n]/.test(texte)
    ? `"${texte.replace(/"/g, '""')}"`
    : texte;
}

/** Assemble les lignes en un CSV precede de sa marque d'ordre des octets. */
export function construireCsv(
  entetes: readonly string[],
  lignes: readonly (readonly (string | number)[])[],
): string {
  const corps = [entetes, ...lignes]
    .map((ligne) => ligne.map(cellule).join(";"))
    .join("\r\n");
  return `\ufeff${corps}`;
}

/**
 * Propose le fichier au telechargement.
 *
 * ⚠️ **L'URL temporaire est revoquee.** Chaque `createObjectURL` retient son
 * contenu en memoire jusqu'a la fermeture de l'onglet : sans la revocation, un
 * groupeur qui exporte dix fois garde dix copies. On attend le prochain tour
 * de boucle, parce que revoquer dans la meme pile annule parfois le
 * telechargement avant qu'il ne commence.
 */
export function telechargerCsv(nomDuFichier: string, contenu: string): void {
  const objet = new Blob([contenu], { type: "text/csv;charset=utf-8" });
  const adresse = URL.createObjectURL(objet);
  const lien = document.createElement("a");
  lien.href = adresse;
  lien.download = nomDuFichier;
  document.body.append(lien);
  lien.click();
  lien.remove();
  window.setTimeout(() => URL.revokeObjectURL(adresse), 0);
}
