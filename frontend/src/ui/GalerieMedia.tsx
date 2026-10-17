import { useEffect, useState } from "react";
import type { MediaProduit } from "../domaine/groupage";
import { IconeFermer, IconeLecture } from "./Icones";

/**
 * La galerie de la fiche produit — jusqu'a 4 images et 2 videos.
 *
 * ## La regle qui commande tout le reste : rien ne se telecharge tout seul
 *
 * Le public vise a un **forfait de donnees limite** (§18.1), et une video pese
 * cent fois une photo. Trois consequences, et aucune n'est negociable :
 *
 * - **`preload="none"`** : tant que l'acheteur n'a pas appuye, la video ne
 *   coute rien. Sans cet attribut, le navigateur en telecharge le debut des
 *   l'ouverture de la fiche — pour une video qui, le plus souvent, ne sera
 *   jamais regardee ;
 * - **aucune lecture automatique**, nulle part. On voit l'affiche, on appuie ;
 * - **le son coupe au depart** (§1.6), parce qu'une fiche produit qui se met a
 *   parler dans un taxi se referme aussitot.
 *
 * ## Ce qui est montre quand il n'y a qu'une image
 *
 * **Rien de plus qu'avant** : pas de vignettes, pas de compteur, pas de
 * fleches. Une galerie d'un seul element est une galerie qui ment sur ce
 * qu'elle contient, et les commandes qu'elle affiche ne menent nulle part.
 *
 * ## L'accessibilite n'est pas une option ici
 *
 * Les vignettes sont de vrais boutons dans une liste, atteignables au clavier,
 * et celle qui est affichee porte `aria-current`. Le texte alternatif de
 * chaque image retombe sur le nom du produit quand le groupeur ne l'a pas
 * renseigne : un `alt` vide sur la photo principale d'une fiche d'achat laisse
 * un lecteur d'ecran annoncer « image », ce qui n'aide personne a decider.
 *
 * ## ⚠️ Deux proportions, et c'est une correction de fond
 *
 * Le cadre etait en `4/5` **partout**. Sur bureau, la colonne fait 576 px :
 * l'image occupait donc **720 px de haut**, plus que la fenetre utile d'un
 * portable. Trois choses tombaient sous la ligne de flottaison du meme coup —
 * les vignettes des autres photos, qui ne se voyaient donc jamais ; le bouton
 * « Commander » de la colonne d'a cote ; et toute idee de comparer l'image au
 * prix.
 *
 * | | Telephone | Bureau |
 * |---|---|---|
 * | Proportion | `4/5` | **`4/3`** |
 * | Hauteur rendue | 487 px sur 390 | **432 px** sur 576 |
 *
 * Le portrait reste juste sur un telephone, qu'on tient en hauteur. Sur un
 * ecran large, c'est le paysage qui laisse la place au reste.
 *
 * ⚠️ Ce que coute ce choix, et il faut le dire : en `object-cover`, un cadre
 * plus large **recadre davantage** une photo verticale. C'est precisement ce
 * que repare l'agrandissement au clic — la photo entiere est a un clic, au
 * lieu d'occuper l'ecran en permanence.
 */
export default function GalerieMedia({
  medias,
  titre,
  children,
}: {
  medias: MediaProduit[];
  /** Le nom du produit — le repli du texte alternatif. */
  titre: string;
  /**
   * Ce qui se pose **sur** le media : retour, partage, pastille de statut.
   *
   * En `children` plutot qu'en proprietes nommees : la galerie n'a pas a
   * connaitre le detail de ce que l'ecran 3 superpose, et l'ecran 3 n'a pas a
   * refaire le cadre.
   */
  children?: React.ReactNode;
}) {
  const [actif, setActif] = useState(0);
  /** La video que l'acheteur a demandee. Avant ce geste, rien ne charge. */
  const [lance, setLance] = useState(false);
  /** L'image affichee en grand, par-dessus la page. */
  const [agrandie, setAgrandie] = useState(false);

  /* Changer de media coupe la lecture en cours : sans ce retour a zero, on
     reviendrait sur une image avec le son d'une video qui tourne derriere. */
  useEffect(() => {
    setLance(false);
  }, [actif]);

  /* Echap ferme l'agrandissement, et le defilement de la page est fige
     derriere : sans cela, la molette fait glisser la fiche sous l'image, et on
     la retrouve ailleurs en refermant. */
  useEffect(() => {
    if (!agrandie) {
      return;
    }
    const auClavier = (evenement: KeyboardEvent) => {
      if (evenement.key === "Escape") setAgrandie(false);
    };
    const defilementInitial = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", auClavier);
    return () => {
      document.body.style.overflow = defilementInitial;
      window.removeEventListener("keydown", auClavier);
    };
  }, [agrandie]);

  if (medias.length === 0) {
    return (
      <div className="aspect-4/5 w-full bg-surface-douce lg:aspect-auto lg:h-full lg:rounded-xl" />
    );
  }

  const media = medias[Math.min(actif, medias.length - 1)];
  const texte = media.alt?.trim() || titre;

  return (
    /* ⚠️ **`lg:h-full` et `flex-col` : c'est ce qui supprime le vide.**
       Sur telephone, rien ne change — la galerie garde son format 4/5 et se
       laisse mesurer par son contenu. Sur ordinateur, elle remplit la hauteur
       que son parent lui donne, et l'image prend tout ce qui reste une fois
       les vignettes placees. */
    <div className="lg:flex lg:h-full lg:flex-col">
      {/* `lg:aspect-auto` annule le format fixe : au-dela de `lg`, c'est
          `flex-1` qui decide de la hauteur, et `min-h-0` autorise la boite a
          retrecir sous la taille de son contenu — sans lui, une image en
          `object-cover` pousse le conteneur et le debordement revient. */}
      <div className="relative aspect-4/5 w-full overflow-hidden bg-surface-douce lg:aspect-auto lg:min-h-0 lg:flex-1 lg:rounded-xl">
        {media.type === "image" ? (
          /* ⚠️ **L'image est un bouton.** Le cadre recadre — c'est le prix du
             format paysage — donc il faut un moyen de voir la photo entiere.
             `zoom-in` au survol l'annonce avant le clic : une image cliquable
             qui ne le dit pas n'est jamais cliquee. */
          <button
            type="button"
            onClick={() => setAgrandie(true)}
            aria-label={`Agrandir : ${texte}`}
            className="size-full cursor-zoom-in"
          >
            <img
              src={media.url}
              alt={texte}
              /* Seule la couverture est prioritaire : les autres ne sont
                 demandees que si l'acheteur les ouvre. */
              fetchPriority={actif === 0 ? "high" : "auto"}
              decoding="async"
              className="size-full object-cover"
            />
          </button>
        ) : lance ? (
          /* `autoPlay` ne contredit pas la regle ci-dessus : cet element
             n'existe qu'apres l'appui. Sans lui, l'acheteur devrait appuyer
             deux fois — une pour demander la video, une pour la lancer. */
          <video
            src={media.url}
            poster={media.affiche}
            controls
            autoPlay
            muted
            playsInline
            className="size-full bg-black object-contain"
          >
            {texte}
          </video>
        ) : (
          <button
            type="button"
            onClick={() => setLance(true)}
            className="group size-full"
            aria-label={`Lire la vidéo : ${texte}`}
          >
            {media.affiche ? (
              <img
                src={media.affiche}
                alt=""
                decoding="async"
                className="size-full object-cover"
              />
            ) : null}
            {/* Le bouton est **pose sur** l'affiche, pas a cote : c'est la
                qu'on appuie d'instinct. Fond blanc a 92 % comme les autres
                commandes posees sur un media (§2.1).
                ⚠️ La mention est **sous le bouton, au centre**, et non en bas
                du cadre : le bas-gauche porte deja la pastille de statut, et
                les deux se chevauchaient. */}
            <span className="absolute inset-0 flex flex-col items-center justify-center gap-3">
              <span className="flex size-16 items-center justify-center rounded-full bg-white/92 text-texte">
                <IconeLecture taille={28} />
              </span>
              {/* Dit franchement ce que l'appui va couter. Sur un forfait
                  limite, c'est une information, pas un ornement. */}
              <span className="rounded-full bg-white/92 px-3 py-1 text-xs font-medium text-texte-secondaire">
                Vidéo — se lance quand vous appuyez
              </span>
            </span>
          </button>
        )}

        {children}
      </div>

      {/* ⚠️ Un seul media : aucune commande. Voir l'en-tete. */}
      {medias.length > 1 ? (
        <ul
          /* `pb-1` : sans lui, l'anneau de focus et l'anneau de
             selection sont rognes par le bord de la boite defilante — on voit
             un demi-anneau, ce qui ressemble a un defaut d'affichage. */
          className="mt-4 flex shrink-0 gap-3 overflow-x-auto px-4 pb-1 lg:px-0"
          aria-label={`Les ${medias.length} médias du produit`}
        >
          {medias.map((vignette, rang) => (
            <li key={`${vignette.url}-${rang}`} className="shrink-0">
              <button
                type="button"
                onClick={() => setActif(rang)}
                aria-current={rang === actif ? "true" : undefined}
                aria-label={
                  vignette.type === "video"
                    ? `Vidéo ${rang + 1}`
                    : `Photo ${rang + 1}`
                }
                /* ⚠️ **L'etat actif se joue sur un anneau, pas sur une
                   nuance de contour.** Il etait `border-texte` contre
                   `border-bordure` : deux contours de 2 px, l'un sombre
                   l'autre gris tres pale — a 64 px et du coin de l'oeil, on
                   ne voyait pas laquelle etait selectionnee.

                   L'anneau `primaire` avec un ecart (`ring-offset`) detache
                   franchement la vignette active, et l'inactive passe en
                   opacite reduite : la difference se lit maintenant sur deux
                   signaux au lieu d'un demi.

                   `size-20` plutot que `size-16` : a cote d'une image de
                   700 px de haut, 64 px se lisait comme un residu. */
                className={`relative block size-20 shrink-0 overflow-hidden rounded-xl transition ${
                  rang === actif
                    ? "ring-2 ring-primaire ring-offset-2 ring-offset-white"
                    : "opacity-70 ring-1 ring-bordure-champ hover:opacity-100"
                }`}
              >
                <img
                  src={vignette.type === "video" ? vignette.affiche : vignette.url}
                  alt=""
                  loading="lazy"
                  decoding="async"
                  className="size-full bg-surface-douce object-cover"
                />
                {/* La pastille dit **avant l'appui** que c'est une video. Sans
                    elle, on clique sur ce qu'on croit etre une photo et on
                    declenche un telechargement qu'on n'avait pas demande. */}
                {vignette.type === "video" ? (
                  <span className="absolute inset-0 flex items-center justify-center bg-black/30 text-white">
                    <IconeLecture taille={18} />
                  </span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {agrandie && media.type === "image" ? (
        /*
         * ⚠️ **`object-contain` ici, `object-cover` dans le cadre.** C'est
         * toute la raison d'etre de cet agrandissement : la vignette recadre
         * pour tenir dans une mise en page, la vue agrandie montre la photo
         * **entiere**. Les deux en `cover` rendraient le clic inutile.
         *
         * Le voile est a 90 % : une photo de produit se juge sur ses couleurs,
         * et un fond clair derriere fausse ce qu'on croit voir. Le noir est
         * ici fonctionnel, pas decoratif.
         */
        <div
          role="dialog"
          aria-modal="true"
          aria-label={texte}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4"
        >
          {/* Le fond ferme : c'est le geste attendu, et il couvre tout
              l'ecran. Un bouton de fermeture seul obligerait a viser. */}
          <button
            type="button"
            onClick={() => setAgrandie(false)}
            aria-label="Fermer l'image"
            className="absolute inset-0 cursor-zoom-out"
          />

          <img
            src={media.url}
            alt={texte}
            decoding="async"
            className="relative max-h-full max-w-full object-contain"
          />

          {/* La croix reste, pour qui ne devine pas que le fond ferme. */}
          <button
            type="button"
            onClick={() => setAgrandie(false)}
            aria-label="Fermer l'image"
            className="absolute top-4 right-4 flex size-11 items-center justify-center rounded-full bg-white/92 text-texte"
          >
            <IconeFermer taille={20} />
          </button>

          {medias.length > 1 ? (
            /* Changer de photo sans refermer : sinon il faut sortir, viser une
               vignette, et rouvrir — trois gestes pour voir la suivante. */
            <div className="absolute inset-x-0 bottom-6 flex justify-center gap-2">
              {medias.map((vignette, rang) => (
                <button
                  key={`${vignette.url}-${rang}`}
                  type="button"
                  onClick={() => setActif(rang)}
                  aria-label={`Photo ${rang + 1}`}
                  aria-current={rang === actif ? "true" : undefined}
                  className={`h-2 rounded-full transition-all ${
                    rang === actif ? "w-6 bg-white" : "w-2 bg-white/60"
                  }`}
                />
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
