import { useMemo, useState } from "react";
import CarteUrgente from "../composants/CarteUrgente";
import TuilesCategories from "../composants/TuilesCategories";
import PucesFiltresActifs from "../composants/PucesFiltresActifs";
import TiroirFiltres from "../composants/TiroirFiltres";
import CarteGroupage from "../composants/CarteGroupage";
import LigneGroupage from "../composants/LigneGroupage";
import RechercheEtFiltres from "../composants/RechercheEtFiltres";
import {
  compterParCategorie,
  filtreActif,
  filtrerEtTrier,
  type Filtres,
  separerParUrgence,
} from "../../domaine/filtres";
import type { Groupage } from "../../domaine/groupage";
import { useCatalogue } from "../../api/CatalogueContexte";
import { useNotifications } from "../../api/NotificationsContexte";
import { ErreurReseau, ListeEnChargement } from "../../ui/EtatReseau";
import EnTeteApplication from "../mise-en-page/EnTeteApplication";
import PiedPage from "../mise-en-page/PiedPage";
import Bouton from "../../ui/Bouton";
import Carrousel from "../../ui/Carrousel";
import EtatVide from "../../ui/EtatVide";
import { IconeCarton, IconeFiltre } from "../../ui/Icones";

/**
 * Le catalogue — ecran 2 sur telephone, page d'accueil du site sur ordinateur.
 *
 * **Deux architectures, pas deux feuilles de style.**
 *
 * | | Telephone | Ordinateur (≥ 768 px) |
 * |---|---|---|
 * | Entree | Le fil plein ecran, puis cet ecran | **Cette page directement** |
 * | Resultats | Des **lignes** separees d'un filet (§2.3) | Une **grille de cartes** |
 * | Filtres | Des puces defilantes, faute de place | Une colonne laterale |
 * | Navigation | `BarreNav` en bas | En-tete et pied de page |
 *
 * La ligne du §2.3 reste la bonne forme sur 390 px, pour les raisons que la
 * spec donne : sur fond blanc une carte blanche n'existe pas, et une liste de
 * lignes defile mieux sur un telephone d'entree de gamme. Ces deux raisons
 * tombent sur une grille de bureau, ou il faut bien delimiter des colonnes
 * voisines.
 *
 * **Ce fichier ne contient aucune regle de filtrage.** Le modele, les seuils,
 * le tri et le partage des deux rangees viennent tous de `domaine/filtres.ts`.
 * C'est ce qui garantit que la puce « Se termine bientot » et le carrousel du
 * meme nom montrent exactement les memes groupages.
 *
 * Aucun mur d'authentification des deux cotes (§1.5) : on parcourt et on
 * filtre librement, le compte n'est demande qu'au moment de payer.
 *
 * Les cartes et les lignes portent la **barre de progression** du §2.5 : le
 * groupeur declare combien de personnes il veut reunir, et c'est ce nombre
 * qu'elle remplit. ⚠️ Ni plafond ni minimum — `JaugeParticipants` porte la
 * regle en entier.
 *
 * Un ecart assume : aucun prix barre nulle part (§3).
 */
export default function GroupagesOuverts({
  estBureau,
  filtres,
  onFiltres,
  onOuvrirGroupage,
  onDemanderProduit,
  rechercheDepliee = false,
}: {
  estBureau: boolean;
  filtres: Filtres;
  onFiltres: (filtres: Filtres) => void;
  /** On arrive par la loupe du fil : l'en-tete ouvre son champ. */
  rechercheDepliee?: boolean;
  onOuvrirGroupage: (groupage: Groupage) => void;
  onDemanderProduit: () => void;
}) {
  const { groupages, chargement, erreur, recharger } = useCatalogue();
  /* La cloche vit dans la coquille ; cet ecran n'en lit que le compteur
     et de quoi l'ouvrir. */
  const cloche = useNotifications();

  /* ⚠️ `groupages` passe explicitement aux deux fonctions de filtrage, qui
     acceptaient jusqu'ici une source par defaut lue dans les constantes. Sans
     ce passage, l'ecran filtrerait un catalogue fige pendant que le reste de
     l'application affiche celui du serveur — defaut qui ne se verrait qu'au
     premier produit ajoute en base. */
  const comptesCategories = useMemo(
    () => compterParCategorie(groupages),
    [groupages],
  );
  const resultats = useMemo(
    () => filtrerEtTrier(filtres, groupages),
    [filtres, groupages],
  );
  const nombre = resultats.length;

  /** Le tiroir de filtres. Ferme par defaut : on arrive pour voir, pas pour regler. */
  const [tiroirOuvert, setTiroirOuvert] = useState(false);

  /**
   * Combien de filtres sont poses, pour la pastille du bouton.
   *
   * ⚠️ **La recherche en fait partie, et le tri non.** Un tri ne retire aucun
   * groupage de la liste — annoncer « 1 filtre » parce qu'on a choisi « prix
   * croissant » ferait chercher un filtrage qui n'existe pas. La recherche, à
   * l'inverse, cache des résultats : elle compte.
   */
  const nombreFiltresActifs =
    (filtres.recherche.trim() ? 1 : 0) +
    (filtres.categorie !== "toutes" ? 1 : 0) +
    (filtres.termineBientot ? 1 : 0) +
    (filtres.petitPrix ? 1 : 0);

  const etatVide = (
    <EtatVide
      titre={
        filtres.recherche.trim()
          ? `Aucun groupage pour « ${filtres.recherche.trim()} »`
          : "Aucun groupage ne correspond"
      }
      explication="Élargissez votre recherche, ou demandez ce produit : un groupeur peut le lancer."
      actionLibelle="Demander ce produit"
      onAction={onDemanderProduit}
    />
  );

  const finDeListe = (
    <div className="border-t border-filet px-4 py-8 text-center lg:px-0 lg:py-12">
      <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-primaire-fond text-primaire-texte-sur-fond">
        <IconeCarton taille={24} />
      </span>
      <p className="mt-3 font-medium text-texte">
        Vous avez vu tous les groupages ouverts
      </p>
      <div className="mx-auto mt-4 max-w-72">
        <Bouton style="secondaire" onClick={onDemanderProduit}>
          Créer une demande d&apos;achat groupé
        </Bouton>
      </div>
    </div>
  );

  /* ── Ordinateur ──────────────────────────────────────────────────────── */
  /**
   * ⚠️ **Le chargement et l'erreur passent AVANT `if (estBureau)`, et c'est la
   * correction de deux défauts d'un seul tenant.**
   *
   * Ils étaient enfermés dans la branche bureau, ce qui coûtait des deux
   * côtés :
   *
   * | | Ce qui se passait |
   * |---|---|
   * | **Ordinateur** | Ils montaient `EnTeteApplication`, l'en-tête du téléphone, alors que `ApplicationAcheteur` affiche déjà `EnTeteBureau` au-dessus : **deux barres de navigation empilées** |
   * | **Téléphone** | Ils n'existaient pas. Une panne réseau affichait « aucun groupage » — on annonçait qu'il n'y a rien à acheter alors que le serveur était tombé |
   *
   * Le second était le plus coûteux, et le plus discret : un état vide et une
   * panne se ressemblent à l'écran, mais l'un invite à revenir plus tard et
   * l'autre doit proposer « Réessayer ».
   *
   * Un seul garde, deux chromes. Il n'y a aucun hook entre ici et les deux
   * `const` de la branche bureau, donc ce déplacement ne change rien à l'ordre
   * des hooks — c'est la seule chose à vérifier avant de remonter un retour
   * anticipé.
   */
  if (chargement || erreur) {
    /**
     * L'attente prend **la forme d'une liste**, pas celle d'un tourniquet.
     *
     * Des rectangles à la place des vignettes donnent la bonne hauteur tout de
     * suite : rien ne bouge au moment où les produits arrivent. Un tourniquet
     * centré, lui, fait sauter toute la page quand le contenu le remplace — et
     * sur la connexion visée par le §5, ce saut arrive après deux secondes,
     * c'est-à-dire juste au moment où l'œil s'est posé.
     *
     * ⚠️ **Sur ordinateur, la forme n'est pas encore la bonne** :
     * `ListeEnChargement` dessine des lignes, alors que le catalogue de bureau
     * est une grille de cartes. L'attente ne provoque donc pas de saut sur
     * téléphone, mais elle en provoque un ici. C'est un reste à traiter, et il
     * vaut mieux l'écrire que de laisser croire le contraire.
     */
    /* On teste `erreur` et non `chargement`, pour deux raisons qui vont dans
       le meme sens. TypeScript n'affine `erreur` que dans la branche qui la
       teste : ecrit dans l'autre sens, il refusait `ErreurApi | undefined`.
       Et au **rechargement apres une panne**, les deux sont vrais a la fois —
       montrer le squelette plutot que l'erreur est alors la bonne reponse,
       puisque le « Reessayer » est deja en cours. */
    const corps =
      erreur && !chargement ? (
        <ErreurReseau erreur={erreur} onReessayer={recharger} />
      ) : (
        <ListeEnChargement nombre={6} className="px-4" />
      );

    if (estBureau) {
      /* Pas d'en-tête ici : `ApplicationAcheteur` monte déjà `EnTeteBureau`.
         Et pas de `pb-18` non plus — la barre de navigation du bas est un
         composant du téléphone, réserver sa hauteur sur ordinateur laisse un
         blanc que rien ne remplit. */
      return (
        <>
          <div className="largeur-page py-8">{corps}</div>
          <PiedPage />
        </>
      );
    }

    return (
      /* `pb-18` : la hauteur exacte de `BarreNav`, qui flotte au-dessus du
         contenu. Les deux branches d'origine écrivaient `pb-20`, une valeur
         qui ne correspondait à rien. */
      <div className="pb-18">
        <EnTeteApplication
          notifications={cloche.nonLues}
          onNotifications={cloche.ouvrir}
        />
        {corps}
      </div>
    );
  }

  if (estBureau) {
    /**
     * **La rangee « Les autres groupages » a ete retiree.**
     *
     * Elle rejouait, dans un carrousel a defiler, exactement les cartes que la
     * grille « Tous les groupages ouverts » montre juste en dessous — et sans
     * rien a faire valoir, puisque c'etait par construction la rangee de ce
     * qui ne presse pas. Deux carrousels avant la grille, c'etaient deux
     * gestes avant le catalogue. **Rien n'est perdu** : la grille reste la
     * liste complete, filtres compris.
     *
     * « Se termine bientot » reste, et son maintien est tout le propos : elle
     * porte la seule information qui justifie de sortir un groupage du lot,
     * le temps restant (§2.4).
     */
    const { presqueClotures } = separerParUrgence(resultats);

    /**
     * Le bandeau de tete et la publicite ne s'affichent que sur l'accueil, pas
     * pendant une recherche. Quelqu'un qui a tape « riz » veut ses resultats,
     * pas un bandeau de marque a traverser avant de les atteindre.
     */
    const enRecherche = filtreActif(filtres);

  return (
      <>
        {enRecherche ? null : (
          <>
            {/*
             * Le lavis orange du bandeau de tete — la seule surface coloree de
             * la page, et elle **se degrade vers le blanc**. Le catalogue en
             * dessous garde donc le fond blanc unique que le §1.2 demande, et
             * la couleur ne sert qu'a marquer l'entree du site.
             *
             * ⚠️ **Les deux bouts du degrade sont calcules, pas estimes.** Un
             * texte pose sur un degrade doit tenir sur la teinte la plus claire
             * comme sur la plus foncee, donc chaque paire est verifiee deux
             * fois :
             *
             * | Jeton de texte | sur `primaire-fond` | sur blanc |
             * |---|---|---|
             * | `texte` | 16,08:1 | 17,79:1 |
             * | `texte-secondaire` | 5,42:1 | 6,00:1 |
             * | `primaire-texte-sur-fond` | 4,87:1 | 5,39:1 |
             * | `confiance` | 9,36:1 | 10,36:1 |
             *
             * **`primaire` (#CC4A00) n'y figure pas, et c'est delibere.** Il ne
             * tient qu'a **4,17:1** sur `primaire-fond`, sous le seuil de
             * 4,5:1 : c'est exactement la raison d'etre du jeton
             * `primaire-texte-sur-fond`, qui existe pour que l'orange du texte
             * change avec son fond au lieu de perdre son contraste.
             */}
            {/* ⚠️ **Fond blanc.** Le bloc portait un aplat `primaire-fond`
                 pale ; la couleur est maintenant **dans la carte**, pas
                 derriere elle. Une teinte de fond plus une carte coloree
                 posee dessus font deux oranges qui se disputent, et aucun des
                 deux ne porte. */}
            <div className="border-b border-filet">
              {/*
               * ⚠️ **La banniere partenaires a ete retiree de l'accueil.**
               *
               * Le composant `composants/BandeauPartenaires` **existe
               * toujours** et reste entierement fonctionnel : il n'est plus
               * monte, c'est tout. L'emplacement publicitaire du §9.3 reste
               * donc a placer, et c'est une decision en attente, pas un
               * abandon — ne pas supprimer le fichier en croyant nettoyer du
               * code mort.
               *
               * Ce qu'il faudra trancher le jour ou on le replace : un
               * emplacement payant doit etre vu pour valoir quelque chose,
               * mais la premiere fenetre appartient aux groupages. Entre la
               * grille et le pied de page, ou entre deux rangees de la
               * grille, sont les deux pistes qui ne prennent la place de
               * personne.
               */}

              {/* ⚠️ `largeur-page` plutot qu'une gouttiere a soi.

                   Cette page avait raison de refuser le plafond de 1 280 px —
                   il laissait 320 px de vide de chaque cote sur un ecran de
                   1 920. Mais elle l'a refuse **seule**, pendant que la fiche
                   produit, les commandes et le profil le gardaient : d'un
                   ecran a l'autre, la page sautait.

                   Le plafond commun est a 1 600, et la gouttiere grandit avec
                   l'ecran — voir `largeur-page` dans `index.css`. */}
              {/*
                ⚠️ `lg:py-7` et non `lg:py-14` : 56 px rendus a la premiere
                fenetre. Le budget complet est au-dessus de la rangee « Se
                termine bientot ».

                ## ⚠️ Deux colonnes, parce qu'il y avait un vide a droite

                Le texte est plafonne a `max-w-2xl` — 672 px — dans un
                conteneur qui en fait 1 600. Il restait donc **plus de 900 px
                de degrade vide** a droite du titre, sur l'ecran d'ouverture du
                site.

                Ce qu'on y met n'est pas un remplissage : c'est **la promesse
                du produit**, et elle ne s'affichait nulle part sur grand
                ecran. `BandeauConfiance` n'etait monte que dans la branche
                telephone — un visiteur de bureau arrivait donc sur le
                catalogue sans jamais lire « vous etes livre, ou rembourse »,
                alors que le §1.7 en fait le signal de confiance de
                l'application et que c'est lui qui decide quelqu'un a payer
                d'avance un inconnu.

                ⚠️ **Elle ne coute aucune hauteur** : le bloc de confiance fait
                environ 90 px, le bloc de titre 164. C'est la colonne la plus
                haute qui commande, donc la premiere fenetre ne bouge pas.
              */}
              <div className="largeur-page py-6 lg:py-5">
               <div className="rounded-2xl bg-primaire px-6 py-7 lg:flex lg:items-center lg:justify-between lg:gap-12 lg:px-10 lg:py-6">
                {/*
                  ⚠️ **Une carte orange pleine, et c'est un changement de
                  direction demande.**

                  Le bloc etait un lavis `primaire-fond` qui se degradait vers
                  le blanc : discret, et c'etait le reproche — la page
                  d'ouverture ne portait aucune couleur. La reference donnee
                  est eBay et Walmart, dont les pages d'accueil sont faites de
                  blocs colores francs.

                  `primaire` `#CC4A00` avec du blanc dessus : **4,62:1**. C'est
                  conforme, et c'est **juste** conforme — d'ou deux regles a ne
                  pas relacher ici :

                  - **aucun texte secondaire sur cet aplat.** `white/80` y
                    tomberait a 3,3:1. Tout ce qui est ecrit dessus est en
                    blanc plein ;
                  - **jamais `marque` `#FF6A00` a la place.** Le blanc n'y tient
                    qu'a 2,87:1, et c'est l'erreur que le §1.2 interdit
                    nommement.
                */}
                <div className="max-w-2xl">
                  {/*
                   * L'exergue bleu. Le §1.2 reserve le bleu a la confiance cote
                   * acheteur, et il travaille ici pour la meme raison qu'au
                   * `BandeauConfiance` : c'est parce que tout le reste est
                   * orange qu'il arrete l'oeil. Pastille blanche plutot que
                   * `confiance-fond`, qui se perdrait sur le lavis — deux
                   * teintes tres claires cote a cote ne dessinent plus de
                   * forme.
                   */}
                  {/*
                   * ⚠️ **Ecart assume au §1.3**, qui fixe `Titre-ecran` a 24 px.
                   * Cette echelle est celle d'un ecran de 390 px ; a 1 280 px
                   * un titre de 24 px ne tient plus le haut d'une page, il
                   * flotte. Le titre suit donc la largeur de la fenetre :
                   *
                   * | Fenetre | 4,2vw | Rendu |
                   * |---|---|---|
                   * | 768 px *(seuil bureau)* | 32,3 px | **32 px** |
                   * | 952 px et au-dela | ≥ 40 px | **40 px** *(plafond)* |
                   *
                   * ⚠️ **Le plafond est descendu de 48 a 40 px**, pour rendre
                   * 8 px a la premiere fenetre. C'est le seul des quatre
                   * reglages de ce budget qui touche la typographie, et c'est
                   * pour cela qu'il vient en dernier : 40 px tiennent encore
                   * le haut d'une page a 1 600 px, ce qui n'etait pas vrai des
                   * 24 px de la spec.
                   *
                   * La borne basse de 24 px n'est, elle, **jamais atteinte
                   * ici** : il faudrait une fenetre de moins de 571 px, et en
                   * dessous de 768 px c'est la branche telephone qui s'affiche,
                   * avec le jeton `Titre-ecran` de la spec. Elle reste comme
                   * garde-fou, pas comme palier reel.
                   */}
                  {/* ⚠️ **Plus de second ton sur le titre.** « a plusieurs »
                      etait en `primaire-texte-sur-fond` ; sur l'aplat orange,
                      cette teinte tombe a 1,2:1 et disparait. Le titre est
                      donc d'un seul blanc, et c'est le fond qui porte la
                      couleur — ce qui est l'inversion exacte de ce qu'on
                      faisait avant. */}
                  <h1 className="text-[clamp(1.5rem,4.2vw,2.5rem)] leading-[1.06] font-semibold tracking-tight text-white">
                    Le prix de gros, à plusieurs
                  </h1>

                  {/*
                   * Le seul endroit de la page ou l'orange vif `marque`
                   * s'emploie. Il le peut parce que **c'est un trait, pas du
                   * texte** : #FF6A00 ne tient qu'a 2,87:1 sur blanc, ce qui
                   * l'interdit a toute lettre, mais un filet decoratif n'a pas
                   * de contraste a tenir.
                   */}
                  {/* ⚠️ Le filet passe en blanc : `marque` `#FF6A00` sur
                      `primaire` `#CC4A00` ne vaut que 1,3:1 — il serait
                      invisible. */}
                  <span
                    aria-hidden="true"
                    className="mt-5 block h-1 w-16 rounded-full bg-white/80"
                  />

                  {/*
                   * 18 px sur bureau. Le §1.3 donne 16 px comme **plancher**,
                   * pas comme plafond : une accroche lue a un metre d'un ecran
                   * d'ordinateur gagne les deux pixels, la ou le corps de
                   * texte du catalogue les garderait pour lui.
                   */}
                  {/* Blanc plein, pas `white/80` : voir l'encadre ci-dessus. */}
                  <p className="mt-4 max-w-xl text-base text-white lg:text-lg">
                    Rejoignez un groupage et payez votre part. Le groupeur
                    ne touche les fonds qu&apos;à la clôture.
                  </p>
                </div>

                {/* ⚠️ **La carte de confiance a ete retiree d'ici, pas du
                    produit.** Le bandeau de tete est une accroche, pas un
                    contrat : y poser les conditions de remboursement obligeait a
                    les lire avant meme d'avoir vu un seul prix.

                    Elle reste la ou elle engage vraiment, c'est-a-dire au
                    moment de payer. Ce qui ne sert pas a l'instant ou on le lit
                    n'est pas rassurant, c'est du remplissage.

                    ⚠️ **Etat reel au moment ou ces lignes sont ecrites** : elle
                    n'est plus montee que sur l'ecran 5 (Commander) et sur le
                    catalogue telephone, plus bas dans ce fichier. Elle a ete
                    retiree de l'ecran 3 sur demande — elle y tenait 110 px et
                    repoussait « Commander » sous la ligne de flottaison. Les
                    ecrans 7 et 9 ne l'ont jamais portee. La liste de
                    verification de la spec, qui nomme les ecrans 3, 5, 7 et 9,
                    est donc en retard sur le produit : c'est elle qu'il faudra
                    corriger, ou ces ecrans qu'il faudra rejoindre. */}
               </div>
              </div>
            </div>

            {/*
              Ce qui presse d'abord : le temps restant est le seul element de
              pression de l'application (§2.4). Sur fond blanc, pour que la
              couleur reste au bandeau de tete.

              ## ⚠️ Elle doit tenir dans la premiere fenetre, sans defilement

              C'est une exigence, pas une preference : cette rangee porte **ce
              qui ferme dans moins de 48 h**, et ce qui n'est jamais vu est
              definitivement perdu. Sous la ligne de flottaison, elle
              n'existait pas pour qui ne faisait pas defiler — une alerte
              invisible n'est pas une alerte.

              Elle n'y tenait pas. Le budget, a 1 600 px de large :

              | | Avant | Maintenant |
              |---|---|---|
              | En-tete de bureau | 80 px | 80 px |
              | Banniere partenaires | 432 px | **120 px** |
              | Bloc de titre | 228 px | **164 px** |
              | Cette rangee | 445 px | **280 px** |
              | **Total** | **1 185 px** | **644 px** |

              1 185 px debordaient de 285 px sur un ecran de 1 080, et de
              525 px sur un portable de 768. 644 px tiennent sur les deux.

              ⚠️ **Aucune hauteur n'est forcee a `100dvh`**, et c'est
              delibere : une section calee sur la hauteur de la fenetre casse
              des qu'on zoome, qu'on ouvre la console ou qu'on arrive sur un
              portable court — elle rogne alors le contenu au lieu de le
              laisser depasser. Les quatre reglages ci-dessus suffisent, et ils
              degradent proprement : sur un ecran trop court, la rangee est
              simplement a moitie visible, ce qui invite a faire defiler.

              Les quatre vont ensemble. En relacher un remet la rangee sous la
              ligne.
            */}
            {/*
              ⚠️ **Fond blanc ici aussi** : la bande `surface-douce` qui
              separait cette rangee a ete retiree sur demande.

              Ce qu'elle apportait — savoir ou une section finit et ou la
              suivante commence — est maintenant porte par les **filets** et
              par les titres seuls. C'est plus discret, et il faut le savoir :
              si la page redonne l'impression d'une seule feuille continue,
              c'est ici qu'il faudra regarder, et la reponse ne sera pas de
              remettre un aplat mais de travailler l'espacement entre
              sections.
            */}
            {presqueClotures.length > 0 ? (
              <div className="pt-8 pb-8 lg:pt-6 lg:pb-8">
               <div className="largeur-page">
                <Carrousel
                  titre="Se termine bientôt"
                  sousTitre={`${presqueClotures.length} groupage${
                    presqueClotures.length > 1 ? "s" : ""
                  } ferme${presqueClotures.length > 1 ? "nt" : ""} dans moins de 48 h`}
                  /* ⚠️ La seule rangee du site qui tourne seule. Son argument
                     est le temps : ce qui ferme dans 48 h et n'est jamais vu
                     est definitivement perdu. Les quatre garde-fous sont dans
                     l'en-tete de `ui/Carrousel.tsx`. */
                  automatique
                  action={
                    /*
                     * « Voir plus » ne mene pas vers une page de plus : il
                     * **pose le filtre** `termineBientot` sur le catalogue qui
                     * est deja en dessous.
                     *
                     * Une page separee aurait fallu l'ecrire, la router et la
                     * tenir a jour, pour montrer exactement ce que la grille
                     * sait deja montrer. Et le resultat est meilleur : on
                     * arrive sur une liste **filtrable**, ou le filtre pose
                     * apparait en puce et se retire d'un clic.
                     */
                    <button
                      type="button"
                      onClick={() => {
                        onFiltres({ ...filtres, termineBientot: true });
                        /* Sans ce defilement, le filtre s'applique a une
                           grille restee hors champ : on clique et rien ne
                           semble se passer. */
                        document
                          .getElementById("catalogue")
                          ?.scrollIntoView({ behavior: "smooth" });
                      }}
                      className="rounded-full px-3 py-2 text-sm font-semibold text-primaire underline underline-offset-2 hover:text-primaire-presse"
                    >
                      Voir plus
                    </button>
                  }
                >
                  {presqueClotures.map((groupage) => (
                    <CarteUrgente
                      key={groupage.id}
                      groupage={groupage}
                      onOuvrir={onOuvrirGroupage}
                    />
                  ))}
                </Carrousel>
               </div>
              </div>
            ) : null}

            {/*
              Les categories, juste avant la grille qu'elles filtrent.

              ⚠️ **Elles ne sont pas plus haut, et c'est un arbitrage.** Sur
              eBay comme sur Walmart, la rangee de categories est tout en
              haut. Ici, la premiere fenetre est deja prise par la rangee « Se
              termine bientot », qui devait y tenir sans defilement — c'etait
              une demande explicite, et les tuiles l'auraient repoussee de
              ~150 px, donc sous la ligne de flottaison sur un portable.

              Posees ici, elles gardent leur sens : on vient de voir ce qui
              presse, on choisit maintenant ou chercher, et la grille filtree
              est immediatement en dessous.
            */}
            <div className="largeur-page pt-10 lg:pt-12">
              <TuilesCategories
                /* ⚠️ **Le catalogue entier, pas `resultats`.** Les tuiles
                   prennent leur photo dans la liste qu'on leur passe : avec
                   la liste filtree, choisir « Maison » aurait vide les cinq
                   autres tuiles de leur image — les categories se seraient
                   effacees au moment precis ou l'on s'en sert pour naviguer. */
                groupages={groupages}
                actif={filtres.categorie}
                onChoisir={(categorie) => {
                  onFiltres({
                    ...filtres,
                    /* Recliquer la categorie active la retire : une tuile
                       pressee qui ne se depresse pas enferme dans un filtre
                       qu'il faut ensuite aller defaire ailleurs. */
                    categorie:
                      filtres.categorie === categorie ? "toutes" : categorie,
                  });
                  document
                    .getElementById("catalogue")
                    ?.scrollIntoView({ behavior: "smooth" });
                }}
              />
            </div>
          </>
        )}

        <div
          id="catalogue"
          className="largeur-page border-t border-filet py-6 lg:py-8"
        >
          <div>
            <div className="min-w-0 flex-1">
              <div>
                <h2 className="text-2xl font-semibold tracking-tight text-texte lg:text-titre-ecran">
                  Tous les groupages ouverts
                </h2>
                {/* Le compteur en deux graisses : le chiffre se lit seul, la
                    phrase ne fait que le qualifier. Pas d'opacite ici — les
                    deux niveaux sont les deux jetons de texte du §1.2, dont le
                    contraste est connu (17,79:1 et 6,00:1 sur blanc). */}
                <p aria-live="polite" className="mt-1 text-texte-secondaire">
                  {nombre === 0 ? (
                    "Aucun groupage ne correspond"
                  ) : (
                    <>
                      <strong className="font-semibold text-texte">
                        {nombre}
                      </strong>{" "}
                      {`groupage${nombre > 1 ? "s" : ""} ouvert${
                        nombre > 1 ? "s" : ""
                      }`}
                    </>
                  )}
                </p>
              </div>

              {/*
               * ⚠️ **La colonne de filtres est devenue un bouton**, ce que le
               * §2 interdisait : « Jamais derriere un bouton "Filtres" — ce
               * serait un menu cache. » La demande est explicite et
               * posterieure, donc elle s'applique ; la raison du §2 reste
               * vraie, et deux choses la ramenent a peu de chose :
               *
               * - **le bouton porte le nombre de filtres actifs**, lisible
               *   sans ouvrir ;
               * - **les filtres actifs restent affiches a cote**, en puces,
               *   et se retirent d'un clic. Ce qui est range, c'est le choix
               *   des filtres ; leur etat ne l'est jamais.
               *
               * Si l'une des deux saute, le tiroir redevient le menu cache que
               * le §2 decrit.
               */}
              <div className="mt-5 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => setTiroirOuvert(true)}
                  className="inline-flex h-11 shrink-0 items-center gap-2 rounded-full border border-bordure px-4 font-medium text-texte hover:border-primaire hover:text-primaire"
                >
                  <IconeFiltre taille={18} />
                  Filtrer
                  {nombreFiltresActifs > 0 ? (
                    <span className="flex size-5 items-center justify-center rounded-full bg-primaire text-xs font-bold text-white">
                      {nombreFiltresActifs}
                    </span>
                  ) : null}
                </button>

                <PucesFiltresActifs filtres={filtres} onChanger={onFiltres} />
              </div>

              {nombre === 0 ? (
                etatVide
              ) : (
                <>
                  {/* ⚠️ **Le nombre de colonnes suit la largeur, depuis qu'il n'y a plus
                      de colonne centree a 1 280 px.** La grille s'arretait a trois
                      colonnes : sur un ecran de 1 920, cela donnait des cartes de
                      **620 px de large avec une photo de 465 px de haut**, soit
                      deux produits et demi par ecran. Une vignette de catalogue
                      n'a pas besoin d'etre plus grande qu'une main.

                      Les paliers visent une carte de 320 a 350 px : 1 920 ÷ 5
                      donne 352, 1 280 ÷ 4 donne 288. Le palier a 1 800 px est
                      assume — `2xl` (1 536) passerait a cinq colonnes trop tot,
                      avec des cartes de 275 px. */}
                  {/* ⚠️ La derniere colonne arrive a `2xl`, plus a 1 800 px.

                      Le conteneur **s'arrete a 1 600 px** : passe cette
                      largeur, rien ne grandit plus. Une cinquieme colonne
                      declenchee a 1 800 px ne gagnait donc aucune place,
                      elle **retrecissait les cartes** de 376 a 300 px — des
                      vignettes qui maigrissent quand l'ecran grandit, ce qui
                      est exactement l'inverse de ce qu'on attend.

                      Calee sur `2xl`, elle tombe la ou le conteneur cesse de
                      croitre, et les cartes gardent ~300 px partout. */}
                  <ul className="mt-6 grid grid-cols-2 gap-4 lg:mt-8 lg:grid-cols-3 lg:gap-6 xl:grid-cols-4 2xl:grid-cols-5">
                    {resultats.map((groupage) => (
                      <CarteGroupage
                        key={groupage.id}
                        groupage={groupage}
                        onOuvrir={onOuvrirGroupage}
                      />
                    ))}
                  </ul>
                  <div className="mt-12">{finDeListe}</div>
                </>
              )}
            </div>
          </div>
        </div>

        <TiroirFiltres
          ouvert={tiroirOuvert}
          onFermer={() => setTiroirOuvert(false)}
          filtres={filtres}
          onChanger={onFiltres}
          comptesCategories={comptesCategories}
          total={groupages.length}
          nombreResultats={nombre}
        />

        <PiedPage />
      </>
    );
  }

  /* ── Telephone : lignes, puces, barre de navigation ──────────────────── */
  return (
    <div className="pb-18">
      <EnTeteApplication
        recherche={filtres.recherche}
        onRecherche={(recherche) => onFiltres({ ...filtres, recherche })}
        rechercheDepliee={rechercheDepliee}
        notifications={cloche.nonLues}
        onNotifications={cloche.ouvrir}
      />


      <div className="mt-4">
        <RechercheEtFiltres
          filtres={filtres}
          onChanger={onFiltres}
          comptesCategories={comptesCategories}
          nombreResultats={nombre}
        />
      </div>

      {nombre === 0 ? (
        etatVide
      ) : (
        <>
          <ul className="px-4">
            {resultats.map((groupage) => (
              <LigneGroupage
                key={groupage.id}
                groupage={groupage}
                onOuvrir={onOuvrirGroupage}
              />
            ))}
          </ul>
          {finDeListe}
        </>
      )}
    </div>
  );
}
