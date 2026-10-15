import { useEffect, useRef } from "react";
import {
  IconeAccueil,
  IconeCommandes,
  IconeDemander,
  IconeFermer,
  IconeGroupage,
  IconeProfil,
} from "../../ui/Icones";

/**
 * Le menu principal du cote acheteur, sur grand ecran.
 *
 * ## ⚠️ Il ne range pas une navigation : il en cree une
 *
 * C'est le point a comprendre avant de juger ce menu. Le §2 reproche a juste
 * titre les menus qui cachent ce qui tenait dans la page — « jamais derriere un
 * bouton, ce serait un menu cache ». Ici, **il n'y avait rien a cacher** :
 *
 * | | Telephone | Bureau *(avant)* |
 * |---|---|---|
 * | Accueil, Groupages, Commandes, Profil | `BarreNav` en bas | **rien** |
 * | Mes demandes | par le profil | **rien** |
 *
 * `BarreNav` est montee sous `!estBureau` : au-dela de 768 px, elle
 * disparaissait et **aucune autre navigation ne la remplacait**. L'en-tete de
 * bureau ne portait que le logo, la recherche, « Demander » et la cloche. Un
 * acheteur sur ordinateur n'avait donc **aucun chemin** vers ses commandes,
 * ses demandes ou son profil — il fallait retrecir la fenetre pour les
 * atteindre.
 *
 * Un menu qui ouvre cinq ecrans jusque-la inaccessibles n'est pas un menu
 * cache. Le jour ou ces entrees existeront aussi en clair dans la barre, la
 * critique du §2 redeviendra valable et il faudra rediscuter celui-ci.
 *
 * ## ⚠️ Aucune entree n'est masquee quand on n'est pas connecte
 *
 * « Mes commandes » et « Mes demandes » restent visibles et cliquables sans
 * compte. C'est le §1.5 : pas de mur d'authentification. Elles menent a l'etat
 * vide pedagogique de ces ecrans, qui explique et propose de se connecter —
 * ce qui est une reponse. Les retirer du menu laisserait croire qu'elles
 * n'existent pas, et c'est le seul endroit ou l'on apprend qu'elles existent.
 */

/** Les cinq ecrans que le menu ouvre. */
export type DestinationMenu =
  | "accueil"
  | "catalogue"
  | "mes-commandes"
  | "mes-demandes"
  | "profil";

const ENTREES: {
  cle: DestinationMenu;
  libelle: string;
  Icone: (p: { taille?: number; className?: string }) => React.ReactElement;
}[] = [
  { cle: "accueil", libelle: "Accueil", Icone: IconeAccueil },
  { cle: "catalogue", libelle: "Tous les groupages", Icone: IconeGroupage },
  { cle: "mes-commandes", libelle: "Mes commandes", Icone: IconeCommandes },
  { cle: "mes-demandes", libelle: "Mes demandes", Icone: IconeDemander },
  { cle: "profil", libelle: "Mon profil", Icone: IconeProfil },
];

export default function MenuPrincipal({
  ouvert,
  onFermer,
  actif,
  connecte,
  nom,
  telephone,
  onAller,
  onSeConnecter,
  onSeDeconnecter,
}: {
  ouvert: boolean;
  onFermer: () => void;
  /** L'ecran courant, pour marquer l'entree correspondante. */
  actif?: DestinationMenu;
  connecte: boolean;
  nom?: string;
  telephone?: string;
  onAller: (destination: DestinationMenu) => void;
  onSeConnecter: () => void;
  onSeDeconnecter: () => void;
}) {
  const panneau = useRef<HTMLDivElement>(null);

  /**
   * Echap ferme, et le defilement de la page est bloque pendant l'ouverture.
   *
   * Sans le blocage, la molette fait defiler la page **derriere** le tiroir :
   * on le referme et on a perdu sa place dans le catalogue. C'est la meme
   * mecanique que `TiroirFiltres`, et pour la meme raison.
   */
  useEffect(() => {
    if (!ouvert) {
      return;
    }
    const auClavier = (evenement: KeyboardEvent) => {
      if (evenement.key === "Escape") {
        onFermer();
      }
    };
    const defilementInitial = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", auClavier);
    panneau.current?.focus();
    return () => {
      document.body.style.overflow = defilementInitial;
      window.removeEventListener("keydown", auClavier);
    };
  }, [ouvert, onFermer]);

  if (!ouvert) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40">
      {/* Le voile ferme. La page reste visible derriere : on sait d'ou on
          vient, et refermer ne ressemble pas a un retour en arriere. */}
      <button
        type="button"
        aria-label="Fermer le menu"
        onClick={onFermer}
        className="absolute inset-0 bg-black/50"
      />

      <div
        ref={panneau}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label="Menu"
        /* Il vient **de la gauche**, du cote du bouton qui l'ouvre. Un tiroir
           qui surgit a l'oppose de ce qu'on a touche oblige a chercher des
           yeux ou il est apparu. */
        className="absolute inset-y-0 left-0 flex w-80 max-w-[85vw] flex-col bg-white shadow-[8px_0_32px_rgba(29,25,22,0.18)]"
      >
        <header className="flex shrink-0 items-center justify-between border-b border-filet px-4 py-3">
          <h2 className="text-lg font-semibold text-texte">Menu</h2>
          <button
            type="button"
            onClick={onFermer}
            aria-label="Fermer le menu"
            className="flex size-10 items-center justify-center rounded-full text-texte-secondaire hover:bg-surface-douce"
          >
            <IconeFermer taille={18} />
          </button>
        </header>

        <nav className="min-h-0 flex-1 overflow-y-auto p-3">
          <ul className="space-y-1">
            {ENTREES.map(({ cle, libelle, Icone }) => {
              const courant = actif === cle;
              return (
                <li key={cle}>
                  <button
                    type="button"
                    onClick={() => {
                      onAller(cle);
                      onFermer();
                    }}
                    aria-current={courant ? "page" : undefined}
                    /* ⚠️ L'entree courante se marque par un **aplat**, pas par
                       la seule couleur du texte : `primaire-texte-sur-fond` sur
                       `primaire-fond` tient 4,87:1, et c'est le fond qui rend
                       l'etat lisible d'un coup d'oeil dans une liste. */
                    className={`flex min-h-12 w-full items-center gap-3 rounded-[10px] px-3 text-left font-medium ${
                      courant
                        ? "bg-primaire-fond text-primaire-texte-sur-fond"
                        : "text-texte hover:bg-surface-douce"
                    }`}
                  >
                    <Icone taille={22} className="shrink-0" />
                    {libelle}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/*
         * Le compte, en bas : c'est l'endroit ou on le cherche, et c'est le
         * seul endroit du bureau ou l'on peut se deconnecter.
         *
         * ⚠️ **« Se connecter » n'est pas un mur** (§1.5) : les cinq entrees
         * au-dessus restent ouvertes sans compte. C'est une proposition, pas
         * un peage.
         */}
        <div className="shrink-0 border-t border-filet p-3">
          {connecte ? (
            <>
              <p className="px-3 text-sm text-texte-secondaire">Connecté</p>
              <p className="truncate px-3 font-medium text-texte">
                {nom || telephone}
              </p>
              <button
                type="button"
                onClick={() => {
                  onSeDeconnecter();
                  onFermer();
                }}
                className="mt-2 flex min-h-12 w-full items-center rounded-[10px] px-3 text-left font-medium text-primaire hover:bg-surface-douce"
              >
                Se déconnecter
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => {
                onSeConnecter();
                onFermer();
              }}
              className="flex min-h-12 w-full items-center rounded-[10px] px-3 text-left font-medium text-primaire hover:bg-surface-douce"
            >
              J&apos;ai déjà un compte — me connecter
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
