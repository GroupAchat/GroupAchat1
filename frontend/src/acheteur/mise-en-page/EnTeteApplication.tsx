import { useEffect, useRef, useState } from "react";
import { IconeFermer, IconeRecherche } from "../../ui/Icones";
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
 * ## ⚠️ La recherche est une **loupe**, et c'est un revirement
 *
 * Ce fichier portait l'argument inverse, et il est reproduit ici plutot que
 * supprime : *« La recherche en clair plutot qu'une loupe seule est un choix
 * assume de la spec : sur un fil vertical, rien ne dit qu'on peut chercher
 * autre chose que ce qui defile, et une loupe se remarque moins qu'un
 * champ. »* L'utilisateur a tranche dans l'autre sens.
 *
 * Ce que ca coute, franchement : la decouvrabilite. Quelqu'un qui ne pense pas
 * a chercher ne verra plus qu'on peut le faire. Ce que ca rend : une ligne
 * entiere de hauteur sur un ecran de 390 px, et un en-tete qui ne pese plus
 * autant que le contenu.
 *
 * **Le champ n'a pas disparu, il se deplie.** Il est le seul de l'application
 * — `RechercheEtFiltres` le dit : *« le champ de recherche est dans
 * l'en-tete »* — donc le replier sans le rendre atteignable aurait supprime la
 * recherche, pas son encombrement.
 */
export default function EnTeteApplication({
  recherche,
  onRecherche,
  onActiverRecherche,
  rechercheDepliee = false,
  surMedia = false,
  notifications = 0,
  onNotifications,
}: {
  recherche?: string;
  onRecherche?: (valeur: string) => void;
  /** Sur le fil, toucher le champ bascule vers la vue liste (ecran 2). */
  onActiverRecherche?: () => void;
  /**
   * Deplier le champ des le montage, au lieu de montrer la loupe.
   *
   * ⚠️ **Sans ca, arriver sur l'ecran de recherche replierait la recherche.**
   * Sur le fil, toucher la loupe fait changer d'ecran : le nouvel en-tete se
   * monte, et s'il demarrait replie il faudrait toucher une seconde fois la
   * loupe pour obtenir ce qu'on venait de demander.
   */
  rechercheDepliee?: boolean;
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
  /* Depliee d'emblee si l'ecran la demande, ou s'il y a deja une recherche en
     cours : replier un filtre actif le rendrait invisible sans l'annuler. */
  const [depliee, setDepliee] = useState(
    rechercheDepliee || (recherche ?? "") !== "",
  );
  const champ = useRef<HTMLInputElement | null>(null);

  /* ⚠️ `autoFocus` ne suffit pas : l'element n'est monte qu'au depliage, et
     React ne refait pas la mise au point sur un montage conditionnel de
     maniere fiable sur tous les navigateurs mobiles. On la pose nous-memes. */
  useEffect(() => {
    if (depliee) champ.current?.focus();
  }, [depliee]);

  const ouvrirLaRecherche = () => {
    setDepliee(true);
    /* Sur le fil, ceci fait basculer vers la vue liste (ecran 2) — qui
       remontera cet en-tete avec `rechercheDepliee`. */
    onActiverRecherche?.();
  };

  const fermerLaRecherche = () => {
    setDepliee(false);
    /* On efface en fermant : laisser un filtre actif derriere une loupe
       repliee donnerait un catalogue amputé sans que rien ne l'explique. */
    onRecherche?.("");
  };

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
      {/* ⚠️ **Tout tient sur une ligne, et le budget est serre.**

          A 390 px il reste **358 px** une fois les marges de 16 retirees. Les
          largeurs connues : logo **117** (158/35 x 26), loupe **40**, cloche
          **40**, et trois intervalles de 8. Restent donc **~145 px** pour
          « Demander ».

          Sa largeur reelle depend des metriques de la police et ne se calcule
          pas ici — c'est pourquoi le libelle **s'efface sous 380 px** plutot
          que de parier dessus : le bouton retombe alors a une icone seule, et
          la marge redevient confortable. Si le logo poussait hors du cadre sur
          un telephone donne, c'est ce seuil qu'il faut relever, pas la taille
          du logo. */}
      <div className="flex h-14 items-center justify-between gap-2 px-4">
        <Logo variante="couleur" disposition="cote" hauteur={26} />

        <div className="flex shrink-0 items-center gap-2">
          {/* La loupe, repliee. Meme diametre que la cloche : les deux se
              lisent comme une paire d'outils, pas comme deux objets. */}
          {depliee ? null : (
            <button
              type="button"
              onClick={ouvrirLaRecherche}
              aria-label="Rechercher un produit"
              aria-expanded={false}
              /* ⚠️ **Le meme format que la cloche** : meme diametre, meme
                 cercle, meme contour `bordure-champ` (3,38:1, le seuil de la
                 regle 1.4.11 pour la limite d'un controle). La loupe etait une
                 icone nue a cote d'un bouton cercle — deux objets la ou il
                 faut une paire. */
              className="flex size-10 shrink-0 items-center justify-center rounded-full border border-bordure-champ text-texte active:bg-surface-douce"
            >
              <IconeRecherche taille={20} />
            </button>
          )}

          {/* Le meme bouton que sur bureau : le compteur et son contraste
              n'existent qu'a un seul endroit, donc ils ne peuvent pas diverger.
              `surMedia` rend le fond opaque quand l'en-tete est pose sur le fil. */}
          <BoutonCloche
            notifications={notifications}
            onClick={onNotifications}
            surMedia={surMedia}
            taille="compacte"
          />

          {/* ⚠️ **« Demander » n'est plus ici : il est dans la barre du bas.**
              L'y garder aussi remettrait deux entrees identiques sur le meme
              ecran. La barre du bas est le meilleur des deux endroits : elle
              est permanente, visible sur tous les ecrans, et elle ne dispute
              pas la place au logo sur une ligne de 358 px.

              La propriete `onDemander` reste acceptee — l'en-tete est monte
              par le fil et par le catalogue, qui la passent encore — mais
              elle ne dessine plus rien. */}
        </div>
      </div>

      {/* La seconde ligne **n'existe que pendant la recherche**. C'est elle
          qu'on vient de rendre a l'ecran : elle occupait une ligne entiere en
          permanence, pour un geste qu'on ne fait pas a chaque visite. */}
      {depliee ? (
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
              ref={champ}
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
            onClick={fermerLaRecherche}
            aria-label="Fermer la recherche"
            className="flex size-10 shrink-0 items-center justify-center rounded-full text-texte-secondaire active:bg-surface-douce"
          >
            <IconeFermer taille={18} />
          </button>
        </div>
      ) : null}
    </header>
  );
}
