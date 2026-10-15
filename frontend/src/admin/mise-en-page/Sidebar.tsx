import type { ReactNode } from "react";
import {
  IconeAlerte,
  IconeBouclier,
  IconeCarton,
  IconeGroupage,
  IconeStatistiques,
} from "../../ui/Icones";

/**
 * La coquille de l'administration : barre laterale fixe, contenu a droite.
 *
 * ## Pourquoi une barre laterale ici, et une barre du bas ailleurs
 *
 * Les deux publics ne travaillent pas dans les memes conditions. L'acheteur et
 * le groupeur sont sur un telephone, debout, une main occupee : leur
 * navigation est en bas, a portee du pouce. L'administrateur est **assis
 * devant un ecran de 1 280 px**, avec un clavier et une souris — c'est le seul
 * ecran du produit destine a un ordinateur (§1.2).
 *
 * Une barre laterale lui donne ce qu'une barre du bas ne peut pas :
 *
 * - **toutes les destinations visibles en permanence**, avec leurs compteurs.
 *   Il n'a pas a ouvrir un ecran pour savoir s'il a du travail dessus ;
 * - **de la place pour un libelle entier.** « Virements a faire » ne tient pas
 *   sous une icone de barre du bas ;
 * - **l'espace horizontal preserve** pour les tableaux, qui sont ce que cet
 *   outil affiche le plus.
 *
 * ## ⚠️ Chrome neutre, et les compteurs ne le sont pas
 *
 * Le §1.2 impose a l'administration un chrome **ni orange ni bleu** : les deux
 * chromes de marque appartiennent aux deux publics, et cette neutralite evite
 * de confondre une capture d'ecran interne avec le produit.
 *
 * La couleur reste donc **reservee aux donnees** : une pastille rouge sur une
 * file dit qu'il y a du travail urgent dessus, elle ne decore rien. C'est la
 * meme regle que pour les graphiques — la couleur encode, elle n'habille pas.
 */

export type EcranAdmin =
  | "tableau-de-bord"
  | "retraits"
  | "groupages"
  | "dossiers";

interface Entree {
  cle: EcranAdmin;
  libelle: string;
  Icone: (proprietes: { taille?: number; className?: string }) => ReactNode;
}

const ENTREES: readonly Entree[] = [
  { cle: "tableau-de-bord", libelle: "Tableau de bord", Icone: IconeStatistiques },
  { cle: "retraits", libelle: "Retraits à exécuter", Icone: IconeAlerte },
  { cle: "groupages", libelle: "Groupages", Icone: IconeCarton },
  { cle: "dossiers", libelle: "Dossiers KYC", Icone: IconeBouclier },
];

export default function Sidebar({
  actif,
  compteurs,
  onNaviguer,
  children,
}: {
  actif: EcranAdmin;
  /**
   * Ce qui attend sur chaque ecran.
   *
   * ⚠️ **Un compteur a zero ne s'affiche pas**, mais l'entree reste. La faire
   * disparaitre deplacerait les autres d'un jour a l'autre, et on ne
   * retrouverait plus rien — c'est le meme raisonnement que pour les files de
   * l'ecran A1.
   */
  compteurs?: Partial<Record<EcranAdmin, { nombre: number; urgent?: boolean }>>;
  onNaviguer: (ecran: EcranAdmin) => void;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-dvh bg-surface-douce">
      <nav
        aria-label="Administration"
        className="flex w-60 shrink-0 flex-col border-r border-bordure bg-white"
      >
        <div className="flex items-center gap-2 border-b border-filet px-5 py-4">
          <IconeGroupage taille={22} className="text-texte" />
          <span className="font-semibold text-texte">Group Achat</span>
        </div>

        <ul className="flex-1 space-y-1 p-3">
          {ENTREES.map(({ cle, libelle, Icone }) => {
            const compteur = compteurs?.[cle];
            const estActif = cle === actif;
            return (
              <li key={cle}>
                <button
                  type="button"
                  onClick={() => onNaviguer(cle)}
                  aria-current={estActif ? "page" : undefined}
                  className={`flex w-full items-center gap-3 rounded-[10px] px-3 py-2.5 text-left text-sm transition-colors ${
                    estActif
                      ? "bg-texte font-semibold text-white"
                      : "text-texte hover:bg-surface-douce"
                  }`}
                >
                  <Icone taille={18} className="shrink-0" />
                  <span className="min-w-0 flex-1 truncate">{libelle}</span>

                  {compteur && compteur.nombre > 0 ? (
                    <span
                      className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${
                        compteur.urgent
                          ? "bg-danger text-white"
                          : estActif
                            ? "bg-white/20 text-white"
                            : "bg-surface-douce text-texte-secondaire"
                      }`}
                    >
                      {compteur.nombre}
                    </span>
                  ) : null}
                </button>
              </li>
            );
          })}
        </ul>

        {/* ⚠️ Dit franchement ce que le jeton ne protege pas. Quelqu'un lira
            cet ecran et en conclura que l'administration est securisee. */}
        <p className="border-t border-filet px-5 py-4 text-xs text-texte-secondaire">
          Jeton partagé — il n&apos;identifie personne. Les décisions portent le
          nom qu&apos;on veut bien y mettre.
        </p>
      </nav>

      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
