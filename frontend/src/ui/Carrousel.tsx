import { useEffect, useId, useRef, useState } from "react";
import { IconeRetour } from "./Icones";

/**
 * Carrousel horizontal — les rangees de la page d'accueil du site.
 *
 * **Par defaut il defile, il ne tourne pas tout seul.** Le §2.14 tranche ce
 * point pour le bandeau partenaires, et la raison vaut pour toutes les
 * rangees : un contenu qui bouge seul pendant qu'on lit est desagreable, et il
 * fait rater ce qu'on visait au moment du clic.
 *
 * ⚠️ **`automatique` leve ce defaut, et c'est un ecart assume.** Il n'est pose
 * aujourd'hui que sur « Se termine bientot », ou la rotation a un argument que
 * les autres rangees n'ont pas : cette rangee porte **ce qui ferme dans moins
 * de 48 h**, et ce qui n'est jamais vu est definitivement perdu. Ailleurs, le
 * defaut reste le bon.
 *
 * Quatre garde-fous rendent la rotation supportable, et si l'un saute elle
 * redevient la nuisance que le §2.14 decrit :
 *
 * - **elle s'arrete au survol et au focus**, donc pendant qu'on lit ou qu'on
 *   vise ;
 * - **un geste manuel l'arrete pour de bon** : fleche, molette ou doigt. Qui
 *   prend la main la garde ;
 * - **elle respecte `prefers-reduced-motion`** et ne demarre alors jamais ;
 * - **elle s'arrete quand l'onglet est cache**, pour ne pas faire tourner une
 *   animation dans le vide sur la batterie d'un telephone.
 *
 * Le defilement est celui du navigateur (`scroll-snap`), pas une animation
 * calculee en JavaScript : c'est plus fluide, ca marche au doigt comme a la
 * molette, et ca ne coute rien sur une machine modeste.
 *
 * Les fleches **disparaissent quand elles ne servent a rien** — en bout de
 * course ou quand tout tient a l'ecran. Une fleche grisee qui reste la est un
 * bouton qui ment.
 *
 * Le contenu reste atteignable au clavier et au lecteur d'ecran : c'est une
 * liste, et le defilement n'est qu'une facon de la montrer.
 */
/** Le temps entre deux avances, en millisecondes. */
const INTERVALLE_MS = 4000;

export default function Carrousel({
  titre,
  sousTitre,
  action,
  automatique = false,
  children,
}: {
  titre: string;
  sousTitre?: string;
  /** Un lien a droite du titre — « Voir plus », par exemple. */
  action?: React.ReactNode;
  /** Fait avancer la piste toute seule. Voir l'en-tete avant de l'activer. */
  automatique?: boolean;
  children: React.ReactNode;
}) {
  /* Sans nom accessible, une <section> n'est pas annoncee comme une region :
     un lecteur d'ecran traverse alors les rangees sans dire laquelle il lit. */
  const idTitre = useId();
  const piste = useRef<HTMLUListElement>(null);
  const [peutReculer, setPeutReculer] = useState(false);
  const [peutAvancer, setPeutAvancer] = useState(false);
  /** Vrai des qu'un geste manuel a eu lieu : la rotation ne reprend plus. */
  const [reprisEnMain, setReprisEnMain] = useState(false);
  const [survole, setSurvole] = useState(false);

  useEffect(() => {
    const element = piste.current;
    if (!element) {
      return;
    }
    const mesurer = () => {
      const reste =
        element.scrollWidth - element.clientWidth - element.scrollLeft;
      setPeutReculer(element.scrollLeft > 8);
      setPeutAvancer(reste > 8);
    };
    mesurer();
    element.addEventListener("scroll", mesurer, { passive: true });
    const observateur = new ResizeObserver(mesurer);
    observateur.observe(element);
    return () => {
      element.removeEventListener("scroll", mesurer);
      observateur.disconnect();
    };
  }, [children]);

  /** Une « page » = la largeur visible moins un peu, pour garder un repere. */
  const defiler = (sens: -1 | 1) => {
    const element = piste.current;
    if (!element) {
      return;
    }
    element.scrollBy({
      left: sens * (element.clientWidth * 0.85),
      behavior: "smooth",
    });
  };

  /**
   * La rotation automatique.
   *
   * **Elle revient au debut en bout de course** au lieu de s'arreter : une
   * rangee qui tourne puis se fige sur sa derniere carte a l'air cassee, et on
   * attend un moment avant de comprendre qu'il faut agir.
   *
   * Les quatre conditions d'arret de l'en-tete sont toutes ici, et chacune est
   * une ligne de ce `useEffect` — `automatique`, `reprisEnMain`, `survole` et
   * `prefers-reduced-motion`. Le `document.hidden` du minuteur en est une
   * cinquieme : un onglet en arriere-plan ne doit pas animer.
   */
  useEffect(() => {
    if (!automatique || reprisEnMain || survole) {
      return;
    }
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }
    const minuteur = window.setInterval(() => {
      const element = piste.current;
      if (!element || document.hidden) {
        return;
      }
      const reste = element.scrollWidth - element.clientWidth - element.scrollLeft;
      if (reste <= 8) {
        element.scrollTo({ left: 0, behavior: "smooth" });
        return;
      }

      /*
       * ⚠️ **Elle avance d'une carte, pas d'une page** — contrairement aux
       * fleches, qui gardent le saut de page parce qu'on les actionne pour
       * aller vite.
       *
       * `defiler(1)` deplacait de 85 % de la largeur visible. Sur un ecran
       * large, la rangee ne depasse souvent que de peu : cinq cartes de
       * 320 px tiennent presque dans 1 536 px, il ne reste que ~160 px a
       * parcourir. La rotation sautait donc **directement a la fin**, puis
       * revenait au debut au coup suivant — un aller-retour brusque qui
       * laissait en permanence une carte tranchee au bord, et qui se lisait
       * comme un defaut d'affichage plutot que comme un mouvement voulu.
       *
       * Le pas est mesure entre deux cartes voisines plutot que calcule :
       * l'ecart contient deja la gouttiere, qui change avec la largeur
       * (`gap-4` puis `lg:gap-6`). La deduire a la main ferait un second
       * endroit a corriger le jour ou elle bouge.
       */
      const cartes = element.children;
      const pas =
        cartes.length > 1
          ? (cartes[1] as HTMLElement).offsetLeft -
            (cartes[0] as HTMLElement).offsetLeft
          : element.clientWidth * 0.85;

      element.scrollBy({ left: pas, behavior: "smooth" });
    }, INTERVALLE_MS);
    return () => window.clearInterval(minuteur);
    /* `defiler` ne figure pas dans les dependances : elle est recreee a chaque
       rendu, et l'y mettre relancerait le minuteur sans arret — la rangee
       n'avancerait alors jamais. Elle ne lit que la ref, qui est stable. */
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [automatique, reprisEnMain, survole]);

  /** Tout geste manuel coupe la rotation definitivement. */
  const prendreLaMain = () => setReprisEnMain(true);

  return (
    <section
      aria-labelledby={idTitre}
      className="mt-10 first:mt-0"
      onMouseEnter={() => setSurvole(true)}
      onMouseLeave={() => setSurvole(false)}
      /* `Capture` : le focus d'une carte au clavier remonte jusqu'ici, donc la
         rotation s'arrete aussi pour qui navigue sans souris. */
      onFocusCapture={() => setSurvole(true)}
      onBlurCapture={() => setSurvole(false)}
    >
      <div className="flex items-end justify-between gap-4">
        <div className="min-w-0">
          <h2
            id={idTitre}
            className="text-xl font-semibold text-texte lg:text-2xl"
          >
            {titre}
          </h2>
          {sousTitre ? (
            <p className="mt-0.5 text-sm text-texte-secondaire">{sousTitre}</p>
          ) : null}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {/* « Voir plus » avant les fleches : c'est l'issue de la rangee, et
              elle doit se lire avant les commandes de defilement. */}
          {action}
          <FlecheCarrousel
            sens="precedent"
            visible={peutReculer}
            onClick={() => {
              prendreLaMain();
              defiler(-1);
            }}
          />
          <FlecheCarrousel
            sens="suivant"
            visible={peutAvancer}
            onClick={() => {
              prendreLaMain();
              defiler(1);
            }}
          />
        </div>
      </div>

      <ul
        ref={piste}
        /*
         * `-mx-4 px-4` : les cartes touchent le bord de la zone de defilement
         * mais restent alignees sur la marge au repos.
         *
         * `relative` n'est pas decoratif et il ne faut pas le retirer. Une
         * zone de defilement en `position: static` n'est pas le bloc
         * conteneur de ses descendants positionnes en absolu : ceux-ci se
         * calent alors sur un ancetre plus haut, **echappent au clipping** et
         * etirent toute la page vers la droite. Sans lui, le site gagne une
         * barre de defilement horizontale et 650 px de vide.
         */
        /* Un geste au doigt ou a la molette coupe la rotation : qui prend la
           main la garde. `onPointerDown` couvre le doigt, la souris et le
           stylet d'un seul coup. */
        onPointerDown={prendreLaMain}
        onWheel={prendreLaMain}
        className="defilement-discret relative mt-4 -mx-4 flex snap-x snap-mandatory gap-4 overflow-x-auto px-4 pb-1 lg:gap-6"
      >
        {children}
      </ul>
    </section>
  );
}

function FlecheCarrousel({
  sens,
  visible,
  onClick,
}: {
  sens: "precedent" | "suivant";
  visible: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={sens === "precedent" ? "Précédent" : "Suivant"}
      aria-hidden={!visible}
      tabIndex={visible ? 0 : -1}
      className={`flex size-11 items-center justify-center rounded-full border border-bordure-champ text-texte transition-opacity hover:border-primaire hover:text-primaire ${
        visible ? "opacity-100" : "pointer-events-none opacity-0"
      }`}
    >
      <IconeRetour
        taille={20}
        className={sens === "suivant" ? "rotate-180" : undefined}
      />
    </button>
  );
}
