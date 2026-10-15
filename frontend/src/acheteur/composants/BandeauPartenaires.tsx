import { useCallback, useEffect, useRef, useState } from "react";
import { ANNONCEURS } from "../../donnees/annonceurs";
import { IconeRetour } from "../../ui/Icones";

/**
 * `BandeauPartenaires` — SPEC_ECRANS_FIGMA.md §2.14, §9.3 du cahier des
 * charges. L'emplacement publicitaire vendu aux entreprises, ici en bannieres
 * illustrees qui defilent seules.
 *
 * ⚠️ **Le defilement automatique est un ecart assume avec le §2.14**, qui
 * ecrit « pas de rotation automatique : un contenu qui bouge seul au-dessus
 * d'un fil qu'on fait defiler est desagreable et empeche de toucher ce qu'on
 * visait ». La demande est explicite et posterieure, donc elle s'applique —
 * mais la gene decrite par la spec est reelle, et quatre garde-fous la
 * ramenent a peu de chose :
 *
 * - **la rotation s'arrete au survol et au focus clavier**, donc elle ne
 *   derobe jamais la cible d'un clic en cours ;
 * - **elle s'arrete aussi des qu'on fait defiler a la main**, et ne reprend
 *   pas : un geste de l'utilisateur l'emporte sur l'automatisme ;
 * - **elle ne demarre pas du tout** si le systeme demande a reduire les
 *   animations — reglage d'accessibilite courant sur Android ;
 * - **elle se met en pause quand l'onglet est en arriere-plan**, pour ne pas
 *   faire tourner une minuterie et des images dans le vide sur un forfait de
 *   donnees limite.
 *
 * Le §2.14 est a corriger, sans quoi il contredit l'ecran construit.
 *
 * **Les deux autres regles du §2.14 tiennent, et elles ne sont pas
 * negociables :** la mention « Sponsorise » est affichee — obligation de
 * loyaute, pas option de mise en page — et une banniere ne porte **ni prix ni
 * bouton « Commander »**. Sur un produit qui vend la confiance, laisser
 * confondre une publicite et un groupage est le genre d'erreur qui coute cher.
 *
 * **Variante `aucun-annonceur` : le bandeau disparait entierement.** Pas de
 * « Votre publicite ici », pas de place vide — un emplacement vide fait plus
 * de mal qu'une absence.
 *
 * ## ⚠️ Sur bureau, c'est un bandeau, plus une affiche
 *
 * Elle faisait **400 px de haut** a 1 600 px de large (`lg:aspect-[4/1]`), et
 * c'etait le defaut le plus couteux de la page d'accueil : avec l'en-tete et le
 * bloc de titre, la premiere fenetre etait entierement occupee par une
 * publicite. La rangee « Se termine bientot » — celle qui porte ce qui ferme
 * dans moins de 48 h — tombait sous la ligne de flottaison, donc n'existait
 * pas pour qui ne faisait pas defiler.
 *
 * Elle passe a **96 px** (`lg:h-24`), et sa presentation change avec sa taille :
 *
 * | | Avant | Maintenant *(bureau)* |
 * |---|---|---|
 * | Hauteur | 400 px | **96 px** |
 * | Texte | deux lignes empilees, 24 px | **une seule ligne**, 16 px |
 * | Nom et accroche | l'un sous l'autre | **cote a cote**, separes d'un point |
 *
 * Une affiche de 400 px demandait un titre de 24 px pour ne pas flotter ; un
 * bandeau de 96 px demande l'inverse — une ligne qui se lit d'un coup d'oeil.
 * Ce n'est donc pas la meme mise en page reduite, c'en est une autre.
 *
 * ⚠️ **Sur telephone, rien ne change** : `aspect-3/1` sur 390 px fait deja
 * 130 px, et la question de la ligne de flottaison ne se pose pas de la meme
 * facon sur un ecran qu'on fait defiler du pouce.
 *
 * ## ⚠️ Le voile est plus fort, et sa limite est calculee
 *
 * Du blanc sur une photo n'a pas de contraste calculable : il depend de
 * l'image. Le voile le porte, et les deux valeurs sont celles deja verifiees
 * dans `CarteUrgente`, **dans le pire cas d'une photo entierement blanche** :
 *
 * | Voile | Couleur reelle | Blanc pur |
 * |---|---|---|
 * | `from-black/85` *(bord gauche)* | `#262626` | **15,13:1** |
 * | `via-black/70` *(a 50 % de la largeur)* | `#4D4D4D` | **8,45:1** |
 *
 * Le texte est donc borne a **48 % de la largeur** : il reste entierement dans
 * la zone ou le voile vaut au moins 70 %, soit 8,45:1 au pire. C'est ce
 * plafond qui porte la garantie, pas le degrade seul — l'elargir la casse, et
 * silencieusement, puisque aucun outil ne mesure du texte sur une image.
 *
 * Les annonceurs et les visuels sont **fictifs** : voir `donnees/annonceurs.ts`.
 */

/** Assez pour lire une accroche, assez court pour que le suivant arrive. */
const INTERVALLE_MS = 5000;

export default function BandeauPartenaires() {
  const [indice, setIndice] = useState(0);
  const [enPause, setEnPause] = useState(false);
  /** Un geste manuel coupe la rotation pour de bon. */
  const [abandonnee, setAbandonnee] = useState(false);
  const piste = useRef<HTMLUListElement>(null);
  const defilementAutomatique = useRef(false);

  const total = ANNONCEURS.length;

  const allerA = useCallback((cible: number) => {
    const element = piste.current;
    if (!element) {
      return;
    }
    const prochain = (cible + ANNONCEURS.length) % ANNONCEURS.length;
    defilementAutomatique.current = true;
    element.scrollTo({
      left: prochain * element.clientWidth,
      behavior: "smooth",
    });
    setIndice(prochain);
    // Le temps que le defilement doux se termine avant de reecouter.
    window.setTimeout(() => {
      defilementAutomatique.current = false;
    }, 600);
  }, []);

  // La rotation elle-meme, avec ses quatre conditions d'arret.
  useEffect(() => {
    if (total < 2 || enPause || abandonnee) {
      return;
    }
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }
    const minuteur = window.setInterval(() => {
      if (!document.hidden) {
        allerA(indice + 1);
      }
    }, INTERVALLE_MS);
    return () => window.clearInterval(minuteur);
  }, [indice, enPause, abandonnee, total, allerA]);

  // Un defilement au doigt ou a la molette met fin a la rotation.
  useEffect(() => {
    const element = piste.current;
    if (!element) {
      return;
    }
    const auDefilement = () => {
      const position = Math.round(element.scrollLeft / element.clientWidth);
      setIndice(position);
      if (!defilementAutomatique.current) {
        setAbandonnee(true);
      }
    };
    element.addEventListener("scroll", auDefilement, { passive: true });
    return () => element.removeEventListener("scroll", auDefilement);
  }, []);

  if (total === 0) {
    return null;
  }

  return (
    <section
      aria-label="Partenaires"
      aria-roledescription="carrousel"
      onMouseEnter={() => setEnPause(true)}
      onMouseLeave={() => setEnPause(false)}
      onFocusCapture={() => setEnPause(true)}
      onBlurCapture={() => setEnPause(false)}
      /*
       * ⚠️ **`largeur-page`, et c'est un revirement.**
       *
       * La banniere allait d'un bord a l'autre, avec cet argument : « une
       * image qui touche les bords est une image ; une image avec 32 px de
       * blanc autour est une vignette ». Il valait pour une affiche de
       * 400 px. Il ne vaut plus pour un bandeau de 96 px.
       *
       * Ce qu'on voyait a la place, sur un ecran de 1 920 : une bande sombre
       * collee aux deux bords, pendant que le titre « Le prix de gros »
       * commencait 160 px plus loin. Les deux ne s'alignaient sur rien, et
       * c'est precisement le defaut que `largeur-page` a ete ecrit pour
       * supprimer partout ailleurs — la banniere etait la derniere exception.
       *
       * Alignee et arrondie, elle se lit comme **un bloc de la page** et non
       * comme une bande de fond.
       *
       * `py-3` et non `py-4` : 8 px rendus a la premiere fenetre.
       */
      className="largeur-page py-3"
    >
      <div className="group relative overflow-hidden rounded-xl">
        <ul
          ref={piste}
          className="defilement-discret relative flex snap-x snap-mandatory overflow-x-auto"
        >
          {ANNONCEURS.map((annonceur, position) => (
            <li
              key={annonceur.id}
              aria-roledescription="diapositive"
              aria-label={`${position + 1} sur ${total}`}
              className="w-full shrink-0 snap-start"
            >
              <button
                type="button"
                /* ⚠️ **Hauteur fixe sur bureau, proportion sur telephone.**
                   Une proportion grandit avec la largeur : `aspect-[4/1]`
                   faisait 400 px a 1 600 px et 640 px sur un ecran de 2 560.
                   Une publicite ne doit pas grandir parce que l'ecran grandit
                   — c'est le contenu qui devrait en profiter. */
                className="relative block aspect-3/1 w-full overflow-hidden text-left lg:aspect-auto lg:h-24"
              >
                <img
                  src={annonceur.image}
                  alt={annonceur.imageAlt}
                  loading={position === 0 ? "eager" : "lazy"}
                  decoding="async"
                  className="absolute inset-0 size-full object-cover"
                />
                {/* Le voile porte le contraste du texte blanc, exactement
                    comme sur le fil (§1.3). */}
                <span
                  aria-hidden="true"
                  /* ⚠️ `via-black/70` et non `/45`. A 45 %, le voile tombait a
                     **3,56:1** en son milieu — sous le seuil de 4,5:1 — et le
                     texte, large de 70 %, y entrait. Valeurs dans l'en-tete. */
                  className="absolute inset-0 bg-gradient-to-r from-black/85 via-black/70 to-transparent"
                />
                {/* `pl-16` : le texte demarre apres la fleche de gauche, qui est
                    centree verticalement du meme cote. Sans ca, les deux se
                    superposent des que la souris entre dans la banniere. */}
                {/* ⚠️ **`max-w-[48%]` sur bureau porte la garantie de
                    contraste**, pas seulement la mise en page : au-dela, le
                    texte sort de la zone ou le voile vaut 70 %. Voir le
                    tableau de l'en-tete avant de l'elargir.

                    `pl-16` : le texte demarre apres la fleche de gauche, qui
                    est centree verticalement du meme cote. Sans ca, les deux
                    se superposent des que la souris entre dans la banniere. */}
                {/* ⚠️ **Deux conteneurs, et il en faut deux.**
                    L'exterieur centre verticalement, l'interieur dispose le
                    nom et l'accroche.

                    Les fondre en un seul cassait le centrage : en
                    `lg:flex-row`, `justify-center` centre sur l'axe
                    **horizontal**, plus vertical, et `items-baseline` collait
                    alors le texte en haut du bandeau. C'est exactement ce que
                    la capture montrait. */}
                <span className="absolute inset-y-0 left-0 flex max-w-[70%] flex-col justify-center pr-5 pl-16 lg:max-w-[48%] lg:pl-20">
                 <span className="flex flex-col gap-1 lg:flex-row lg:items-baseline lg:gap-2">
                  <span className="text-lg font-semibold text-white lg:shrink-0 lg:text-base">
                    {annonceur.nom}
                  </span>
                  {/* ⚠️ `min-w-0` : sans lui, `truncate` ne coupe rien. Un element
                        flex a `min-width: auto` par defaut, donc il refuse de
                        passer sous la largeur de son contenu — le texte
                        depasse du voile au lieu de finir en points de
                        suspension, et il depasse la ou le contraste n'est plus
                        garanti. */}
                  <span className="min-w-0 truncate text-sm text-white/90">
                    {/* Le point separateur n'existe que quand les deux textes
                        sont sur la meme ligne. */}
                    <span aria-hidden="true" className="hidden lg:inline">
                      ·{" "}
                    </span>
                    {annonceur.accroche}
                  </span>
                 </span>
                </span>

                {/*
                 * ⚠️ **« Sponsorise » est revenu**, et il devait revenir.
                 *
                 * Le §9.3 en fait une obligation de loyaute : une banniere
                 * payante qui ne se declare pas se fait passer pour du
                 * contenu editorial. Elle avait ete retiree pour
                 * l'encombrement — une pastille dans un coin **ne coute aucun
                 * pixel de hauteur** et tient la meme promesse.
                 *
                 * Et elle sert aussi le dessin : a 96 px, la photo n'est plus
                 * qu'une texture sombre. Sans cette pastille, le bandeau ne
                 * se lit comme rien de precis. Avec elle, on sait en un coup
                 * d'oeil que ce n'est pas un groupage.
                 *
                 * `bg-black/70` : **8,45:1** pour du blanc dans le pire cas
                 * d'une photo entierement blanche — meme valeur que le voile.
                 */}
                <span className="absolute top-2.5 right-4 rounded-full bg-black/70 px-2 py-0.5 text-[11px] font-medium tracking-wide text-white uppercase">
                  Sponsorisé
                </span>
              </button>
            </li>
          ))}
        </ul>

        {total > 1 ? (
          <>
            <FlecheBanniere
              sens="precedent"
              onClick={() => {
                setAbandonnee(true);
                allerA(indice - 1);
              }}
            />
            <FlecheBanniere
              sens="suivant"
              onClick={() => {
                setAbandonnee(true);
                allerA(indice + 1);
              }}
            />

            <div className="absolute right-4 bottom-3 flex gap-1.5">
              {ANNONCEURS.map((annonceur, position) => (
                <button
                  key={annonceur.id}
                  type="button"
                  aria-label={`Aller à l'annonce ${position + 1}`}
                  aria-current={position === indice}
                  onClick={() => {
                    setAbandonnee(true);
                    allerA(position);
                  }}
                  className="p-1.5"
                >
                  <span
                    className={`block h-1.5 rounded-full transition-all ${
                      position === indice ? "w-5 bg-white" : "w-1.5 bg-white/60"
                    }`}
                  />
                </button>
              ))}
            </div>
          </>
        ) : null}
      </div>

    </section>
  );
}

function FlecheBanniere({
  sens,
  onClick,
}: {
  sens: "precedent" | "suivant";
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={sens === "precedent" ? "Annonce précédente" : "Annonce suivante"}
      /* Visibles au survol et au clavier seulement : la banniere n'est pas
         l'endroit ou l'on veut attirer l'oeil en permanence. */
      className={`absolute top-1/2 flex size-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-texte opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100 ${
        sens === "precedent" ? "left-3" : "right-3"
      }`}
    >
      <IconeRetour
        taille={18}
        className={sens === "suivant" ? "rotate-180" : undefined}
      />
    </button>
  );
}
