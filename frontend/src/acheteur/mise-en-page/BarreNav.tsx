import {
  IconeAccueil,
  IconeCommandes,
  IconeGroupage,
  IconeProfil,
} from "../../ui/Icones";

/**
 * `BarreNav` — SPEC_ECRANS_FIGMA.md §2.2 pour la forme, ecran 1 (« Les onglets,
 * a definir maintenant ») pour les libelles, et la maquette fournie pour les
 * icones.
 *
 * ⚠️ La spec se contredit sur les onglets : le §2.2 annonce
 * « Fil · Rechercher · Demander · Mes commandes », l'ecran 1 tranche
 * « Accueil · Groupage · Commandes · Profil ». C'est ce dernier qui est
 * applique — il est posterieur, il associe chaque onglet a un numero d'ecran,
 * et il place la vue liste sous l'onglet **Groupage**. A corriger dans §2.2.
 *
 * Hauteur 72, fond blanc, filet de 1 px en haut et rien d'autre — pas d'ombre.
 * Onglet actif en `primaire`, inactif en `texte-secondaire`.
 *
 * **Identique, connecte ou non** : aucun onglet grise, aucun cadenas (§1.5).
 * Un onglet protege n'affiche pas un mur mais un `EtatVide`.
 *
 * La pastille de l'onglet Commandes est en `marque` : c'est une pastille
 * pleine, le seul usage de l'orange vif autorise avec ce contraste (§1.2).
 */
export type OngletAcheteur = "accueil" | "groupage" | "commandes" | "profil";

const ONGLETS: {
  cle: OngletAcheteur;
  libelle: string;
  Icone: (p: { taille?: number }) => React.ReactElement;
}[] = [
  { cle: "accueil", libelle: "Accueil", Icone: IconeAccueil },
  { cle: "groupage", libelle: "Groupage", Icone: IconeGroupage },
  { cle: "commandes", libelle: "Commandes", Icone: IconeCommandes },
  { cle: "profil", libelle: "Profil", Icone: IconeProfil },
];

export default function BarreNav({
  actif,
  commandesEnCours = 0,
  onChanger,
}: {
  actif: OngletAcheteur;
  /** Nombre de commandes en cours : alimente la pastille de l'onglet. */
  commandesEnCours?: number;
  onChanger?: (onglet: OngletAcheteur) => void;
}) {
  return (
    <nav
      aria-label="Navigation principale"
      /* ⚠️ **Fond blanc plein.** A `white/85`, la photo du fil remontait au
         travers et la barre virait au gris : les quatre libelles se
         posaient alors sur une couleur qui changeait a chaque groupage.
         Une barre de navigation est un repere fixe — elle ne doit rien
         emprunter a ce qu'il y a derriere elle. */
      className="fixed inset-x-0 bottom-0 z-20 mx-auto h-18 max-w-[430px] border-t border-filet bg-white"
    >
      <ul className="flex h-full">
        {ONGLETS.map(({ cle, libelle, Icone }) => {
          const estActif = cle === actif;
          const pastille = cle === "commandes" && commandesEnCours > 0;
          return (
            <li key={cle} className="flex-1">
              <button
                type="button"
                aria-current={estActif ? "page" : undefined}
                onClick={() => onChanger?.(cle)}
                className={`flex size-full flex-col items-center justify-center gap-1 ${
                  estActif ? "text-primaire" : "text-texte-secondaire"
                }`}
              >
                <span className="relative">
                  <Icone taille={24} />
                  {pastille ? (
                    <span
                      className="absolute -top-0.5 -right-1 size-2.5 rounded-full bg-marque"
                      aria-hidden="true"
                    />
                  ) : null}
                </span>
                <span className="text-xs font-medium">
                  {libelle}
                  {pastille ? (
                    <span className="sr-only">
                      , {commandesEnCours} commande
                      {commandesEnCours > 1 ? "s" : ""} en cours
                    </span>
                  ) : null}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
