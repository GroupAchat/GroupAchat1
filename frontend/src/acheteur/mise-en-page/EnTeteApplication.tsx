import { IconeDemander, IconeRecherche } from "../../ui/Icones";
import Logo from "../../ui/Logo";
import BoutonCloche from "./BoutonCloche";

/**
 * L'en-tete des ecrans d'accueil, d'apres la maquette fournie : le logo a
 * gauche, la cloche de notifications a droite, puis le champ de recherche et
 * le bouton « Demander ».
 *
 * Le bouton « Demander » a cote de la recherche est l'idee de l'ecran 1,
 * point 2 : un echec de recherche se transforme en demande de produit
 * (ecran 11) au lieu de laisser l'utilisateur repartir les mains vides.
 *
 * La recherche en clair plutot qu'une loupe seule est un choix assume de la
 * spec : sur un fil vertical, rien ne dit qu'on peut chercher autre chose que
 * ce qui defile, et une loupe se remarque moins qu'un champ.
 */
export default function EnTeteApplication({
  recherche,
  onRecherche,
  onActiverRecherche,
  onDemander,
  surMedia = false,
  notifications = 0,
  onNotifications,
}: {
  recherche?: string;
  onRecherche?: (valeur: string) => void;
  /** Sur le fil, toucher le champ bascule vers la vue liste (ecran 2). */
  onActiverRecherche?: () => void;
  /** Vers l'ecran 11. Un echec de recherche n'est jamais un cul-de-sac. */
  onDemander?: () => void;
  /** Sur le fil, l'en-tete est pose sur le media : fond blanc a 92 %. */
  surMedia?: boolean;
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
}) {
  return (
    <header
      className={`${
        surMedia ? "absolute inset-x-0 top-0 z-10" : "sticky top-0 z-10"
      } bg-white`}
    >
      {/*
       * ⚠️ **Fond blanc plein, et non plus `white/85` + flou.**
       *
       * Sur le fil, cet en-tete est pose **sur une photo plein cadre**. A
       * 85 %, la photo transparaissait au travers : le bandeau prenait la
       * teinte de l'image — gris sur une basket sombre, jaunatre sur un sac de
       * riz — et le logo changeait de fond a chaque glissement. Un en-tete qui
       * change de couleur avec le produit n'est plus un repere.
       *
       * Le flou coutait en plus : `backdrop-blur-xl` sur une surface qui
       * couvre toute la largeur fait travailler le compositeur a chaque image
       * du defilement, sur des telephones d'entree de gamme (§5).
       */}
      <div className="flex h-14 items-center justify-between px-4">
        <Logo variante="couleur" disposition="cote" hauteur={28} />

        {/* Le meme bouton que sur bureau : le compteur et son contraste
            n'existent qu'a un seul endroit, donc ils ne peuvent pas diverger.
            `surMedia` rend le fond opaque quand l'en-tete est pose sur le fil. */}
        <BoutonCloche
          notifications={notifications}
          onClick={onNotifications}
          surMedia={surMedia}
          taille="compacte"
        />
      </div>

      <div className="flex items-center gap-2 px-4 pb-3">
        <label htmlFor="recherche-entete" className="sr-only">
          Rechercher un produit
        </label>
        <div className="flex h-12 flex-1 items-center gap-2 rounded-[10px] bg-surface-douce px-3 focus-within:bg-white focus-within:ring-2 focus-within:ring-primaire">
          <IconeRecherche
            taille={18}
            className="shrink-0 text-texte-secondaire"
          />
          <input
            id="recherche-entete"
            type="search"
            value={recherche ?? ""}
            readOnly={onRecherche === undefined}
            onFocus={onActiverRecherche}
            onChange={(evenement) => onRecherche?.(evenement.target.value)}
            placeholder="Rechercher un produit…"
            className="h-full w-full bg-transparent text-sm outline-none placeholder:text-texte-secondaire"
          />
        </div>

        <button
          type="button"
          onClick={onDemander}
          className="inline-flex h-12 shrink-0 items-center gap-1.5 rounded-[10px] bg-primaire px-4 font-semibold text-white active:bg-primaire-presse"
        >
          <IconeDemander taille={18} />
          Demander
        </button>
      </div>
    </header>
  );
}
