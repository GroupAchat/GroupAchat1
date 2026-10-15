import { useId } from "react";

/**
 * `Champ` — SPEC_ECRANS_FIGMA.md §2.9.
 *
 * **Libelle 14 au-dessus du champ, jamais un simple placeholder** : un
 * placeholder disparait a la saisie et l'utilisateur ne sait plus ce qu'il
 * remplit. Hauteur 52, coins 10, fond blanc avec un contour de 1 px
 * `bordure` — sur fond blanc, c'est le contour qui dit « ici on ecrit ».
 *
 * Etats : `vide`, `rempli`, `focus` (contour `primaire` 2 px), `erreur`
 * (contour `danger` + message 12 dessous), `desactive` (fond `surface-douce`,
 * l'un des trois usages autorises du gris).
 */
export default function Champ({
  libelle,
  valeur,
  onChanger,
  exemple,
  erreur,
  type = "text",
  inputMode,
  autoComplete,
  prefixe,
  aide,
  desactive = false,
  autoFocus = false,
}: {
  libelle: string;
  valeur: string;
  onChanger: (valeur: string) => void;
  exemple?: string;
  erreur?: string;
  type?: "text" | "tel" | "email" | "password";
  /**
   * `email` ouvre le clavier avec l'arobase et le point, sans espace. Sur un
   * telephone, c'est la difference entre saisir une adresse et se battre avec
   * le clavier.
   */
  inputMode?: "text" | "tel" | "numeric" | "email";
  /**
   * Ce que le navigateur doit comprendre du champ.
   *
   * ⚠️ **Indispensable sur un mot de passe, et pas pour le confort.** Sans
   * `autoComplete="new-password"`, aucun gestionnaire ne propose d'en
   * enregistrer un — et un mot de passe de huit caractères que rien ne retient
   * finit écrit sur un papier, ou choisi assez faible pour tenir de mémoire.
   * Les deux valeurs ne sont pas interchangeables : `current-password` sur un
   * champ de création fait proposer l'ancien, `new-password` sur un champ de
   * connexion empêche de proposer celui qu'on a enregistré.
   */
  autoComplete?:
    | "new-password"
    | "current-password"
    | "email"
    | "tel"
    | "name"
    | "given-name";
  /** Prefixe fige a gauche, par exemple `+228` sur le numero (ecran 4). */
  prefixe?: string;
  /** Mention 12 px sous le champ, quand elle n'est pas une erreur. */
  aide?: string;
  desactive?: boolean;
  autoFocus?: boolean;
}) {
  const id = useId();
  const idAide = `${id}-aide`;

  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-texte">
        {libelle}
      </label>
      <div
        className={`mt-1.5 flex h-13 items-center rounded-[10px] border bg-white px-3 focus-within:border-2 ${
          erreur
            ? "border-danger focus-within:border-danger"
            : "border-bordure-champ focus-within:border-primaire"
        } ${desactive ? "border-bordure bg-surface-douce" : ""}`}
      >
        {prefixe ? (
          <span className="mr-2 shrink-0 text-texte-secondaire">{prefixe}</span>
        ) : null}
        <input
          id={id}
          type={type}
          inputMode={inputMode}
          autoComplete={autoComplete}
          value={valeur}
          disabled={desactive}
          autoFocus={autoFocus}
          placeholder={exemple}
          onChange={(evenement) => onChanger(evenement.target.value)}
          aria-invalid={erreur ? true : undefined}
          aria-describedby={erreur || aide ? idAide : undefined}
          className="h-full w-full bg-transparent outline-none placeholder:text-texte-secondaire disabled:text-texte-secondaire"
        />
      </div>
      {erreur || aide ? (
        <p
          id={idAide}
          className={`mt-1 text-xs ${erreur ? "text-danger" : "text-texte-secondaire"}`}
        >
          {erreur ?? aide}
        </p>
      ) : null}
    </div>
  );
}
