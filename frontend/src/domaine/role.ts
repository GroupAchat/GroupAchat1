/**
 * Les trois publics de la boutique, et par ou chacun entre.
 *
 * | Role | Ecrans | Comment on y arrive |
 * |---|---|---|
 * | **Acheteur** | 1 a 12 | On ouvre le site et on repond a l'ecran de profil |
 * | **Groupeur** | 13 a 21 | Meme ecran de profil, puis l'inscription et le KYC |
 * | **Livreur** | 22 | On ouvre **un lien recu le matin** |
 *
 * L'administration n'est pas dans cette liste : elle a sa propre application
 * sur un autre port (`src/admin/`). Offrir un chemin, meme de demonstration,
 * entre la boutique et l'outil interne reviendrait a defaire cette separation.
 */
export type Role = "acheteur" | "groupeur" | "livreur";

/** Les roles qu'on peut demander par l'adresse. */
const ROLES_PAR_ADRESSE: readonly Role[] = ["livreur"];

/**
 * Lit un role demande dans l'adresse : `?role=livreur`.
 *
 * **Seul le livreur peut entrer ainsi, et ce n'est pas une restriction
 * arbitraire.** Un acheteur et un groupeur choisissent leur profil dans
 * l'interface ; un livreur, lui, n'a ni compte ni application — il recoit un
 * lien qui ne couvre que la tournee du jour et qui expire le soir (§6 du
 * cahier des charges). L'adresse **est** son mode d'entree, pas un raccourci.
 *
 * Autoriser `?role=groupeur` ouvrirait en revanche un contournement de
 * l'inscription et du dossier KYC — et ce dossier est ce qui nous permet
 * d'honorer « vous etes livre, ou rembourse » : nous remboursons l'acheteur et
 * nous nous retournons contre le groupeur, ce qui suppose de savoir qui il
 * est. D'ou la liste blanche.
 *
 * ⚠️ Aujourd'hui le lien n'est pas signe : n'importe qui peut taper
 * `?role=livreur` et voir la tournee de demonstration. **C'est acceptable tant
 * que les donnees sont fictives, et plus du tout ensuite** — cette page est la
 * seule du produit qui porte des noms, des adresses et des numeros. Le jeton
 * de tournee se lira ici, a cote de ce parametre.
 */
export function roleDepuisAdresse(): Role | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  const demande = new URLSearchParams(window.location.search).get("role");
  return ROLES_PAR_ADRESSE.find((role) => role === demande);
}
