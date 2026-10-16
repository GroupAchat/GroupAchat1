import type { RoleChrome } from "./chrome";
import { IconeAlerte, IconeCoche, IconeInfo } from "./Icones";

/**
 * `Encart` — SPEC_ECRANS_FIGMA.md §2.11.
 *
 * Fond teinte, icone + texte, coins 12, **sans bordure ni ombre** : sur fond
 * blanc, un aplat de couleur douce se detache seul.
 *
 * L'orange presse, le vert confirme, le rouge arrete (§1.2). Un encart `info`
 * et un encart `attention` ne disent donc pas la meme chose, et leur couleur le
 * dit avant le texte — ne pas les intervertir pour des raisons d'equilibre
 * visuel.
 *
 * ## ⚠️ `info` n'est plus bleu, des deux cotes
 *
 * Il l'etait cote acheteur, et le cote groupeur le neutralisait deja parce
 * qu'un encart bleu dans un chrome bleu ne signale plus rien. **Le neutre est
 * desormais la regle pour les deux**, sur demande : le bleu s'etait installe
 * par petites boites un peu partout sur les ecrans acheteur, ou il n'a rien a
 * faire — c'est le chrome du cote groupeur.
 *
 * `texte-secondaire` sur `surface-douce` tient **7,01:1**, calcule. Et `info`
 * reste distinct des trois autres : il est le seul sans teinte.
 */
export type VarianteEncart = "info" | "attention" | "succes" | "danger";

const STYLES: Record<VarianteEncart, string> = {
  info: "bg-surface-douce text-texte-secondaire",
  attention: "bg-primaire-fond text-primaire-texte-sur-fond",
  succes: "bg-succes-fond text-succes",
  danger: "bg-danger-fond text-danger",
};

const ICONES: Record<
  VarianteEncart,
  (p: { taille?: number; className?: string }) => React.ReactElement
> = {
  info: IconeInfo,
  attention: IconeAlerte,
  succes: IconeCoche,
  danger: IconeAlerte,
};

export default function Encart({
  variante,
  titre,
  role = "acheteur",
  children,
}: {
  variante: VarianteEncart;
  titre?: string;
  /**
   * ⚠️ **Ne sert plus a neutraliser `info`**, qui l'est desormais partout.
   * Conserve parce que `attention`, `succes` et `danger` pourraient avoir
   * besoin de se distinguer par chrome, et parce que les appelants le passent
   * deja.
   */
  role?: RoleChrome;
  children: React.ReactNode;
}) {
  const Icone = ICONES[variante];
  /* `role` ne modifie plus aucune variante — voir sa documentation. On le lit
     quand meme pour que TypeScript ne le signale pas comme inutilise, et pour
     que le jour ou une variante doit diverger, l'endroit soit evident. */
  void role;
  const style = STYLES[variante];

  return (
    <div
      className={`flex items-start gap-2 rounded-xl px-3 py-2.5 text-sm ${style}`}
    >
      <Icone taille={18} className="mt-0.5 shrink-0" />
      <div>
        {titre ? <p className="font-semibold">{titre}</p> : null}
        <p className={titre ? "mt-0.5" : ""}>{children}</p>
      </div>
    </div>
  );
}
