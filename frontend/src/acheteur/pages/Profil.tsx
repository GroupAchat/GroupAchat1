import { useState } from "react";
import { LIBELLE_QUARTIER, QUARTIERS, type Quartier } from "../../domaine/groupage";
import {
  ecrireEconomieDonnees,
  lireEconomieDonnees,
} from "../../domaine/profil";
import {
  completerMonProfil,
  deconnecterTousLesAppareils,
  definirLeMotDePasse,
  supprimerMonCompte,
  type Profil as ProfilCompte,
} from "../../api/session";
import { ErreurApi } from "../../api/client";
import EnTeteEcran from "../mise-en-page/EnTeteEcran";
import PiedPage from "../mise-en-page/PiedPage";
import Bouton from "../../ui/Bouton";
import Champ from "../../ui/Champ";
import Encart from "../../ui/Encart";
import EtatVide from "../../ui/EtatVide";
import {
  IconeBouclier,
  IconeCarton,
  IconeProfil,
  IconeAlerte,
  IconeChevronDroit,
  IconeCommandes,
  IconeTelephone,
  IconeVerrou,
} from "../../ui/Icones";

/**
 * Onglet Profil — SPEC_ECRANS_FIGMA.md, ecran 1, « Les onglets, a definir
 * maintenant » : *« Mes informations, mes demandes, mode economie de donnees,
 * aide »*, rattache a « 12 et reglages ».
 *
 * C'est le quatrieme onglet de `BarreNav`, et jusqu'ici il renvoyait vers
 * l'ecran 12 faute d'exister.
 *
 * ## Les quatre blocs, et pourquoi dans cet ordre
 *
 * | Bloc | Ce qu'il porte |
 * |---|---|
 * | Mes informations | Nom, numero, adresse de livraison par defaut |
 * | Mes demandes | Le lien vers l'ecran 12 |
 * | Economie de donnees | La bascule du §1.6 regle 4 |
 * | Aide | Les trois promesses, redites la ou on les cherche |
 *
 * ## ⚠️ Deux etats, et aucun n'est un mur (§1.5)
 *
 * Un visiteur qui touche cet onglet **ne voit pas une invitation a se
 * connecter en travers de l'ecran**. Il voit le patron impose par le §1.5 —
 * un titre, une explication, « Voir les campagnes », et en lien discret « J'ai
 * deja un compte — me connecter ».
 *
 * ⚠️ **Mais la bascule economie de donnees reste au-dessus de cet etat
 * vide**, et c'est delibere. C'est une preference d'appareil, stockee en
 * local, qui n'a besoin d'aucun compte (voir `domaine/profil.ts`) : le
 * visiteur qui fait defiler le fil sans s'etre connecte est **exactement**
 * celui a qui le §1.6 la destine. La placer derriere le compte reviendrait a
 * la refuser a son premier public.
 *
 * ## ⚠️ Ce que cet ecran ne contient pas
 *
 * **Aucun profil de groupeur, aucun moyen d'en joindre un** : §1.7 et §7
 * regle 4 du cahier des charges l'interdisent, et c'est ce qui protege la
 * nous. Le pseudonyme n'est cliquable nulle part, ici pas davantage.
 *
 * **Pas de canal d'assistance.** Le bloc d'aide redit les regles du produit,
 * il ne promet ni numero, ni adresse, ni formulaire : le cahier des charges ne
 * tranche pas encore le canal du support. Inventer un contact serait pire que
 * de ne rien afficher.
 */
export default function Profil({
  estBureau,
  connecte,
  profil,
  onCreerUnCompte,
  onMesCommandes,
  onMesDemandes,
  onDemanderProduit,
  onSeConnecter,
  onProfilMisAJour,
  onSeDeconnecter,
}: {
  estBureau: boolean;
  connecte: boolean;
  /** Absent tant que la reconnexion automatique n'a pas repondu (§ `api/session`). */
  profil?: ProfilCompte;
  onCreerUnCompte: () => void;
  onMesCommandes: () => void;
  onMesDemandes: () => void;
  onDemanderProduit: () => void;
  onSeConnecter: () => void;
  onProfilMisAJour: (profil: ProfilCompte) => void;
  onSeDeconnecter: () => void;
}) {
  /* Lu une seule fois au montage : `lireEconomieDonnees` touche
     `localStorage`, et le relire a chaque rendu serait un acces disque par
     frappe pour une valeur qui ne change qu'ici. */
  const [economie, setEconomie] = useState(lireEconomieDonnees);

  const basculerEconomie = () => {
    const suivant = !economie;
    setEconomie(suivant);
    ecrireEconomieDonnees(suivant);
  };

  /**
   * **Les blocs sont groupes en deux familles, et c'est ce qui rend la page
   * reponsive sans la dupliquer.**
   *
   * | Famille | Blocs | Ce qu'on y fait |
   * |---|---|---|
   * | Le compte | Mes informations, Mes demandes | On consulte, on corrige |
   * | Les reglages | Economie de donnees, Aide, Deconnexion | On y touche une fois |
   *
   * La distinction n'est pas esthetique : au-dela de 1 280 px les deux
   * familles tiennent cote a cote, en dessous elles s'empilent dans cet
   * ordre. **Un seul jeu de blocs sert les deux cas** — rien n'est monte deux
   * fois, donc rien ne peut diverger entre le telephone et l'ordinateur.
   */
  const blocsCompte = (
    <>
      <BlocInformations profil={profil} onProfilMisAJour={onProfilMisAJour} />
      {/* Juste après les informations, et avant les demandes : c'est le compte
          lui-même, pas un réglage d'affichage. */}
      <BlocMotDePasse profil={profil} onProfilMisAJour={onProfilMisAJour} />
      <BlocActivite
        onMesCommandes={onMesCommandes}
        onMesDemandes={onMesDemandes}
        onDemanderProduit={onDemanderProduit}
      />
    </>
  );

  const blocsReglages = (
    <>
      <BlocEconomieDonnees actif={economie} onBasculer={basculerEconomie} />
      <BlocAide />
      <BlocAppareils onSeDeconnecter={onSeDeconnecter} />
    </>
  );

  /**
   * L'état vide de l'onglet, pour un visiteur sans compte.
   *
   * ⚠️ **Il disait : « votre compte se crée au moment de payer ».** C'était
   * vrai, ça ne l'est plus — le compte se crée par un formulaire, et il est
   * demandé avant de rejoindre un groupage ou de poser une question. Une
   * phrase d'interface qui décrit un parcours disparu est pire qu'une phrase
   * absente : elle fait chercher un chemin qui n'existe pas.
   *
   * L'action proposée a changé avec elle. « Voir les campagnes » avait un sens
   * quand le compte naissait du paiement : on renvoyait l'acheteur là où le
   * compte se créerait tout seul. Aujourd'hui le chemin direct existe, et
   * l'envoyer au catalogue serait un détour.
   */
  const etatVide = (
    <EtatVide
      titre="Créez votre compte"
      explication="Vos commandes, vos codes de livraison et vos demandes de produits, au même endroit et sur tous vos appareils."
      actionLibelle="Créer mon compte"
      registre="attente"
      onAction={onCreerUnCompte}
      lienSecondaire={{
        libelle: "J'ai déjà un compte — me connecter",
        onClick: onSeConnecter,
      }}
    />
  );

  if (!estBureau) {
    return (
      /* `pb-18` : la barre de navigation du bas mesure `h-18` et flotte
         au-dessus du contenu. Sans cette reserve, le bloc de deconnexion —
         le dernier — passe dessous et devient inatteignable. */
      <div className="pb-18">
        <EnTeteEcran titre="Profil" />
        <div className="space-y-4 px-4 py-4">
          {connecte ? <CarteIdentite profil={profil} /> : null}
          {connecte ? blocsCompte : null}
          {blocsReglages}
          {connecte ? (
            <>
              <BlocDeconnexion onSeDeconnecter={onSeDeconnecter} />
              <BlocSupprimerCompte onSeDeconnecter={onSeDeconnecter} />
            </>
          ) : (
            /* \u26a0\ufe0f **Apres la bascule, et c'est delibere** : l'economie de
               donnees est une preference d'appareil qui ne demande aucun
               compte. La mettre sous l'etat vide la ferait passer pour une
               fonction reservee aux inscrits. */
            etatVide
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="largeur-page py-8 lg:py-10">
        <header
          className={`${CADRE} flex flex-wrap items-end justify-between gap-x-6 gap-y-4`}
        >
          <div className="min-w-0">
            <h1 className="font-titre text-2xl font-semibold tracking-tight text-texte lg:text-3xl">
              Mon profil
            </h1>
            <p className="mt-1 text-texte-secondaire">
              Vos informations de livraison, vos demandes, et la fa\u00e7on dont le
              site consomme vos donn\u00e9es.
            </p>
          </div>
          {connecte ? (
            /* `pleineLargeur={false}` : le bouton faisait 320 px de large pour
               trois mots, parce qu'il etait enferme dans un `w-full max-w-xs`.
               A cote d'un titre, il doit prendre la largeur de son libelle. */
            <Bouton
              style="secondaire"
              pleineLargeur={false}
              onClick={onDemanderProduit}
            >
              Demander un produit
            </Bouton>
          ) : null}
        </header>

        {connecte ? (
          <>
            <div className={`${CADRE} mt-6`}>
              <CarteIdentite profil={profil} />
            </div>

            <div
              className={`${CADRE} mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem] xl:items-start`}
            >
              <div className="space-y-6">{blocsCompte}</div>

              {/* \u26a0\ufe0f **`xl:items-start` sur la grille est ce qui fait tenir
                  le `sticky` ci-dessous.** Un element de grille s'etire par
                  defaut sur toute la hauteur de sa rangee : la colonne
                  laterale mesurerait alors exactement la hauteur du
                  formulaire, elle n'aurait aucune marge pour glisser, et le
                  `sticky` ne produirait rien du tout.

                  `top-24` et non `top-0` : l'en-tete de bureau est collant et
                  mesure 80 px plus son filet. Colle a 0, la colonne passerait
                  dessous. */}
              <aside className="space-y-6 xl:sticky xl:top-24">
                {blocsReglages}
                <BlocDeconnexion onSeDeconnecter={onSeDeconnecter} />
                <BlocSupprimerCompte onSeDeconnecter={onSeDeconnecter} />
              </aside>
            </div>
          </>
        ) : (
          /* Un visiteur sans compte n'a que deux blocs et un etat vide : une
             grille a deux colonnes pour si peu laisserait une moitie d'ecran
             vide. Une seule colonne, et l'ordre du \u00a71.5 est preserve —
             la bascule, puis l'aide, puis l'invitation. */
          <div className={`${CADRE} mt-6 space-y-6`}>
            {blocsReglages}
            {etatVide}
          </div>
        )}
      </div>
      <PiedPage />
    </>
  );
}

/**
 * \u26a0\ufe0f **Deux largeurs, un seul point de rupture — et il est a `xl`,
 * 1 280 px, pas a `md`.**
 *
 * Le defaut repare ici etait mesurable : la page etait plafonnee a
 * `max-w-2xl`, soit **672 px, calee a gauche**. Sur un ecran de 1 920 il
 * restait donc plus de 900 px de vide a droite, pendant que l'en-tete et le
 * pied, eux, allaient d'un bord a l'autre. C'est exactement le defaut que le
 * \u00a71.3 de la spec des ecrans raconte pour la fiche produit et les commandes,
 * reste en place sur le profil.
 *
 * | Largeur | Ce qu'on voit |
 * |---|---|
 * | < 768 | Une colonne, en-tete d'ecran, barre du bas |
 * | 768 a 1 279 | Une colonne **centree** de 672 px |
 * | \u2265 1 280 | Formulaire ~776 px + colonne de reglages 352 px, collante |
 *
 * 672 px pour un formulaire n'est pas une limite arbitraire : au-dela, un
 * libelle a gauche et sa valeur a droite finissent separes par tant de blanc
 * qu'on ne les lit plus comme une paire — c'est ce que font les lignes de
 * `Ligne` ci-dessous. Le probleme n'etait donc pas la largeur de la colonne,
 * c'etait qu'elle ne soit **pas centree** et qu'aucune seconde colonne ne
 * vienne occuper la place des qu'elle existe.
 */
const CADRE = "mx-auto w-full max-w-2xl xl:max-w-6xl";

/* \u2500\u2500 La carte d'identite \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */

/**
 * « mars 2026 » a partir d'une date ISO.
 *
 * `Intl` plutôt qu'un tableau de mois écrit à la main : la locale `fr-FR`
 * connait deja les noms, les accents et les elisions, et un tableau maison
 * serait une seconde liste a tenir a jour pour rien.
 *
 * ⚠️ **Une date invalide ne doit pas casser la carte.** Le serveur la
 * fournit toujours, mais un profil lu depuis un cache ancien pourrait ne pas
 * l'avoir : on rend alors une chaine vide plutot qu'un « Invalid Date ».
 */
function moisEtAnnee(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("fr-FR", {
    month: "long",
    year: "numeric",
  }).format(date);
}

/**
 * Qui je suis, en un coup d'oeil : une initiale, un nom, un numero.
 *
 * \u26a0\ufe0f **Ce n'est pas une photo de profil, et il n'en faut pas.** Le \u00a71.7
 * interdit tout profil public et tout moyen de joindre quelqu'un ; une page de
 * profil acheteur qui ressemble a un reseau social invite a y chercher les
 * autres. Une initiale sur une pastille dit \u00ab c'est bien ton compte \u00bb et
 * s'arrete la.
 *
 * **L'initiale est en `primaire-texte-sur-fond` sur `primaire-fond`, soit
 * 4,87:1** — au-dessus du seuil de 4,5:1. C'est calcule, pas estime. La
 * pastille n'est pas en `primaire` plein : un disque orange vif de 56 px en
 * haut d'une page deja coiffee d'un en-tete orange faisait un second aplat de
 * marque a trois centimetres du premier.
 */
function CarteIdentite({ profil }: { profil?: ProfilCompte }) {
  /* Pas de squelette ici : `BlocInformations` en porte deja un juste en
     dessous, et deux zones qui pulsent pour une seule requete donnent
     l'impression que la page est cassee. */
  if (!profil) return null;

  const nom = profil.nom?.trim();
  /* `Array.from` et non `nom[0]` : une chaine indexee coupe au milieu d'un
     caractere code sur deux unites et rend un demi-symbole. */
  const initiale = nom ? Array.from(nom)[0].toUpperCase() : undefined;

  return (
    <section className="flex items-center gap-4 rounded-xl border border-bordure p-4">
      <span
        aria-hidden="true"
        className="flex size-14 shrink-0 items-center justify-center rounded-full bg-primaire-fond text-xl font-semibold text-primaire-texte-sur-fond"
      >
        {/* Sans nom renseigne, une icone plutot qu'un \u00ab ? \u00bb : un point
            d'interrogation en guise d'avatar donne l'air de ne pas savoir a
            qui on parle. */}
        {initiale ?? <IconeProfil taille={26} />}
      </span>

      <div className="min-w-0">
        {/* `truncate` : un nom long ne doit pas pousser le numero hors de la
            carte sur un ecran de 320 px. */}
        <p className="truncate font-titre text-lg font-semibold text-texte">
          {nom || "Votre compte"}
        </p>
        <p className="mt-0.5 flex items-center gap-1.5 text-sm text-texte-secondaire">
          <IconeTelephone taille={16} />
          {profil.telephone}
        </p>
        {/* « Membre depuis » : la date était en base depuis le début et
            n'avait jamais été servie. Elle dit à l'acheteur que son compte a
            une histoire — c'est peu, et c'est ce qui distingue un compte d'un
            formulaire. En `texte-mention`, 4,86:1 sur blanc : une mention,
            pas une information dont dépend une décision. */}
        <p className="mt-0.5 text-xs text-texte-mention">
          Membre depuis {moisEtAnnee(profil.cree_le)}
        </p>
      </div>
    </section>
  );
}

/* ── Mes informations ────────────────────────────────────────────────────── */

/**
 * Nom, numero, adresse de livraison par defaut.
 *
 * ⚠️ **Le numero ne se modifie pas ici.** Il *est* l'identifiant du compte :
 * le changer serait changer de compte, ce qui demande un nouveau code SMS, pas
 * un champ de formulaire. La feuille de connexion (§ecran 4) est le seul
 * endroit ou un numero est etabli, et c'est ce qui garantit qu'il a ete prouve.
 *
 * ⚠️ **Modifier l'adresse ici ne touche aucune commande deja passee.** Le
 * livreur doit voir l'adresse qui valait au moment de la commande : la
 * position est conservee *sur la commande* (§6 du PRD), pas lue sur le compte.
 * Un demenagement ne doit pas derouter un colis en cours de livraison.
 */
function BlocInformations({
  profil,
  onProfilMisAJour,
}: {
  profil?: ProfilCompte;
  onProfilMisAJour: (profil: ProfilCompte) => void;
}) {
  const [edition, setEdition] = useState(false);
  const [nom, setNom] = useState(profil?.nom ?? "");
  const [courriel, setCourriel] = useState(profil?.courriel ?? "");
  const [quartier, setQuartier] = useState<Quartier | undefined>(
    profil?.quartier as Quartier | undefined,
  );
  const [repere, setRepere] = useState(profil?.repere ?? "");
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState<string>();

  if (!profil) {
    /* La reconnexion automatique n'a pas encore repondu. Un squelette plutot
       qu'un vide : l'onglet est deja ouvert, et afficher « aucune
       information » ferait croire le compte vide. */
    return (
      <Bloc titre="Mes informations" Icone={IconeProfil}>
        <div className="space-y-2" aria-hidden="true">
          <div className="h-4 w-32 animate-pulse rounded bg-surface-douce" />
          <div className="h-4 w-48 animate-pulse rounded bg-surface-douce" />
        </div>
        <p className="sr-only">Chargement de vos informations.</p>
      </Bloc>
    );
  }

  const enregistrer = () => {
    setEnvoi(true);
    setErreur(undefined);
    completerMonProfil({
      nom: nom.trim() || undefined,
      /* ⚠️ `?? undefined` plutôt que `|| undefined` serait faux ici : une
         chaîne vide **doit** partir, sinon on ne peut jamais effacer un
         courriel qu'on a renseigné par erreur. `completerMonProfil` n'ignore
         que les champs absents, pas les champs vides. */
      courriel: courriel.trim(),
      quartier,
      repere: repere.trim() || undefined,
    })
      .then((misAJour) => {
        onProfilMisAJour(misAJour);
        setEdition(false);
      })
      .catch((e: unknown) => {
        /* Le message du serveur s'il en donne un, sinon une phrase qui dit
           quoi faire. « Erreur 500 » n'aide personne a Lome. */
        setErreur(
          e instanceof ErreurApi && e.message
            ? e.message
            : "Vos informations n'ont pas pu être enregistrées. Vérifiez votre connexion et réessayez.",
        );
      })
      .finally(() => setEnvoi(false));
  };

  if (!edition) {
    return (
      <Bloc titre="Mes informations" Icone={IconeProfil}>
        <dl className="divide-y divide-bordure">
          <Ligne libelle="Nom" valeur={profil.nom || "Non renseigné"} />
          <Ligne libelle="Numéro" valeur={profil.telephone} />
          <Ligne
            libelle="Courriel"
            valeur={profil.courriel || "Non renseigné"}
          />
          <Ligne
            libelle="Livraison"
            valeur={
              profil.quartier
                ? `${LIBELLE_QUARTIER[profil.quartier as Quartier] ?? profil.quartier}${
                    profil.repere ? ` — ${profil.repere}` : ""
                  }`
                : "Non renseignée"
            }
          />
        </dl>
        <div className="mt-4 max-w-xs">
          <Bouton style="secondaire" onClick={() => setEdition(true)}>
            Modifier
          </Bouton>
        </div>
      </Bloc>
    );
  }

  return (
    <Bloc titre="Mes informations" Icone={IconeProfil}>
      <div className="space-y-4">
        <Champ
          libelle="Nom"
          valeur={nom}
          onChanger={setNom}
          exemple="Akosua Doe"
          aide="Il n'est montré qu'au livreur, le jour de la livraison."
        />

        <Champ
          libelle="Courriel (facultatif)"
          valeur={courriel}
          onChanger={setCourriel}
          type="email"
          inputMode="email"
          autoComplete="email"
          exemple="akosua@example.tg"
          aide="Facultatif. Nous ne nous en servons pas pour vous reconnaître : c'est votre numéro qui identifie votre compte."
        />

        {/* Le numero est affiche, jamais modifiable : voir l'en-tete. */}
        <div>
          <p className="text-sm font-medium text-texte">Numéro</p>
          <p className="mt-1 flex items-center gap-2 text-texte-secondaire">
            <IconeTelephone taille={18} />
            {profil.telephone}
          </p>
          <p className="mt-1 text-sm text-texte-secondaire">
            Il identifie votre compte. Pour en changer, connectez-vous avec le
            nouveau numéro.
          </p>
        </div>

        <div>
          <p className="text-sm font-medium text-texte">Quartier de livraison</p>
          {/* Les memes pastilles qu'aux ecrans 5 et 11 : une liste fermee,
              parce que les frais de livraison se calculent par quartier
              (§11.1) et qu'un champ libre ne se calcule pas. */}
          <div className="mt-2 flex flex-wrap gap-2">
            {QUARTIERS.map((unQuartier) => {
              const choisi = unQuartier === quartier;
              return (
                <button
                  key={unQuartier}
                  type="button"
                  aria-pressed={choisi}
                  onClick={() => setQuartier(unQuartier)}
                  className={`inline-flex min-h-12 items-center rounded-full px-4 text-sm font-medium ${
                    choisi
                      ? "bg-primaire text-white"
                      : "bg-surface-douce text-texte"
                  }`}
                >
                  {LIBELLE_QUARTIER[unQuartier]}
                </button>
              );
            })}
          </div>
        </div>

        <Champ
          libelle="Repère"
          valeur={repere}
          onChanger={setRepere}
          exemple="En face de la pharmacie du marché"
          aide="À Lomé, le repère vaut plus que la coordonnée : c'est lui que le livreur cherche."
        />

        {erreur ? <Encart variante="danger">{erreur}</Encart> : null}

        <div className="flex flex-wrap gap-3">
          <div className="min-w-40 flex-1">
            <Bouton onClick={enregistrer} chargement={envoi}>
              Enregistrer
            </Bouton>
          </div>
          <div className="min-w-32 flex-1">
            <Bouton
              style="secondaire"
              desactive={envoi}
              onClick={() => {
                /* On remet les valeurs du compte : un abandon ne doit pas
                   laisser le formulaire a moitie modifie au prochain clic
                   sur « Modifier ». */
                setNom(profil.nom ?? "");
                setCourriel(profil.courriel ?? "");
                setQuartier(profil.quartier as Quartier | undefined);
                setRepere(profil.repere ?? "");
                setErreur(undefined);
                setEdition(false);
              }}
            >
              Annuler
            </Bouton>
          </div>
        </div>
      </div>
    </Bloc>
  );
}

/* ── Le mot de passe ─────────────────────────────────────────────────────── */

/**
 * Définir un mot de passe, ou en changer.
 *
 * ## ⚠️ Pourquoi c'est **ici** et pas dans la feuille de connexion
 *
 * Le compte acheteur n'est plus « un truc de code SMS », mais le parcours
 * d'achat n'a pas gagné un champ pour autant, et c'est délibéré : le §1.5
 * interdit d'alourdir le chemin vers le paiement, et chaque champ posé devant
 * quelqu'un qui s'apprête à payer est un acheteur perdu. Le mot de passe se
 * pose donc **plus tard, ici, quand plus rien n'est en jeu** — et il sert à la
 * visite suivante, depuis un autre appareil.
 *
 * | État | Bouton | Ce qui est demandé |
 * |---|---|---|
 * | Aucun | « Définir un mot de passe » | Le nouveau, deux fois |
 * | Il y en a un | « Modifier » | **L'actuel**, puis le nouveau deux fois |
 *
 * ⚠️ **L'actuel est exigé, et il faut résister à l'envie de s'en passer.** La
 * session est déjà ouverte, donc techniquement elle suffirait. Mais le jeton
 * vit dans le `localStorage` et survit à la fermeture de l'onglet : la
 * différence est celle entre **voir** les commandes de quelqu'un et **lui
 * prendre son compte définitivement**. Sans l'actuel, un téléphone prêté cinq
 * minutes suffit à verrouiller son propriétaire dehors pour de bon. Le serveur
 * l'exige de son côté ; ce formulaire ne fait que le demander avant de se
 * faire refuser.
 *
 * ⚠️ **Il n'y a pas de « mot de passe oublié » à écrire.** Le code SMS ouvre
 * le compte de tout le monde et **lève le verrou** des cinq échecs : c'est la
 * voie de récupération, elle existe déjà, et elle ne demande ni lien à durée
 * de vie ni courriel — qui est facultatif sur ce marché.
 */
function BlocMotDePasse({
  profil,
  onProfilMisAJour,
}: {
  profil?: ProfilCompte;
  onProfilMisAJour: (profil: ProfilCompte) => void;
}) {
  const [ouvert, setOuvert] = useState(false);
  const [actuel, setActuel] = useState("");
  const [nouveau, setNouveau] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [erreurActuel, setErreurActuel] = useState<string>();
  const [erreurNouveau, setErreurNouveau] = useState<string>();
  const [erreur, setErreur] = useState<string>();

  /* Même raison que dans `BlocInformations` : la reconnexion automatique n'a
     pas répondu, et on ne sait pas encore s'il faut écrire « Définir » ou
     « Modifier ». Rien plutôt qu'une proposition fausse — contrairement aux
     informations, il n'y a ici aucune donnée à faire patienter, donc pas de
     squelette non plus. */
  if (!profil) return null;

  const existe = profil.a_un_mot_de_passe;

  const fermer = () => {
    setOuvert(false);
    setActuel("");
    setNouveau("");
    setConfirmation("");
    setErreurActuel(undefined);
    setErreurNouveau(undefined);
    setErreur(undefined);
  };

  const enregistrer = () => {
    setErreurActuel(undefined);
    setErreurNouveau(undefined);
    setErreur(undefined);

    /* ⚠️ **La confirmation est vérifiée ici, et seulement ici.** Le serveur ne
       la reçoit pas, et c'est normal : ce n'est pas une règle de sécurité mais
       une protection contre la faute de frappe, et un champ masqué tapé une
       seule fois est la façon ordinaire de se verrouiller dehors. Toutes les
       autres règles — longueur, numéro interdit, mot de passe actuel — sont
       vérifiées par le serveur, parce qu'un contrôle qui ne vit que dans
       l'écran se contourne par un appel direct. */
    if (nouveau !== confirmation) {
      setErreurNouveau("Les deux saisies ne sont pas identiques.");
      return;
    }

    setEnvoi(true);
    definirLeMotDePasse({
      mot_de_passe: nouveau,
      ...(existe ? { ancien_mot_de_passe: actuel } : {}),
    })
      .then((misAJour) => {
        onProfilMisAJour(misAJour);
        fermer();
      })
      .catch((e: unknown) => {
        if (e instanceof ErreurApi && e.estRefusDeSaisie) {
          /* Le serveur répond champ par champ, et les deux ne mènent pas au
             même endroit : « mot de passe actuel incorrect » se corrige dans
             la première case, « trop court » dans la seconde. Les mêler dans
             un message unique laisserait chercher laquelle reprendre. */
          setErreurActuel(e.champs.ancien_mot_de_passe?.[0]);
          setErreurNouveau(e.champs.mot_de_passe?.[0]);
          if (!e.champs.ancien_mot_de_passe && !e.champs.mot_de_passe) {
            setErreur(e.messageLisible);
          }
          return;
        }
        setErreur(
          e instanceof ErreurApi
            ? e.messageLisible
            : "Votre mot de passe n'a pas pu être enregistré. Vérifiez votre connexion et réessayez.",
        );
      })
      .finally(() => setEnvoi(false));
  };

  if (!ouvert) {
    return (
      <Bloc titre="Mot de passe" Icone={IconeVerrou}>
        <p className="text-texte-secondaire">
          {existe
            ? "Vous pouvez vous connecter avec votre mot de passe, sans attendre de SMS."
            : "Définissez-en un pour vous reconnecter sans attendre de SMS. Le code par SMS continuera de fonctionner."}
        </p>
        <div className="mt-4 max-w-xs">
          <Bouton style="secondaire" onClick={() => setOuvert(true)}>
            {existe ? "Modifier" : "Définir un mot de passe"}
          </Bouton>
        </div>
      </Bloc>
    );
  }

  return (
    <Bloc titre="Mot de passe" Icone={IconeVerrou}>
      <div className="space-y-4">
        {existe ? (
          <Champ
            libelle="Mot de passe actuel"
            valeur={actuel}
            onChanger={setActuel}
            type="password"
            autoComplete="current-password"
            erreur={erreurActuel}
            autoFocus
          />
        ) : null}

        <Champ
          libelle="Nouveau mot de passe"
          valeur={nouveau}
          onChanger={setNouveau}
          type="password"
          /* `new-password` : c'est ce qui fait proposer un mot de passe fort
             par le gestionnaire, au lieu de re-proposer l'ancien. */
          autoComplete="new-password"
          erreur={erreurNouveau}
          aide="Au moins 8 caractères. Votre numéro de téléphone ne peut pas servir de mot de passe."
          autoFocus={!existe}
        />

        <Champ
          libelle="Confirmez le nouveau mot de passe"
          valeur={confirmation}
          onChanger={setConfirmation}
          type="password"
          autoComplete="new-password"
        />

        {erreur ? <Encart variante="danger">{erreur}</Encart> : null}

        <div className="flex flex-wrap gap-3">
          <div className="min-w-40 flex-1">
            <Bouton
              onClick={enregistrer}
              chargement={envoi}
              desactive={
                nouveau === "" ||
                confirmation === "" ||
                (existe && actuel === "")
              }
            >
              Enregistrer
            </Bouton>
          </div>
          <div className="min-w-32 flex-1">
            <Bouton style="secondaire" desactive={envoi} onClick={fermer}>
              Annuler
            </Bouton>
          </div>
        </div>
      </div>
    </Bloc>
  );
}

/* ── Economie de donnees ─────────────────────────────────────────────────── */

/**
 * La bascule du §1.6 regle 4.
 *
 * Un vrai `<input type="checkbox">`, pas un `<div>` avec un `onClick` : la
 * tabulation doit l'atteindre et un lecteur d'ecran doit annoncer son etat.
 * L'apparence d'interrupteur est posee par-dessus en CSS.
 */
function BlocEconomieDonnees({
  actif,
  onBasculer,
}: {
  actif: boolean;
  onBasculer: () => void;
}) {
  return (
    <Bloc titre="Économie de données" Icone={IconeCarton}>
      <label className="flex cursor-pointer items-start gap-4">
        <span className="min-w-0 flex-1">
          <span className="block font-medium text-texte">
            Images seulement, aucune vidéo
          </span>
          <span className="mt-1 block text-sm text-texte-secondaire">
            Le fil affiche la photo de couverture et ne charge aucune vidéo. Les
            logos des partenaires cèdent la place à du texte. À garder activé
            sur un forfait limité.
          </span>
        </span>

        <input
          type="checkbox"
          checked={actif}
          onChange={onBasculer}
          className="peer sr-only"
        />
        {/* La piste et la pastille.
            ⚠️ L'apparence est pilotee par `actif`, l'etat React, et **pas**
            par `peer-checked:`. Le modificateur `peer-*` de Tailwind produit
            un selecteur de freres (`~`) : il atteint la piste, qui est bien
            un frere de la case, mais **jamais la pastille**, qui en est un
            descendant. Ecrite en `peer-checked:`, elle ne se deplacerait
            donc pas. `peer-focus-visible` reste, lui, sur la piste — ou il
            fonctionne. */}
        <span
          aria-hidden="true"
          className={`relative mt-1 h-7 w-12 shrink-0 rounded-full transition-colors peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primaire ${
            actif ? "bg-primaire" : "bg-bordure"
          }`}
        >
          <span
            className={`absolute top-1 left-1 size-5 rounded-full bg-white transition-transform ${
              actif ? "translate-x-5" : ""
            }`}
          />
        </span>
      </label>
    </Bloc>
  );
}

/* ── Mon activite ────────────────────────────────────────────────────────── */

/**
 * Les raccourcis vers ce que l'acheteur a fait sur la plateforme.
 *
 * ⚠️ **Ce bloc remplace « Mes demandes », qui était seul.** Les commandes
 * n'étaient atteignables que par la barre de navigation du bas — qui
 * **n'existe pas sur ordinateur**. Un visiteur de bureau n'avait donc aucun
 * chemin vers ses commandes depuis son profil, alors que c'est exactement là
 * qu'on les cherche.
 */
function BlocActivite({
  onMesCommandes,
  onMesDemandes,
  onDemanderProduit,
}: {
  onMesCommandes: () => void;
  onMesDemandes: () => void;
  onDemanderProduit: () => void;
}) {
  const liens: { libelle: string; description: string; onClick: () => void }[] =
    [
      {
        libelle: "Mes commandes",
        description: "Leur suivi, et vos codes de livraison",
        onClick: onMesCommandes,
      },
      {
        libelle: "Mes demandes",
        description: "Les produits demandés, et ceux repris en campagne",
        onClick: onMesDemandes,
      },
      {
        libelle: "Demander un produit",
        description: "Proposer un produit qu'aucun groupeur ne propose encore",
        onClick: onDemanderProduit,
      },
    ];

  return (
    <Bloc titre="Mon activité" Icone={IconeCommandes}>
      <ul className="divide-y divide-bordure">
        {liens.map(({ libelle, description, onClick }) => (
          <li key={libelle}>
            {/* `min-h-12` : la cible tactile de 48 px du §2.7. Une ligne de
                liste est le premier endroit où on l'oublie. */}
            <button
              type="button"
              onClick={onClick}
              className="flex min-h-12 w-full items-center gap-3 py-3 text-left first:pt-0 active:bg-surface-douce"
            >
              <span className="min-w-0 flex-1">
                <span className="block font-medium text-texte">{libelle}</span>
                <span className="mt-0.5 block text-sm text-texte-secondaire">
                  {description}
                </span>
              </span>
              <span aria-hidden="true" className="shrink-0 text-primaire">
                <IconeChevronDroit taille={18} />
              </span>
            </button>
          </li>
        ))}
      </ul>
    </Bloc>
  );
}

/* ── Mes appareils ───────────────────────────────────────────────────────── */

/**
 * Fermer les sessions ouvertes **partout**.
 *
 * ⚠️ **Ce n'est pas un doublon du bouton « Me déconnecter »**, et le
 * commentaire de ce dernier annonçait déjà ce manque : *« Une révocation
 * globale aurait sa place dans un écran mes appareils, qui n'existe pas
 * encore. »* Il existe maintenant, sous forme d'un bloc plutôt que d'un
 * écran — il n'y a qu'une action, et une page pour un bouton serait un
 * détour.
 *
 * | | Ce qu'on veut |
 * |---|---|
 * | « Me déconnecter » | Quitter **cet** appareil — celui d'un ami, un cyber |
 * | ici | Fermer **partout**, parce qu'on a perdu son téléphone |
 *
 * Les confondre ferait, dans un sens, déconnecter son propre téléphone en
 * quittant celui d'un ami ; dans l'autre, laisser une session ouverte sur un
 * appareil perdu.
 *
 * ⚠️ **La session courante meurt aussi**, donc l'écran traite ce retour comme
 * une déconnexion ordinaire. Épargner la session d'ici laisserait croire que
 * « tout » a été fermé alors que la plus proche reste ouverte.
 */
function BlocAppareils({ onSeDeconnecter }: { onSeDeconnecter: () => void }) {
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState<string>();

  const fermerPartout = () => {
    setEnvoi(true);
    setErreur(undefined);
    deconnecterTousLesAppareils()
      .then(() => onSeDeconnecter())
      .catch((e: unknown) => {
        setErreur(
          e instanceof ErreurApi
            ? e.messageLisible
            : "Les sessions n'ont pas pu être fermées. Vérifiez votre connexion et réessayez.",
        );
        setEnvoi(false);
      });
  };

  return (
    <Bloc titre="Mes appareils" Icone={IconeBouclier}>
      <p className="text-texte-secondaire">
        Vous restez connecté sur chaque appareil où vous vous êtes identifié.
        Si vous avez perdu votre téléphone, fermez-les tous.
      </p>

      {erreur ? (
        <div className="mt-3">
          <Encart variante="danger">{erreur}</Encart>
        </div>
      ) : null}

      <div className="mt-4 max-w-xs">
        <Bouton style="secondaire" chargement={envoi} onClick={fermerPartout}>
          Fermer toutes mes sessions
        </Bouton>
      </div>
      <p className="mt-2 text-sm text-texte-secondaire">
        Celle-ci comprise : vous devrez vous reconnecter.
      </p>
    </Bloc>
  );
}

/* ── Supprimer mon compte ────────────────────────────────────────────────── */

/**
 * La zone sensible, et la seule action irréversible de l'écran.
 *
 * ## ⚠️ Ce que « supprimer » veut dire ici, exactement
 *
 * Le serveur **anonymise**, il n'efface pas la ligne, et ce n'est ni un
 * raccourci ni une demi-mesure :
 *
 * - les **commandes sont protégées** (`on_delete=PROTECT`). Les effacer
 *   trouerait la comptabilité — montants collectés, frais retenus, retraits —
 *   dont les additions doivent continuer de tomber juste ;
 * - les **questions publiques** seraient emportées en cascade. On détruirait
 *   le fil qu'un groupeur a alimenté et que d'autres acheteurs lisent pour
 *   décider d'acheter : supprimer son compte ne doit pas effacer le contenu
 *   d'autrui.
 *
 * Ce qui disparaît vraiment : prénom, courriel, adresse, mot de passe, et
 * toutes les sessions. Le numéro est remplacé par une marque inerte — le
 * libérer permettrait à quelqu'un d'autre de s'inscrire avec et de récupérer
 * l'historique.
 *
 * **L'écran le dit**, et ne promet pas un effacement total qui n'aurait pas
 * lieu.
 *
 * ## La confirmation
 *
 * ⚠️ **Elle est ici et nulle part ailleurs** : le serveur exécute sans
 * redemander. C'est le bon partage — une confirmation est une affaire
 * d'interface, et un second appel « êtes-vous sûr » côté serveur ne
 * protégerait de rien puisqu'il suffirait de l'envoyer deux fois.
 *
 * Deux gestes, et le second n'est pas un simple « oui » : il faut **écrire le
 * mot**. Un bouton de confirmation se clique par réflexe ; une saisie oblige
 * à lire.
 */
const MOT_DE_CONFIRMATION = "SUPPRIMER";

function BlocSupprimerCompte({
  onSeDeconnecter,
}: {
  onSeDeconnecter: () => void;
}) {
  const [ouvert, setOuvert] = useState(false);
  const [saisie, setSaisie] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState<string>();

  const supprimer = () => {
    setEnvoi(true);
    setErreur(undefined);
    supprimerMonCompte()
      .then(() => onSeDeconnecter())
      .catch((e: unknown) => {
        setErreur(
          e instanceof ErreurApi
            ? e.messageLisible
            : "Votre compte n'a pas pu être supprimé. Vérifiez votre connexion et réessayez.",
        );
        setEnvoi(false);
      });
  };

  if (!ouvert) {
    return (
      <div className="pb-4">
        {/* En lien `danger` et non en bouton : c'est une sortie, pas une
            action qu'on propose. Un bouton plein rouge au bas d'un écran de
            réglages attire l'œil vers la seule chose irréversible. */}
        <button
          type="button"
          onClick={() => setOuvert(true)}
          className="min-h-12 text-sm font-medium text-danger"
        >
          Supprimer mon compte
        </button>
      </div>
    );
  }

  return (
    <section className="rounded-xl border border-danger p-4">
      <h2 className="flex items-center gap-2 font-semibold text-texte">
        <span className="text-danger">
          <IconeAlerte taille={20} />
        </span>
        Supprimer mon compte
      </h2>

      <div className="mt-3 space-y-3 text-sm text-texte-secondaire">
        <p>
          Vos informations personnelles sont effacées : prénom, courriel,
          adresse, et toutes vos sessions. Vous ne pourrez plus vous
          reconnecter avec ce numéro.
        </p>
        {/* ⚠️ On le dit plutôt que de laisser croire à un effacement total.
            Promettre plus que ce qu'on fait est pire que d'en faire moins. */}
        <p>
          <strong className="font-semibold text-texte">
            Vos commandes passées sont conservées
          </strong>{" "}
          sans votre nom : elles portent des montants déjà encaissés et des
          livraisons déjà faites. Vos questions publiques restent en ligne, car
          des groupeurs y ont répondu.
        </p>
        <p>Cette action est irréversible.</p>
      </div>

      <div className="mt-4">
        <Champ
          libelle={`Écrivez « ${MOT_DE_CONFIRMATION} » pour confirmer`}
          valeur={saisie}
          onChanger={setSaisie}
          exemple={MOT_DE_CONFIRMATION}
        />
      </div>

      {erreur ? (
        <div className="mt-3">
          <Encart variante="danger">{erreur}</Encart>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-3">
        <div className="min-w-40 flex-1">
          <Bouton
            style="danger-texte"
            chargement={envoi}
            desactive={saisie.trim().toUpperCase() !== MOT_DE_CONFIRMATION}
            onClick={supprimer}
          >
            Supprimer définitivement
          </Bouton>
        </div>
        <div className="min-w-32 flex-1">
          <Bouton
            style="secondaire"
            desactive={envoi}
            onClick={() => {
              setOuvert(false);
              setSaisie("");
              setErreur(undefined);
            }}
          >
            Annuler
          </Bouton>
        </div>
      </div>
    </section>
  );
}

/* ── Aide ────────────────────────────────────────────────────────────────── */

/**
 * Les trois promesses du produit, redites la ou on vient les chercher.
 *
 * Ce ne sont pas des textes d'habillage : chacun repond a une inquietude que
 * le §1 du cahier des charges documente, et chacun reprend la formulation
 * autorisee. ⚠️ « **detenu jusqu'a la cloture** », jamais « bloque jusqu'a la
 * livraison » — le groupeur est paye integralement a la cloture (§10.1), et le
 * tableau du §1.7 de la spec des ecrans interdit l'autre formulation.
 */
const AIDE: { question: string; reponse: string }[] = [
  {
    question: "Que devient mon argent avant la livraison ?",
    reponse:
      "Il va au portefeuille du groupeur, qui ne peut le retirer qu'à la clôture de la campagne — c'est à ce moment-là qu'il commande chez le fournisseur. Si la campagne n'aboutit pas, vous êtes remboursé intégralement.",
  },
  {
    question: "À quoi sert mon code de livraison ?",
    reponse:
      "Vous vérifiez la marchandise devant le livreur, puis vous lui donnez le code. Si ce n'est pas ce que vous avez commandé, vous refusez le colis.",
  },
  {
    question: "Pourquoi je ne vois qu'un pseudonyme de groupeur ?",
    reponse:
      "Les groupeurs sont sélectionnés un par un par Group Achat, et c'est à Group Achat que vous faites confiance, pas à eux. C'est aussi ce qui vous évite d'être démarché en privé.",
  },
  {
    question: "Que se passe-t-il si la campagne n'aboutit pas ?",
    reponse:
      "Vous êtes remboursé intégralement, frais de livraison compris. Une campagne se termine à sa date : elle peut aboutir même si l'objectif de participants n'est pas atteint.",
  },
  {
    question: "Combien coûte la livraison ?",
    reponse:
      "Elle n'est pas comprise dans le prix que vous payez ici : vous réglez votre part, et la livraison directement au livreur au moment de la remise. Le total affiché avant le paiement est donc le montant exact qui sera débité.",
  },
  {
    question: "Puis-je refuser le colis à la livraison ?",
    reponse:
      "Oui. Vous vérifiez la marchandise devant le livreur avant de lui donner votre code. Si ce n'est pas ce que vous avez commandé, vous refusez, et vous êtes remboursé.",
  },
  {
    question: "Mon numéro est-il communiqué au groupeur ?",
    reponse:
      "Jamais. Le groupeur ne voit qu'un code de livraison et un quartier — pas votre nom, pas votre numéro, pas votre adresse. Seul le livreur les connaît, le jour de la remise.",
  },
];

function BlocAide() {
  return (
    <Bloc titre="Aide" Icone={IconeBouclier}>
      <dl className="divide-y divide-bordure">
        {AIDE.map(({ question, reponse }) => (
          <div key={question} className="py-3 first:pt-0 last:pb-0">
            <dt className="font-medium text-texte">{question}</dt>
            <dd className="mt-1 text-sm text-texte-secondaire">{reponse}</dd>
          </div>
        ))}
      </dl>
    </Bloc>
  );
}

/* ── Deconnexion ─────────────────────────────────────────────────────────── */

/**
 * ⚠️ Pas de confirmation, et c'est voulu : il n'y a rien a perdre. Les
 * commandes vivent sur le compte, pas dans la session — se reconnecter avec le
 * meme numero les retrouve toutes.
 */
function BlocDeconnexion({ onSeDeconnecter }: { onSeDeconnecter: () => void }) {
  return (
    <div className="pb-4">
      <Bouton style="secondaire" onClick={onSeDeconnecter}>
        Me déconnecter
      </Bouton>
      <p className="mt-2 text-sm text-texte-secondaire">
        Vos commandes restent sur votre compte. Reconnectez-vous avec le même
        numéro pour les retrouver.
      </p>
    </div>
  );
}

/* ── Les deux briques de presentation ────────────────────────────────────── */

function Bloc({
  titre,
  Icone,
  children,
}: {
  titre: string;
  Icone: (p: { taille?: number }) => React.ReactElement;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-bordure p-4">
      <h2 className="flex items-center gap-2 font-semibold text-texte">
        <span className="text-primaire">
          <Icone taille={20} />
        </span>
        {titre}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function Ligne({ libelle, valeur }: { libelle: string; valeur: string }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-2 py-3 first:pt-0 last:pb-0">
      <dt className="text-sm text-texte-secondaire">{libelle}</dt>
      <dd className="font-medium text-texte">{valeur}</dd>
    </div>
  );
}
