import {
  IconeAccueil,
  IconeCarton,
  IconePortefeuille,
  IconeRetour,
  IconeStatistiques,
} from "../../ui/Icones";

/**
 * Le chrome du cote groupeur — SPEC_ECRANS_FIGMA.md §1.2, ecran 13.
 *
 * ## Bleu dominant, orange assume
 *
 * Le bleu reste la couleur du cote groupeur : en-tete `confiance` a texte
 * blanc (10,36:1), cartes de chiffres bleues, fond blanc partout ailleurs
 * (§1.0). **L'orange n'est plus cantonne a l'alerte** : il marque desormais
 * l'onglet actif, souligne l'en-tete et porte la creation de groupage.
 *
 * ⚠️ **Les deux chromes ne sont pas inverses pour autant** : on sait toujours
 * d'un coup d'oeil de quel cote on se trouve, parce que c'est le bleu qui
 * porte les aplats et l'orange qui ponctue. Inverser les deux rendrait
 * l'espace groupeur indiscernable de la boutique.
 *
 * ## Les contrastes, calcules et non estimes
 *
 * | Usage | Rapport | Verdict |
 * |---|---|---|
 * | `primaire` #CC4A00 sur blanc | 4,62:1 | texte autorise |
 * | `marque` #FF6A00 sur `confiance` | 3,61:1 | **aplats pleins seulement** |
 * | `marque` avec texte blanc | 2,87:1 | **interdit partout** |
 *
 * D'ou le detail de ce fichier : le libelle de l'onglet actif est en
 * `primaire` sur blanc, jamais en `marque` ; et le souligne orange de
 * l'en-tete est une bande pleine, pas du texte.
 *
 * ## Deux navigations, une par largeur
 *
 * Sous 768 px, la barre du bas — un composant de pouce. Au-dela, une colonne
 * laterale : une barre d'onglets collee en bas d'un ecran de 1 400 px est un
 * reflexe mobile applique au mauvais appareil, et elle laisse le contenu
 * flotter dans une colonne etroite au milieu du vide.
 */
export type OngletGroupeur =
  | "tableau-de-bord"
  | "campagnes"
  | "statistiques"
  | "portefeuille";

const ONGLETS: {
  cle: OngletGroupeur;
  libelle: string;
  Icone: (p: { taille?: number }) => React.ReactElement;
}[] = [
  { cle: "tableau-de-bord", libelle: "Tableau de bord", Icone: IconeAccueil },
  { cle: "campagnes", libelle: "Mes campagnes", Icone: IconeCarton },
  { cle: "statistiques", libelle: "Statistiques", Icone: IconeStatistiques },
  { cle: "portefeuille", libelle: "Portefeuille", Icone: IconePortefeuille },
];

/**
 * La barre de navigation groupeur, **version telephone**. Quatre onglets.
 *
 * C'est l'arrivee de l'ecran 21 qui fixe le quatrieme : sans lui, les
 * statistiques resteraient un ecran qu'on ne retrouve pas.
 *
 * L'onglet actif est en `primaire` (4,62:1 sur blanc) et porte un trait
 * orange au-dessus : **la couleur seule ne porte jamais l'information** —
 * `aria-current` la dit aux lecteurs d'ecran, et le trait la rend visible
 * meme en noir et blanc.
 */
export function BarreNavGroupeur({
  actif,
  onChanger,
}: {
  actif: OngletGroupeur;
  onChanger: (onglet: OngletGroupeur) => void;
}) {
  return (
    <nav
      aria-label="Navigation groupeur"
      className="fixed inset-x-0 bottom-0 z-20 mx-auto h-18 max-w-[430px] border-t border-filet bg-white md:hidden"
    >
      <ul className="flex h-full">
        {ONGLETS.map(({ cle, libelle, Icone }) => {
          const estActif = cle === actif;
          return (
            <li key={cle} className="relative flex-1">
              {estActif ? (
                <span
                  aria-hidden="true"
                  className="absolute inset-x-3 top-0 h-[3px] rounded-full bg-marque"
                />
              ) : null}
              <button
                type="button"
                aria-current={estActif ? "page" : undefined}
                onClick={() => onChanger(cle)}
                className={`flex size-full flex-col items-center justify-center gap-1 px-1 ${
                  estActif
                    ? "text-primaire font-semibold"
                    : "text-texte-secondaire"
                }`}
              >
                <Icone taille={24} />
                <span className="text-center text-xs leading-tight font-medium">
                  {libelle}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/**
 * La navigation **sur grand ecran** : une colonne laterale, bleue.
 *
 * ⚠️ **Ce n'est pas la barre du bas deplacee sur le cote.** Elle porte le nom
 * du groupeur en tete, parce qu'un espace professionnel doit dire a qui il
 * appartient — on y travaille longtemps, souvent sur une machine partagee.
 *
 * L'onglet actif est un aplat blanc a texte `primaire` : sur le bleu, un
 * libelle orange tomberait a 3,61:1, ce qui ne passe pas pour du texte.
 */
export function RailGroupeur({
  actif,
  onChanger,
  pseudonyme,
}: {
  actif: OngletGroupeur;
  onChanger: (onglet: OngletGroupeur) => void;
  pseudonyme?: string;
}) {
  return (
    <nav
      aria-label="Navigation groupeur"
      className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col bg-confiance px-3 py-5 md:flex"
    >
      <div className="px-3 pb-5">
        <p className="text-sm text-white/70">Espace groupeur</p>
        <p className="truncate text-lg font-semibold text-white">
          {pseudonyme || "Mon espace"}
        </p>
        {/* Le souligne orange : un aplat plein, jamais du texte (3,61:1). */}
        <span
          aria-hidden="true"
          className="mt-3 block h-1 w-12 rounded-full bg-marque"
        />
      </div>

      <ul className="flex flex-col gap-1">
        {ONGLETS.map(({ cle, libelle, Icone }) => {
          const estActif = cle === actif;
          return (
            <li key={cle}>
              <button
                type="button"
                aria-current={estActif ? "page" : undefined}
                onClick={() => onChanger(cle)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium ${
                  estActif
                    ? "bg-white text-primaire"
                    : "text-white/80 hover:bg-white/10"
                }`}
              >
                <Icone taille={20} />
                {libelle}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/**
 * L'en-tete bleu des ecrans groupeur. Fond `confiance`, texte blanc.
 *
 * `onRetour` est absent sur les ecrans de premier niveau, et volontairement
 * absent aussi sur l'ecran 16 : **on ne quitte pas l'ecran de decision sans
 * decider ou sans le refermer explicitement**.
 */
export function EnTeteGroupeur({
  titre,
  sousTitre,
  onRetour,
  action,
}: {
  titre: string;
  sousTitre?: string;
  onRetour?: () => void;
  action?: React.ReactNode;
}) {
  return (
    /* ⚠️ Le liseré orange est une **bande pleine**, pas du texte : sur le bleu,
       `marque` tombe à 3,61:1, ce qui n'autorise que les aplats. C'est lui qui
       installe l'orange dans le chrome groupeur sans inverser les deux côtés
       (§1.2). */
    <header className="border-b-4 border-marque bg-confiance px-4 pt-5 pb-5 text-white md:px-8">
      <div className="flex items-start gap-2">
        {onRetour ? (
          <button
            type="button"
            onClick={onRetour}
            aria-label="Retour"
            className="-ml-2 flex size-11 shrink-0 items-center justify-center text-white"
          >
            <IconeRetour />
          </button>
        ) : null}

        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-semibold">{titre}</h1>
          {sousTitre ? (
            <p className="mt-0.5 text-sm text-white/85">{sousTitre}</p>
          ) : null}
        </div>

        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
    </header>
  );
}
