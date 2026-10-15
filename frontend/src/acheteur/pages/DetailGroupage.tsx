import { useState } from "react";
import Bouton, { BoutonAncre } from "../../ui/Bouton";
import {
  IconeCamion,
  IconeHorloge,
  IconePartager,
  IconeQuestion,
  IconeRetour,
  IconeVerifie,
} from "../../ui/Icones";
import PiedPage from "../mise-en-page/PiedPage";
import GalerieMedia from "../../ui/GalerieMedia";
import JaugeParticipants from "../../composants/JaugeParticipants";
import CarteGroupage from "../composants/CarteGroupage";
import { type Groupage } from "../../domaine/groupage";
import {
  decrireTempsRestant,
  formaterDateCourte,
  formaterFrancs,
} from "../../domaine/format";
import { FRAIS_PROVISOIRES } from "../../domaine/livraison";

/**
 * Ecran 3 — Detail d'un groupage. SPEC_ECRANS_FIGMA.md ecran 3, mis en forme
 * d'apres la maquette fournie.
 *
 * **Objectif : donner tout ce qu'il faut pour decider de payer.** Le bouton ne
 * demande aucun compte (§1.5) — il ouvre l'ecran 5.
 *
 * **Deux mises en page.** Sur telephone, une seule colonne et le bouton ancre
 * en bas, comme la maquette. Sur ordinateur, la fiche produit classique d'un
 * site marchand : le media a gauche, et a droite un **bloc d'achat colle en
 * haut** qui reste visible pendant qu'on lit la fiche — prix, compteurs,
 * garantie, bouton. Un bouton ancre en bas d'ecran est un geste de pouce ; a
 * la souris, c'est le bloc d'achat qui doit suivre.
 *
 * Trois points de la spec qu'il ne faut pas relacher, quelle que soit la
 * largeur :
 *
 * - ⚠️ **le `BandeauConfiance` a ete retire de cet ecran**, sur demande. Il
 *   etait avant le bouton d'achat, et il y tenait 110 px avec son interligne
 *   — c'est lui qui repoussait « Commander » sous la ligne de flottaison. La
 *   promesse n'est pas perdue : elle reste au bloc de tete de l'accueil, et
 *   « Les regles » ci-dessous la redit en toutes lettres, remboursement
 *   compris. **Ne pas le remonter ici sans trouver ces 110 px ailleurs** ;
 * - les frais de livraison ne sont **jamais annonces comme un tarif unique**
 *   ici. A ce stade l'acheteur n'a pas dit ou il est, donc l'ecran ne peut pas
 *   connaitre son prix : « selon votre position », puis « a partir de
 *   1 000 F CFA ». Ecrire « 1 000 F partout » serait un engagement que le vrai
 *   calcul ne tiendra pas ;
 * - la derniere regle est a ecrire **exactement** comme elle l'est. Une
 *   fenetre de contestation fermee a la livraison est acceptable si elle est
 *   annoncee ; decouverte apres coup, elle est vecue comme une arnaque.
 *
 * Les questions sont **publiques** : il n'y a pas d'echange prive entre un
 * acheteur et un groupeur dans ce produit.
 *
 * ⚠️ Les blocs gris `surface-douce` viennent de la maquette et s'ecartent du
 * §1.0, qui demande de separer par le vide et un filet. La maquette l'emporte
 * parce qu'elle est la decision la plus recente, mais le §1.0 est a corriger.
 */
export default function DetailGroupage({
  groupage,
  estBureau,
  onRetour,
  onCommander,
  onQuestions,
  onPartager,
  onOuvrirGroupage,
  similaires = [],
  questionsOuvertes = false,
}: {
  groupage: Groupage;
  estBureau: boolean;
  onRetour: () => void;
  onCommander: () => void;
  /** Vers l'ecran 10. Le seul canal entre acheteur et groupeur (§1.7). */
  onQuestions: () => void;
  /**
   * Partage la fiche : feuille du systeme sur telephone, presse-papier
   * ailleurs. Tenu par la coquille, qui sait fabriquer le lien et afficher
   * « Lien copie ».
   */
  onPartager: () => void;
  /** Ouvrir un autre groupage depuis la section « Dans la meme categorie ». */
  onOuvrirGroupage?: (groupage: Groupage) => void;
  /**
   * Les groupages proposes sous la fiche.
   *
   * ⚠️ **Choisis par la coquille, pas ici.** Cet ecran ne connait pas le
   * catalogue et n'a pas a le connaitre : lui faire lire le contexte le
   * rendrait impossible a monter seul, et c'est exactement ce qui arrive
   * quand on veut le dessiner dans un atelier de maquette.
   */
  similaires?: readonly Groupage[];
  /**
   * Vrai quand le panneau de questions est deja ouvert.
   *
   * ⚠️ Sert a **retirer le bouton flottant** : les deux se posent dans le
   * meme angle, et sans cela le bouton s'affichait par-dessus le panneau
   * qu'il venait d'ouvrir.
   */
  questionsOuvertes?: boolean;
}) {
  const [descriptionDepliee, setDescriptionDepliee] = useState(false);
  const temps = decrireTempsRestant(groupage.heuresRestantes);
  const cloture = temps.urgence === "terminee";

  /* La couverture reste en tete : c'est elle que l'acheteur a vue sur la
     carte, et la retrouver en premier sur la fiche confirme qu'il a ouvert le
     bon groupage. `photo` sert de repli pour les campagnes d'avant la liste. */
  const medias =
    groupage.medias && groupage.medias.length > 0
      ? groupage.medias
      : groupage.photo
        ? [
            {
              type: "image" as const,
              url: groupage.photo,
              alt: groupage.photoAlt,
            },
          ]
        : [];

  const media = (
    <GalerieMedia medias={medias} titre={groupage.produit}>
      {/* Les boutons en surimpression sont la pour le pouce. Sur ordinateur,
          le retour est dans le fil d'Ariane et le partage dans le bloc
          d'achat : deux retours a l'ecran seraient un de trop. */}
      {estBureau ? null : (
        <>
          <button
            type="button"
            onClick={onRetour}
            aria-label="Retour"
            className="absolute top-3 left-3 flex size-11 items-center justify-center rounded-full bg-white/92 text-texte"
          >
            <IconeRetour taille={20} />
          </button>
          <button
            type="button"
            onClick={onPartager}
            aria-label="Partager ce groupage"
            className="absolute top-3 right-3 flex size-11 items-center justify-center rounded-full bg-white/92 text-texte"
          >
            <IconePartager taille={20} />
          </button>
        </>
      )}

      {/* `Statut` (§2.8) : « en cours » est un etat qui avance, donc orange. */}
      <span className="absolute bottom-3 left-3 inline-flex items-center gap-1.5 rounded-full bg-white/92 px-3 py-1 text-xs font-semibold text-primaire-texte-sur-fond">
        <span aria-hidden="true" className="size-2 rounded-full bg-marque" />
        Groupage en cours
      </span>
    </GalerieMedia>
  );

  /** Titre, prix, compteurs, groupeur. Identique dans les deux mises en page. */
  const enTeteProduit = (
    <div>
      <h2 className="text-2xl font-semibold text-texte lg:text-3xl">
        {groupage.produit}
      </h2>

      {/* Le prix seul. Ni prix barre, ni pastille de reduction (§3). */}
      <p className="mt-2 flex items-baseline gap-2">
        <span className="text-prix font-bold text-primaire lg:text-3xl">
          {formaterFrancs(groupage.prixPart)}
        </span>
        <span className="text-texte-secondaire">par part</span>
      </p>

      {/* Une seule horloge : l'encart porte la sienne.

          ⚠️ **Le verbe suit l'etat.** « Se termine le 7 octobre » sur un
          groupage deja cloture annonce au present une date passee. Ce cas
          n'arrive plus en parcourant — le catalogue ne sert que l'ouvert —
          mais la fiche reste atteignable par son lien, et c'est precisement
          l'acheteur qui a paye qui la rouvre. */}
      <div className="mt-3 flex items-start gap-2 rounded-xl bg-primaire-fond px-3 py-2.5 text-sm text-primaire-texte-sur-fond">
        <IconeHorloge taille={18} className="mt-0.5 shrink-0" />
        <p>
          <strong className="font-semibold">{temps.libelle}</strong>{" "}
          {temps.urgence === "terminee" ? "— il s'est terminé le" : "— se termine le"}{" "}
          {formaterDateCourte(groupage.clotureLe)} à 23 h 59
        </p>
      </div>

      {/* La barre de progression vers l'objectif du groupeur (§2.5).
          ⚠️ Ce n'est **ni un plafond ni un minimum** — voir
          `JaugeParticipants`, qui porte la règle en entier. */}
      <div className="mt-3">
        <JaugeParticipants
          acheteursConfirmes={groupage.acheteursConfirmes}
          objectif={groupage.objectifParticipants}
          progression={groupage.progression}
        />
      </div>

      {/* Pseudonyme, non cliquable, sans aucun autre detail (§1.7). */}
      <p className="mt-1.5 flex items-center gap-1.5 text-texte-secondaire">
        Proposé par
        <span className="font-semibold text-texte">{groupage.groupeur}</span>
        <IconeVerifie taille={15} className="text-confiance" />
      </p>
    </div>
  );

  const contenuPart = (
    <section className="rounded-xl bg-surface-douce p-4">
      <h3 className="font-semibold text-texte">Ce que contient une part</h3>
      <p className="mt-1.5 text-texte-secondaire">{groupage.contenuPart}</p>
    </section>
  );

  const livraison = (
    <section className="rounded-xl bg-surface-douce p-4">
      <div className="flex items-start gap-3">
        <IconeCamion
          taille={22}
          className="mt-0.5 shrink-0 text-texte-secondaire"
        />
        <div>
          <h3 className="font-semibold text-texte">
            Délai estimé d&apos;arrivée du colis
          </h3>
          <p className="mt-1 text-texte-secondaire">
            Réception chez vous sous 3 à 5 jours après la clôture, à domicile
            par notre partenaire.
          </p>
          <p className="mt-2 font-semibold text-texte">
            Frais de livraison selon votre position
          </p>
          <p className="text-xs text-texte-secondaire">
            à partir de {formaterFrancs(FRAIS_PROVISOIRES)}
          </p>
        </div>
      </div>
    </section>
  );

  const caracteristiques = (
    <section className="rounded-xl bg-surface-douce p-4">
      <h3 className="font-semibold text-texte">Caractéristiques</h3>
      <dl className="mt-2">
        {groupage.caracteristiques.map((caracteristique) => (
          <div
            key={caracteristique.cle}
            className="flex justify-between gap-4 border-b border-filet py-2 last:border-b-0 last:pb-0"
          >
            <dt className="text-texte-secondaire">{caracteristique.cle}</dt>
            <dd className="text-right font-medium text-texte">
              {caracteristique.valeur}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );

  const description = (
    <section>
      <h3 className="text-lg font-semibold text-texte">Description</h3>
      <p
        className={`mt-2 text-texte-secondaire ${
          descriptionDepliee ? "" : "line-clamp-4"
        }`}
      >
        {groupage.description}
      </p>
      <button
        type="button"
        onClick={() => setDescriptionDepliee(!descriptionDepliee)}
        className="mt-1 min-h-12 text-sm font-semibold text-primaire"
      >
        {descriptionDepliee ? "Voir moins" : "Voir plus"}
      </button>
    </section>
  );

  const regles = (
    /*
     * ⚠️ **Ces quatre lignes sont la politique, pas de la redaction.** Deux
     * d'entre elles etaient restees sur l'ancien modele :
     *
     * 1. elles s'arretaient a « detenu jusqu'a la cloture » **sans dire ce
     *    qui se passe apres**. Or c'est la que tout a change : le groupeur
     *    retire son argent a la cloture, donc **avant la livraison**, et a
     *    partir de ce moment ce n'est plus la detention des fonds qui
     *    protege l'acheteur mais **la garantie de Group Achat**. Une fiche qui
     *    ne le dit pas laisse croire que son argent nous attend jusqu'au
     *    colis ;
     * 2. la derniere affirmait que « la contestation n'est plus possible
     *    apres acceptation » — vrai, mais elle taisait l'essentiel : **on
     *    peut refuser le colis a la remise**, et c'est examine sous 48 h
     *    (ecran 9). Elle decrivait donc une porte fermee la ou il y en a une
     *    ouverte.
     *
     * ⚠️ Formulations interdites ici, §1.7 : « bloque jusqu'a la livraison »,
     * et tout pourcentage — les 1 500 F sont a la charge du groupeur, retenus
     * a son retrait, et ne regardent pas l'acheteur.
     */
    <section>
      <h3 className="text-lg font-semibold text-texte">Les règles</h3>
      <ul className="mt-2 space-y-2">
        {[
          <>
            Paiement à la commande, <strong className="font-semibold">détenu
            jusqu&apos;à la clôture</strong> du groupage
          </>,
          <>
            À la clôture, le groupeur reçoit les fonds et prépare la commande.{" "}
            <strong className="font-semibold">
              Group Achat garantit votre livraison
            </strong>
          </>,
          <>
            <strong className="font-semibold">
              Si le groupage n&apos;aboutit pas, vous êtes remboursé
              intégralement
            </strong>
            , frais de livraison compris
          </>,
          <>
            <strong className="font-semibold">
              Vérifiez le colis devant le livreur
            </strong>{" "}
            : vous pouvez le refuser. Group Achat examine votre dossier sous
            48 h et vous rembourse si le refus est justifié
          </>,
        ].map((regle, indice) => (
          <li key={indice} className="flex gap-2.5 text-texte-secondaire">
            <span
              aria-hidden="true"
              className="mt-2 size-1.5 shrink-0 rounded-full bg-primaire"
            />
            <span>{regle}</span>
          </li>
        ))}
      </ul>
    </section>
  );

  const questions = (
    <section>
      <h3 className="text-lg font-semibold text-texte">
        Questions sur ce groupage
      </h3>

      {groupage.questionsRecentes?.length ? (
        <div className="mt-3 space-y-3">
          {groupage.questionsRecentes.map((echange) => (
            <article
              key={echange.question}
              className="rounded-xl bg-surface-douce p-3"
            >
              <p className="flex items-center gap-1.5 text-xs text-texte-secondaire">
                <IconeQuestion taille={14} />
                Acheteur vérifié
              </p>
              <p className="mt-1 font-medium text-texte">{echange.question}</p>
              <div className="mt-2 border-l-2 border-primaire pl-3">
                <p className="text-xs font-semibold text-primaire">
                  Réponse de {groupage.groupeur}
                </p>
                <p className="mt-0.5 text-sm text-texte-secondaire">
                  {echange.reponse}
                </p>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-texte-secondaire">
          Aucune question pour l&apos;instant.
        </p>
      )}

      {/*
        ⚠️ **Deux défauts corrigés ici, et ils se cumulaient.**

        1. Le bouton « Posez une question » n'avait **aucun `onClick`** : sur
           ordinateur, il avait l'air d'un bouton, il réagissait au survol, et
           il ne faisait rien. C'est la pire sorte de panne — on croit avoir
           mal appuyé, alors on recommence.
        2. « Voir les N questions » ne s'affichait que si `questions > 0`.
           Autrement dit, sur un groupage **sans aucune question**, il
           n'existait plus aucun chemin vers l'écran des questions depuis un
           téléphone : personne ne pouvait poser la première. Le produit qui
           en a le plus besoin était celui qui l'interdisait.

        D'où : le bouton d'envoi existe **toujours**, sur les deux largeurs, et
        son libellé suit ce qu'on y trouvera.
      */}
      <div className="mt-3 flex flex-wrap items-center gap-3">
        {groupage.questions > 0 ? (
          <button
            type="button"
            onClick={onQuestions}
            className="min-h-12 text-sm font-semibold text-primaire"
          >
            Voir les {groupage.questions} questions
          </button>
        ) : null}
        <button
          type="button"
          onClick={onQuestions}
          className={`inline-flex min-h-12 items-center gap-1.5 rounded-[10px] border-[1.5px] border-primaire px-4 text-sm font-semibold text-primaire ${
            groupage.questions > 0 ? "ml-auto" : ""
          }`}
        >
          <IconeQuestion taille={16} />
          {groupage.questions > 0
            ? "Poser une question"
            : "Posez la première question"}
        </button>
      </div>
    </section>
  );

  /* ── Ordinateur : fiche produit en deux colonnes ─────────────────────── */
  if (estBureau) {
    return (
      <>
        <div className="largeur-page py-6">
          <nav aria-label="Fil d'Ariane" className="mb-5">
            <button
              type="button"
              onClick={onRetour}
              className="inline-flex min-h-12 items-center gap-1 text-sm font-medium text-texte-secondaire hover:text-primaire"
            >
              <IconeRetour taille={18} />
              Tous les groupages
            </button>
          </nav>

          {/*
            ⚠️ **La galerie est a gauche et elle reste a l'ecran.**

            L'ordre du document suit l'ordre visuel : la galerie d'abord, donc
            a gauche. Entre 768 et 1 023 px — la tablette, ou cet ecran
            s'empile en colonne — elle passe naturellement en tete, comme sur
            telephone : c'est la photo que l'acheteur a vue sur la carte, et la
            retrouver en premier confirme qu'il a ouvert le bon produit.

            `items-start` n'est pas decoratif : sans lui, un element de flex
            s'etire sur toute la hauteur de la rangee, et `sticky` n'a plus
            aucune place pour glisser — il ne se passe simplement rien.
          */}
          <div className="flex flex-col gap-8 lg:flex-row lg:items-start lg:gap-12">
            <div className="w-full lg:sticky lg:top-24 lg:w-[46%] lg:max-w-xl lg:shrink-0">
              {media}
            </div>

            {/* Tout ce qui se lit defile de ce cote.

                ⚠️ **Plafonne a `max-w-2xl`.** Le conteneur monte a 1 600 px et
                la galerie en prend 576 : sans ce plafond, la colonne de
                lecture recevait pres de 880 px, et une ligne de texte de cette
                longueur se perd — l'oeil ne retrouve pas le debut de la
                suivante. */}
            <div className="min-w-0 flex-1 space-y-10 lg:max-w-2xl">
              <div className="space-y-5">
                {enTeteProduit}
                {contenuPart}
                {/* ⚠️ **La description passe avant le bouton.** Elle etait
                    sous le bloc d'achat : on demandait de commander avant
                    d'avoir dit ce qu'on vend. Repliee a quatre lignes, avec
                    « Voir plus » — elle informe sans repousser le bouton hors
                    de l'ecran. */}
                {description}
                {/* ⚠️ **On ne commande pas un groupage cloture.** Le
                    bouton restait actif, et il menait a un paiement que le
                    serveur refuse — l'acheteur remplissait son adresse pour
                    rien. La fiche d'un groupage cloture reste atteignable par
                    son lien (ecran 2), donc ce cas se voit pour de vrai. */}
                {cloture ? (
                  <Bouton desactive>Groupage clôturé</Bouton>
                ) : (
                  <Bouton onClick={onCommander}>
                    Commander — {formaterFrancs(groupage.prixPart)}
                  </Bouton>
                )}
                <Bouton style="secondaire" onClick={onPartager}>
                  <IconePartager taille={18} />
                  Partager ce groupage
                </Bouton>
              </div>

              {/* ⚠️ **Le detail etait sous la fiche, sur deux colonnes.** Il
                  remonte dans cette colonne-ci, et c'est tout l'interet de la
                  galerie collee : on lit la description, les caracteristiques,
                  la livraison, les regles et les questions **sans perdre la
                  photo de vue**. Deux colonnes de texte sous une galerie qui a
                  defile obligeaient a remonter pour revoir le produit. */}
              {caracteristiques}
              {livraison}
              {regles}
              {questions}
            </div>
          </div>
        </div>

        {/* ⚠️ **Apres la fiche, et pleine largeur.** La suite de lecture est
            finie : la galerie collee se decolle, et on propose autre chose.
            Pose en dehors de la colonne de lecture, sinon la grille
            n'occuperait que 672 px au milieu de la page. */}
        {similaires.length > 0 && onOuvrirGroupage ? (
          <section className="largeur-page border-t border-filet pt-10 pb-4 lg:pt-14">
            <h2 className="text-2xl font-semibold tracking-tight text-texte">
              Dans la même catégorie
            </h2>
            <p className="mt-1 text-texte-secondaire">
              D&apos;autres groupages ouverts, livrés par le même service.
            </p>
            <ul className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-3 lg:gap-6 xl:grid-cols-4">
              {similaires.map((autre) => (
                <CarteGroupage
                  key={autre.id}
                  groupage={autre}
                  onOuvrir={onOuvrirGroupage}
                />
              ))}
            </ul>
          </section>
        ) : null}

        <PiedPage />

        {/*
          ⚠️ **Le bouton flottant manquait sur ordinateur.** Il n'existait
          que dans la branche telephone : sur grand ecran, le seul acces aux
          questions etait un bouton perdu au milieu de la fiche, qu'il fallait
          avoir fait defiler jusqu'a lui.

          Il se pose maintenant dans l'angle et **suit le defilement**, comme
          l'assistance d'une place de marche. Un clic ouvre le panneau juste
          au-dessus de lui, sans quitter la fiche — on pose une question parce
          qu'on hesite a commander, remplacer le produit par un formulaire est
          le mauvais geste a cet instant.
        */}
        {questionsOuvertes ? null : (
          <button
            type="button"
            onClick={onQuestions}
            className="fixed right-6 bottom-6 z-20 inline-flex h-12 items-center gap-2 rounded-full bg-primaire px-5 text-sm font-semibold text-white shadow-[0_4px_16px_rgba(29,25,22,0.24)] hover:bg-primaire-presse"
          >
            <IconeQuestion taille={18} />
            Poser une question
          </button>
        )}
      </>
    );
  }

  /* ── Telephone et tablette : une colonne, bouton ancre ───────────────── */
  return (
    <div className="pb-28">
      <header className="sticky top-0 z-10 flex h-14 items-center gap-1 border-b border-filet bg-white px-2">
        <button
          type="button"
          onClick={onRetour}
          aria-label="Retour"
          className="flex size-12 items-center justify-center text-texte"
        >
          <IconeRetour />
        </button>
        <h1 className="text-lg font-semibold text-texte">Détail du groupage</h1>
      </header>

      {media}

      <div className="space-y-6 px-4 pt-5">
        {enTeteProduit}
        {contenuPart}
        {/* ⚠️ Meme ordre que sur ordinateur : la description avant tout le
            reste. Le bouton de commande est ancre en bas de l'ecran, donc il
            reste atteignable quoi qu'il arrive. */}
        {description}
        {caracteristiques}
        {livraison}
        {regles}
        {questions}
      </div>

      {/* Une question est publique et filtree avant publication — ce n'est pas
          une messagerie privee.

          ⚠️ **Ce bouton flottant n'avait pas de `onClick` non plus**, et c'est
          celui qu'on voit le plus : il est fixe en bas de l'ecran pendant tout
          le defilement de la fiche. */}
      <button
        type="button"
        onClick={onQuestions}
        className="fixed right-4 bottom-24 z-10 inline-flex h-11 items-center gap-1.5 rounded-full bg-primaire px-4 text-sm font-semibold text-white shadow-[0_2px_10px_rgba(29,25,22,0.2)]"
      >
        <IconeQuestion taille={16} />
        Posez une question
      </button>

      {/* Son montant est le prix de la part, pas le total : le total n'existe
          qu'une fois la position connue. */}
      <BoutonAncre>
        {cloture ? (
          <Bouton desactive>Groupage clôturé</Bouton>
        ) : (
          <Bouton onClick={onCommander}>
            Commander — {formaterFrancs(groupage.prixPart)}
          </Bouton>
        )}
      </BoutonAncre>
    </div>
  );
}
