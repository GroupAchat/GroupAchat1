import { LOGOS } from "@/composants/logos";
import { fusionner } from "@/composants/ui";

/**
 * Le logo : l'emblème, puis le nom.
 *
 * **Le nom est écrit en HTML, pas lu dans le fichier SVG**, et c'est
 * volontaire. Le verrouillage horizontal fourni dessine « Group Achat » dans
 * un `viewBox` calculé pour une fonte précise : dès que la fonte réelle est
 * un peu plus large — ce qui arrive avec la police de secours, ou simplement
 * avec Outfit chargée par le navigateur — **le dernier caractère sort du
 * cadre et se retrouve coupé**. C'est ce qu'on voyait sur la barre du haut.
 *
 * Composer le nom en texte supprime le problème à la racine : il ne peut
 * plus être rogné, il reste net à toutes les tailles, il se met à l'échelle
 * avec le reste de l'interface, et un lecteur d'écran le lit.
 *
 * L'emblème, lui, vient toujours du fichier `public/logos/marque.svg` : le
 * remplacer change l'icône partout, comme avant.
 */

const TAILLES = {
  /** Barres compactes. */
  compacte: { icone: "size-7", texte: "text-[1.05rem]" },
  /** La barre du haut : un cran plus petit sur téléphone. */
  moyenne: { icone: "size-7 sm:size-8", texte: "text-[1.05rem] sm:text-[1.3rem]" },
  /** Écrans d'entrée, pages de présentation. */
  grande: { icone: "size-10", texte: "text-[1.75rem]" },
} as const;

export function Marque({
  className,
  taille = "moyenne",
  variante = "couleur",
}: {
  className?: string;
  taille?: keyof typeof TAILLES;
  /** « blanc » pour les fonds colorés ou sombres. */
  variante?: "couleur" | "blanc";
}) {
  const mesures = TAILLES[taille];
  const blanc = variante === "blanc";

  return (
    <span
      className={fusionner("flex select-none items-center gap-2", className)}
      role="img"
      aria-label="Group Achat"
    >
      <img
        src={LOGOS.marque}
        alt=""
        className={fusionner("shrink-0", mesures.icone)}
        draggable={false}
        aria-hidden
      />
      {/* `whitespace-nowrap` : sur un écran étroit, « Group » et « Achat »
          ne doivent jamais passer à la ligne l'un sous l'autre. */}
      <span
        className={fusionner(
          "whitespace-nowrap font-bold leading-none tracking-[-0.01em]",
          mesures.texte,
        )}
        aria-hidden
      >
        <span style={{ color: blanc ? "#ffffff" : "var(--color-marine-800)" }}>
          Group
        </span>{" "}
        <span style={{ color: blanc ? "#ffffff" : "var(--color-mangue-500)" }}>
          Achat
        </span>
      </span>
    </span>
  );
}

/** L'emblème seul, sans le nom : favicon, pastilles, barres très étroites. */
export function Embleme({
  taille = 32,
  className,
}: {
  taille?: number;
  className?: string;
}) {
  return (
    <img
      src={LOGOS.marque}
      alt=""
      width={taille}
      height={taille}
      style={{ width: taille, height: taille }}
      className={fusionner("select-none", className)}
      draggable={false}
      aria-hidden
    />
  );
}
