import { IconeDemander, IconeMenu, IconeRecherche } from "../../ui/Icones";
import Logo from "../../ui/Logo";
import BoutonCloche from "./BoutonCloche";

/**
 * L'en-tete des grands ecrans — quatre elements, et rien d'autre :
 * **logo, barre de recherche, bouton « Demander », bouton de notifications.**
 *
 * La recherche occupe le centre et toute la largeur disponible. C'est l'action
 * principale d'un catalogue, et la reduire a une loupe la cache : sur une page
 * longue, rien ne dit a l'utilisateur qu'il peut chercher autre chose que ce
 * qu'il voit (meme raisonnement qu'a l'ecran 1, point 2).
 *
 * Le bouton « Demander » est colle a la recherche, et c'est voulu : un echec
 * de recherche se transforme en demande de produit (ecran 11) au lieu de
 * laisser quelqu'un repartir les mains vides.
 *
 * ⚠️ **« Mes commandes » et « Profil » ne sont plus ici.** Ils y etaient, et
 * ils ont ete retires pour tenir la liste de quatre elements. Sur un site
 * marchand, le suivi de commande est une des raisons principales de revenir —
 * pour l'instant il n'est atteignable que par le pied de page. A rouvrir.
 *
 * Le chrome reste celui de l'acheteur : orange (§1.2). Rien de bleu ici.
 */
export default function EnTeteBureau({
  recherche,
  onRecherche,
  onDemander,
  notifications = 0,
  onNotifications,
  onMenu,
  menuOuvert = false,
  onAccueil,
}: {
  recherche: string;
  onRecherche: (valeur: string) => void;
  /** Vers l'ecran 11. Un echec de recherche n'est jamais un cul-de-sac. */
  /**
   * ⚠️ **Absent quand on est déjà sur l'écran de demande.**
   *
   * Le bouton ne se dessine alors pas, et c'est la même règle que celle de
   * `NavigationContexte` pour le pied de page : *une entrée non branchée ne se
   * dessine pas*. Sur l'écran du formulaire, ce bouton menait à la page
   * courante — avec exactement le poids du bouton d'envoi, même orange, même
   * hauteur. Deux actions identiques dont une ne faisait rien.
   */
  onDemander?: () => void;
  /**
   * Le nombre de notifications non lues.
   *
   * ⚠️ **Il vient du serveur.** C'etait la constante `1` ecrite dans le
   * routeur : la pastille etait donc allumee en permanence, pour une
   * notification qui n'existait pas. Une pastille qui ment est pire qu'une
   * cloche absente, parce qu'on finit par ne plus la regarder.
   */
  notifications?: number;
  /** Ouvre le panneau de notifications. */
  onNotifications?: () => void;
  /** Ouvre le menu principal — la seule navigation du cote bureau. */
  onMenu?: () => void;
  /** Pour `aria-expanded` : le bouton doit dire si son panneau est ouvert. */
  menuOuvert?: boolean;
  onAccueil: () => void;
}) {
  /*
   * Le verre de l'en-tete : translucide, le contenu passe dessous au lieu de
   * disparaitre derriere un bandeau plein.
   *
   * ⚠️ **Les 85 pour cent sont calcules pour le pire cas**, qui n'est pas
   * celui qu'on imagine : une photo noire qui defile dessous **et** un appareil
   * qui ne gere pas `backdrop-blur`. Sur l'Android d'entree de gamme du §5, ce
   * cas est la regle, pas l'exception. Le fond reel vaut alors `#D9D9D9`, ou
   * `texte` tient **12,37:1** et `texte-secondaire` **5,26:1**.
   *
   * Le flou est un bonus, jamais ce sur quoi repose la lisibilite : a 80 pour
   * cent, le texte secondaire tomberait a 4,62:1, trop juste.
   *
   * ⚠️ **Ce commentaire est hors du JSX, et il doit y rester.** Place entre
   * `return (` et `<header>`, il devenait un second noeud racine : le fichier
   * ne compilait plus, sur un « ')' expected » qui ne designe pas la cause.
   */
  return (
    <header className="sticky top-0 z-20 border-b border-bordure bg-white/85 backdrop-blur-xl">
      {/* Pleine largeur, comme le reste de la page : un en-tete arrete a
          1 280 px au-dessus d'un contenu qui va d'un bord a l'autre laisse le
          logo flotter au milieu de nulle part sur un grand ecran. */}
      {/* ⚠️ `largeur-page` : le meme plafond et la meme gouttiere que
          les ecrans. Sans lui, le logo se collait au bord gauche de
          l'ecran pendant que le contenu commencait 320 px plus loin. */}
      <div className="largeur-page flex h-20 items-center gap-4 lg:gap-8">
        {/* ⚠️ **A gauche, avant le logo.** C'est la que se cherche un menu,
            et le tiroir s'ouvre du meme cote — un panneau qui surgit a
            l'oppose de ce qu'on a touche oblige a chercher des yeux ou il est
            apparu.

            Il porte un **libelle visible** et pas seulement l'icone : trois
            barres seules sont comprises par qui a l'habitude du web, et par
            personne d'autre. Le public vise ici n'est pas celui-la. */}
        <button
          type="button"
          onClick={onMenu}
          aria-expanded={menuOuvert}
          className="flex h-12 shrink-0 items-center gap-2 rounded-[10px] border border-bordure-champ px-3 font-medium text-texte hover:bg-surface-douce"
        >
          <IconeMenu taille={22} />
          Menu
        </button>

        <button
          type="button"
          onClick={onAccueil}
          aria-label="Group Achat, accueil"
          className="shrink-0"
        >
          <Logo variante="couleur" disposition="cote" hauteur={32} />
        </button>

        {/*
         * ⚠️ **Trois zones : logo a gauche, recherche au centre, actions a
         * droite.** C'est la disposition de toutes les places de marche, et
         * elle n'y est pas par habitude — chaque bord porte une fonction
         * differente, et l'oeil sait ou revenir.
         *
         * Ce qu'il y avait avant etait casse de deux facons :
         *
         * 1. **« Demander » etait enferme dans le bloc de recherche**, lui-meme
         *    plafonne a 640 px. Le champ ne recevait donc que ce que le bouton
         *    lui laissait — environ 460 px — alors que le plafond etait cense
         *    etre pour lui seul ;
         * 2. **tout etait tasse a gauche.** Les trois elements tenaient dans
         *    les 640 premiers pixels et laissaient pres de 700 px de vide a
         *    droite sur un ecran de 1 920. Une barre d'en-tete dont tout le
         *    contenu occupe le premier tiers n'a pas l'air centree, elle a
         *    l'air tombee.
         *
         * `mx-auto` sur un element en `flex-1` plafonne : il grandit jusqu'a
         * 640 px, puis les marges automatiques absorbent le reste **a parts
         * egales**. La recherche est donc centree entre le logo et les
         * actions, et le vide devient une respiration voulue au lieu d'un
         * reste.
         */}
        <div className="mx-auto flex h-12 max-w-[40rem] flex-1 items-center gap-2 rounded-[10px] border border-bordure-champ bg-white px-3 focus-within:border-2 focus-within:border-primaire">
          <label htmlFor="recherche-bureau" className="sr-only">
            Rechercher un produit
          </label>
          <IconeRecherche
            taille={20}
            className="shrink-0 text-texte-secondaire"
          />
          <input
            id="recherche-bureau"
            type="search"
            value={recherche}
            onChange={(evenement) => onRecherche(evenement.target.value)}
            placeholder="Rechercher un produit…"
            className="h-full w-full bg-transparent outline-none placeholder:text-texte-secondaire"
          />
        </div>

        {/* Les actions, groupees et calees a droite.

            ⚠️ **Ce commentaire disait : « ce sont les deux seuls gestes
            permanents de l'en-tete ».** Ils ne sont plus permanents tous les
            deux : « Demander » s'efface sur l'ecran de demande. La cloche,
            elle, reste partout. */}
        <div className="flex shrink-0 items-center gap-2 lg:gap-3">
          {/* ⚠️ **Rien sans destination**, la meme regle que le pied de page.
              La rendre facultative ne suffisait pas : le bouton se dessinait
              quand meme, et `onClick={undefined}` est du TypeScript valide —
              le typage ne pouvait donc pas signaler le bouton mort. */}
          {onDemander ? (
            <button
              type="button"
              onClick={onDemander}
              className="inline-flex h-12 shrink-0 items-center gap-1.5 rounded-[10px] bg-primaire px-5 font-semibold text-white active:bg-primaire-presse"
            >
              <IconeDemander taille={18} />
              Demander
            </button>
          ) : null}

          <BoutonCloche
            notifications={notifications}
            onClick={onNotifications}
          />
        </div>
      </div>
    </header>
  );
}
