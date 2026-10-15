import { CATEGORIES, type Categorie, LIBELLE_CATEGORIE } from "../../domaine/groupage";
import { formaterFrancs } from "../../domaine/format";
import {
  type Filtres,
  LIBELLE_TRI,
  ORDRE_TRI,
  SEUIL_PETIT_PRIX,
} from "../../domaine/filtres";

/**
 * La colonne de filtres des grands ecrans.
 *
 * Sur telephone, les memes filtres sont des puces defilantes : c'est la seule
 * forme qui tienne sur 390 px. Ici la place existe, donc on montre tout d'un
 * coup — rien n'est replie, rien n'est cache derriere un bouton « Filtres ».
 *
 * Ce sont **les memes trois filtres** que sur mobile, et c'est volontaire :
 * la place disponible n'est pas une raison d'inventer des criteres. Il n'y a
 * ni notation des groupeurs (§1.7) ni livraison offerte, donc rien a filtrer
 * de ce cote.
 */
export default function PanneauFiltres({
  filtres,
  onChanger,
  comptesCategories,
  total,
}: {
  filtres: Filtres;
  onChanger: (filtres: Filtres) => void;
  comptesCategories: Record<Categorie, number>;
  total: number;
}) {
  const modifier = (partie: Partial<Filtres>) =>
    onChanger({ ...filtres, ...partie });

  return (
    /* `sticky` : la colonne suit le defilement de la grille, ce qui evite de
       remonter en haut de page pour changer un filtre. */
    <aside className="sticky top-36 w-60 shrink-0 self-start">
      <h2 className="text-lg font-semibold text-texte">Filtrer</h2>

      <section className="mt-5">
        <h3 className="text-sm font-semibold text-texte">Catégorie</h3>
        <ul className="mt-2 space-y-0.5">
          <li>
            <LigneFiltre
              actif={filtres.categorie === "toutes"}
              compte={total}
              onClick={() => modifier({ categorie: "toutes" })}
            >
              Toutes
            </LigneFiltre>
          </li>
          {CATEGORIES.map((categorie) => (
            <li key={categorie}>
              <LigneFiltre
                actif={filtres.categorie === categorie}
                compte={comptesCategories[categorie]}
                onClick={() =>
                  modifier({
                    categorie:
                      filtres.categorie === categorie ? "toutes" : categorie,
                  })
                }
              >
                {LIBELLE_CATEGORIE[categorie]}
              </LigneFiltre>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-6 border-t border-filet pt-5">
        <h3 className="text-sm font-semibold text-texte">Affiner</h3>
        <div className="mt-2 space-y-1">
          <CaseFiltre
            coche={filtres.termineBientot}
            onChanger={(coche) => modifier({ termineBientot: coche })}
          >
            Se termine bientôt
          </CaseFiltre>
          <CaseFiltre
            coche={filtres.petitPrix}
            onChanger={(coche) => modifier({ petitPrix: coche })}
          >
            Moins de {formaterFrancs(SEUIL_PETIT_PRIX)}
          </CaseFiltre>
        </div>
      </section>

      <section className="mt-6 border-t border-filet pt-5">
        <h3 className="text-sm font-semibold text-texte">Trier par</h3>
        <ul className="mt-2 space-y-0.5">
          {ORDRE_TRI.map((tri) => (
              <li key={tri}>
                <LigneFiltre
                  actif={filtres.tri === tri}
                  onClick={() => modifier({ tri })}
                >
                  {LIBELLE_TRI[tri]}
                </LigneFiltre>
            </li>
          ))}
        </ul>
      </section>
    </aside>
  );
}

function LigneFiltre({
  actif,
  compte,
  onClick,
  children,
}: {
  actif: boolean;
  compte?: number;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={actif}
      onClick={onClick}
      className={`flex min-h-10 w-full items-center justify-between gap-2 rounded-[10px] px-2 text-left text-sm transition-colors ${
        actif
          ? "bg-primaire-fond font-semibold text-primaire-texte-sur-fond"
          : "text-texte hover:bg-surface-douce"
      }`}
    >
      <span>{children}</span>
      {compte === undefined ? null : (
        <span className="text-texte-secondaire">{compte}</span>
      )}
    </button>
  );
}

function CaseFiltre({
  coche,
  onChanger,
  children,
}: {
  coche: boolean;
  onChanger: (coche: boolean) => void;
  children: React.ReactNode;
}) {
  return (
    <label className="flex min-h-10 cursor-pointer items-center gap-2.5 rounded-[10px] px-2 text-sm text-texte hover:bg-surface-douce">
      <input
        type="checkbox"
        checked={coche}
        onChange={(evenement) => onChanger(evenement.target.checked)}
        className="size-4 shrink-0 accent-[#CC4A00]"
      />
      {children}
    </label>
  );
}
