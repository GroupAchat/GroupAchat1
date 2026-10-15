import { useEffect, useState } from "react";
import { lireMonDossier, type MonDossierApi } from "../api/dossiers";
import {
  FournisseurEspaceGroupeur,
  useEspaceGroupeur,
} from "../api/EspaceGroupeurContexte";
import { useRequete } from "../api/useRequete";
import { formaterFrancs } from "../domaine/format";
import { LIBELLE_QUARTIER } from "../domaine/groupage";
import { annoncerLArrivee } from "../api/notifications";
import { lienGroupage, partager } from "../domaine/partage";
import { peutLancerUnGroupage } from "../domaine/recrutement";
import Fugitif, { useFugitif } from "../ui/Fugitif";
import type { Campagne, DemandeAgregee } from "../domaine/groupeur";
import {
  BarreNavGroupeur,
  type OngletGroupeur,
  RailGroupeur,
} from "./mise-en-page/ChromeGroupeur";
import CreerCampagne from "./pages/CreerCampagne";
import Decision from "./pages/Decision";
import FilDemandes from "./pages/FilDemandes";
import GererCampagne from "./pages/GererCampagne";
import MesCampagnes from "./pages/MesCampagnes";
import Justificatif from "./pages/Justificatif";
import Portefeuille from "./pages/Portefeuille";
import QuestionsRecues from "./pages/QuestionsRecues";
import Statistiques from "./pages/Statistiques";
import TableauDeBord from "./pages/TableauDeBord";

/**
 * Le routeur du cote groupeur — ecrans 13 a 21.
 *
 * **Separe du routeur acheteur, et volontairement.** Les deux cotes n'ont ni
 * le meme chrome (§1.2 : orange contre bleu), ni la meme barre de navigation,
 * ni les memes ecrans. Les melanger dans un seul `switch` obligerait a tester
 * le role a chaque branche, et la premiere erreur de chrome passerait
 * inapercue.
 *
 * ## Les ecrans
 *
 * | | Ecran | Fichier |
 * |---|---|---|
 * | 13 | Tableau de bord | `pages/groupeur/TableauDeBord` |
 * | 14 | Creer une campagne | `pages/groupeur/CreerCampagne` |
 * | 15 | Gerer une campagne | `pages/groupeur/GererCampagne` |
 * | 16 | Cloturer et decider | `pages/groupeur/Decision` |
 * | 17 | Deposer un justificatif | `pages/groupeur/Justificatif` |
 * | 18 | Portefeuille | `pages/groupeur/Portefeuille` |
 * | 19 | Fil des demandes | `pages/groupeur/FilDemandes` |
 * | 20 | Questions recues | `pages/groupeur/QuestionsRecues` |
 * | 21 | Statistiques | `pages/groupeur/Statistiques` |
 *
 * ## Deux largeurs, une seule arborescence d'ecrans
 *
 * Ces ecrans restent **penses pour le telephone** : un commercant qui
 * travaille debout dans son magasin. Mais un groupeur suit aussi ses
 * groupages depuis un ordinateur, et une colonne de 430 px flottant au milieu
 * d'un ecran de 1 400 px donne le pire des deux mondes.
 *
 * Au-dela de 768 px, on passe donc :
 *
 * - de la **barre du bas** a une **colonne laterale** bleue. Une barre
 *   d'onglets collee en bas d'un grand ecran est un reflexe mobile applique
 *   au mauvais appareil ;
 * - d'une colonne de 430 px a une zone de contenu large, bornee a 1 100 px —
 *   au-dela, les lignes de texte deviennent illisibles.
 *
 * ⚠️ **Aucun ecran n'est dedouble.** Les memes composants sont montes dans
 * les deux cas ; seules la largeur et la navigation changent. Ecrire une
 * version bureau separee doublerait le travail a chaque correction, et les
 * deux divergeraient en quelques semaines.
 *
 * Les formulaires, eux, **gardent leur colonne etroite** meme sur grand
 * ecran : un champ de 1 000 px de large ne se remplit pas mieux, il se lit
 * moins bien.
 */
type EcranGroupeur =
  | { nom: "tableau-de-bord" }
  | { nom: "creer"; depuis?: DemandeAgregee }
  //: La **liste** de ses groupages — l'ecran 15 porte un seul groupage.
  | { nom: "campagnes" }
  | { nom: "campagne"; campagne: Campagne }
  | { nom: "decision"; campagne: Campagne }
  | { nom: "justificatif" }
  | { nom: "portefeuille" }
  | { nom: "demandes" }
  | { nom: "questions" }
  | { nom: "statistiques" };

/** Les ecrans de premier niveau, ceux qui gardent la barre du bas. */
const AVEC_BARRE_NAV: EcranGroupeur["nom"][] = [
  "tableau-de-bord",
  "campagnes",
  "portefeuille",
  "statistiques",
];

export default function ApplicationGroupeur(proprietes: {
  telephone?: string;
  dossierFrais?: MonDossierApi;
  onDossierValide?: () => void;
  onReprendreLeDossier?: () => void;
}) {
  return (
    <FournisseurEspaceGroupeur telephone={proprietes.telephone ?? ""}>
      <RouteurGroupeur {...proprietes} />
    </FournisseurEspaceGroupeur>
  );
}

function RouteurGroupeur({
  telephone = "",
  dossierFrais,
  onDossierValide,
  onReprendreLeDossier,
}: {
  /**
   * Le numero avec lequel le dossier KYC a ete depose.
   *
   * Vide pour un groupeur **deja valide** : on ne relit alors rien, et tout
   * s'ouvre. C'est le cas de toutes les sessions ordinaires — on depose son
   * dossier une fois, on travaille ensuite pendant des mois.
   */
  telephone?: string;
  /** Ce que le depot vient de renvoyer, pour ne pas faire patienter. */
  dossierFrais?: MonDossierApi;
  /** Appele quand la relecture apprend que le dossier est passe valide. */
  onDossierValide?: () => void;
  onReprendreLeDossier?: () => void;
} = {}) {
  const [ecran, setEcran] = useState<EcranGroupeur>({ nom: "tableau-de-bord" });
  const [onglet, setOnglet] = useState<OngletGroupeur>("tableau-de-bord");

  /** De quoi dire « Lien copie » quand le partage passe par le presse-papier. */
  const { message, annoncer } = useFugitif();

  /**
   * L'etat du dossier, **relu a chaque ouverture**.
   *
   * C'est par ici que la decision de l'administrateur rejoint le groupeur
   * dans l'application. Elle lui est annoncee par courriel ou par telephone
   * (§10.5) — une application qu'on rouvre n'est pas un canal d'annonce —
   * mais quand il revient, il doit trouver l'etat a jour et le motif, pas
   * celui de la veille.
   */
  const suivi = useRequete(
    (signal) => lireMonDossier(telephone, signal),
    [telephone],
    telephone !== "",
  );

  /* Ce que le serveur vient de dire l'emporte sur ce que le depot avait
     renvoye : entre les deux, un administrateur a pu trancher. */
  const dossierApi = suivi.donnees ?? dossierFrais;

  /**
   * ⚠️ **Le dossier ne verrouille qu'un seul geste : creer un groupage.**
   *
   * Tout le reste du cote groupeur s'ouvre normalement, et c'est un equilibre
   * delibere : faire attendre quelqu'un devant une porte close pendant deux
   * jours ouvres lui fait oublier le produit, alors que le laisser creer un
   * groupage avant examen nous ferait garantir « vous etes livre, ou
   * rembourse » — affiche a l'acheteur sur presque chaque ecran — sur le
   * compte de quelqu'un dont nous ne savons encore rien. Il decouvre l'outil ;
   * il n'engage pas encore l'argent des autres.
   *
   * **Et ce n'est qu'un confort d'affichage.** Le verrou reel est dans
   * `Campagne.save()` cote serveur : une interface ne protege rien, il suffit
   * d'une requete directe pour la contourner.
   *
   * ⚠️ **C'est le serveur qui dit s'il peut lancer**, pas un calcul local sur
   * l'etat. `peut_lancer_une_campagne` sort du modele Django, qui connait les
   * conditions reelles ; les deduire ici d'un libelle d'etat creerait une
   * seconde regle a tenir a jour.
   */
  const dossier =
    dossierApi && !dossierApi.peut_lancer_une_campagne
      ? {
          etat: dossierApi.etat,
          motif: dossierApi.motif || undefined,
          pseudonyme: dossierApi.pseudonyme,
        }
      : undefined;

  const peutCreer =
    dossier === undefined || peutLancerUnGroupage(dossier.etat);

  /* Le dossier vient d'etre valide : plus rien a suivre, le numero peut
     s'effacer du navigateur. Dans un effet — prevenir le parent pendant le
     rendu reviendrait a changer son etat au milieu du notre. */
  const estValide = dossierApi?.peut_lancer_une_campagne === true;
  useEffect(() => {
    if (estValide) {
      onDossierValide?.();
    }
  }, [estValide, onDossierValide]);

  const { campagnes, recharger } = useEspaceGroupeur();

  /* ⚠️ `?? CAMPAGNES[0]` a disparu : il y avait toujours une campagne de
     demonstration sous la main, donc l'ecran 16 s'ouvrait meme quand il n'y
     avait rien a decider. Avec de vraies donnees, un groupeur neuf n'a aucune
     campagne, et ouvrir un ecran de decision vide serait pire que de ne pas
     l'ouvrir. */
  /* ⚠️ **`statut === "ouverte"` est indispensable dans le repli.** Sans lui,
     `heuresRestantes === 0` attrapait aussi les groupages **annules et
     livres**, dont le compteur vaut zero lui aussi — et c'est l'annule qui
     arrivait en tete de liste. L'ecran 16 s'ouvrait donc sur « 0 commande,
     0 F CFA » alors que la tache annoncait « Eau de javel, 14 commandes ».

     La condition est maintenant celle que le serveur applique pour fabriquer
     la tache (`_taches` dans `api_groupeur.py`) : ouverte, et le temps
     ecoule. Les deux doivent dire la meme chose, sinon on clique sur une
     ligne et on arrive ailleurs. */
  const campagneADecider =
    campagnes.find((c) => c.statut === "a-decider") ??
    campagnes.find((c) => c.statut === "ouverte" && c.heuresRestantes === 0);

  /** Les quatre entrees de « A faire aujourd'hui » de l'ecran 13. */
  const ouvrirTache = (destination: string) => {
    switch (destination) {
      case "decision":
        /* Pas de campagne a decider : la tache n'aurait pas du s'afficher.
           On ne navigue pas plutot que d'ouvrir un ecran sans sujet. */
        return campagneADecider
          ? setEcran({ nom: "decision", campagne: campagneADecider })
          : undefined;
      case "justificatif":
        return setEcran({ nom: "justificatif" });
      case "questions":
        return setEcran({ nom: "questions" });
      case "demandes":
        return setEcran({ nom: "demandes" });
    }
  };

  const retourTableau = () => {
    setOnglet("tableau-de-bord");
    setEcran({ nom: "tableau-de-bord" });
  };

  const ouvrirStatistiques = () => {
    setOnglet("statistiques");
    setEcran({ nom: "statistiques" });
  };

  const navigation = AVEC_BARRE_NAV.includes(ecran.nom);

  const changerDOnglet = (nouvelOnglet: OngletGroupeur) => {
    setOnglet(nouvelOnglet);
    switch (nouvelOnglet) {
      case "tableau-de-bord":
        return setEcran({ nom: "tableau-de-bord" });
      case "campagnes":
        /* ⚠️ **La liste, pas le premier groupage.** Cet onglet ouvrait
           directement l'ecran 15 sur `campagnes[0]`, c'est-a-dire sur le plus
           recent — qui se trouvait etre le groupage annule. On arrivait donc
           sur « 0 commande, 0 F CFA », et l'application avait l'air vide
           alors qu'elle portait six groupages pleins. */
        return setEcran({ nom: "campagnes" });
      case "statistiques":
        return setEcran({ nom: "statistiques" });
      case "portefeuille":
        return setEcran({ nom: "portefeuille" });
    }
  };

  return (
    <div className="flex min-h-dvh bg-white">
      {navigation ? (
        <RailGroupeur
          actif={onglet}
          onChanger={changerDOnglet}
          pseudonyme={dossierApi?.pseudonyme}
        />
      ) : null}

      {/* ⚠️ **Deux boites, et les deux servent.** `flex-1` prend la largeur
          restante a cote du rail ; `mx-auto` **centre le contenu dedans**.
          Sans la seconde, la colonne de 1 100 px se collait au rail et
          laissait tout le vide a droite — ce qui donne l'impression que la
          page a mal charge plutot qu'une mise en page.
          `min-w-0` evite qu'un tableau large pousse le rail hors de l'ecran. */}
      <div className="min-w-0 flex-1">
        {/* ⚠️ **Deux largeurs, selon ce que l'ecran fait.**

            Les ecrans de premier niveau — tableau de bord, statistiques,
            portefeuille — gagnent a l'espace : ce sont des vues d'ensemble, et
            deux colonnes y valent mieux qu'un ruban.

            Les ecrans de travail — un formulaire, une decision, une file de
            demandes — gardent une colonne etroite. Un champ de 1 000 px ne se
            remplit pas mieux, un bouton de 1 000 px de large n'est pas plus
            facile a viser, et une ligne de texte aussi longue se relit mal. */}
        <div
          className={`relative mx-auto min-h-dvh w-full max-w-[430px] bg-white ${
            navigation ? "md:max-w-[1180px]" : "md:max-w-[760px]"
          }`}
        >
      {ecran.nom === "tableau-de-bord" ? (
        <TableauDeBord
          onStatistiques={ouvrirStatistiques}
          onCampagne={(campagne) => setEcran({ nom: "campagne", campagne })}
          onTache={ouvrirTache}
          onCreer={() => setEcran({ nom: "creer" })}
          dossier={dossier}
          onReprendreLeDossier={onReprendreLeDossier}
        />
      ) : null}

      {ecran.nom === "campagnes" ? (
        <MesCampagnes
          onCampagne={(campagne) => setEcran({ nom: "campagne", campagne })}
          onCreer={peutCreer ? () => setEcran({ nom: "creer" }) : undefined}
        />
      ) : null}

      {ecran.nom === "creer" ? (
        <CreerCampagne
          prerempli={
            ecran.depuis
              ? {
                  produit: ecran.depuis.produit,
                  quantite: ecran.depuis.personnes,
                  /* Le libelle, pas la cle : « Agoè » et non « Agoe ». */
                  quartier: LIBELLE_QUARTIER[ecran.depuis.quartier],
                }
              : undefined
          }
          telephone={telephone}
          onRetour={retourTableau}
          onPubliee={() => {
            /* Le groupage existe : le tableau de bord, la liste et les
               chiffres ont tous change. */
            recharger();
            retourTableau();
          }}
        />
      ) : null}

      {ecran.nom === "campagne" ? (
        <GererCampagne
          campagne={ecran.campagne}
          onRetour={retourTableau}
          /*
           * ⚠️ **Le groupeur partage la fiche acheteur, pas un ecran a lui.**
           * C'est le meme lien que celui du bouton « Partager » de la fiche :
           * recruter des participants, c'est envoyer quelqu'un sur la page ou
           * il peut commander. Un lien vers l'ecran 14 l'enverrait sur sa
           * propre gestion de campagne.
           */
          onPartager={async () => {
            const resultat = await partager({
              titre: ecran.campagne.produit,
              texte: `${ecran.campagne.produit} — ${formaterFrancs(ecran.campagne.prixPart)} la part sur Group Achat.`,
              lien: lienGroupage(ecran.campagne.id),
            });
            if (resultat === "copie") {
              annoncer("Lien copié");
            } else if (resultat === "echec") {
              annoncer("Impossible de copier le lien");
            }
          }}
          arriveeAnnoncee={ecran.campagne.arriveeAnnonceeLe !== undefined}
          /*
           * ⚠️ **Le compte est la seule chose qu'on lui renvoie.**
           *
           * « 32 personnes prevenues » lui dit que son geste a porte, sans
           * rien lui apprendre sur qui elles sont — ni nom, ni numero, ni
           * quartier. C'est ce qui rend cette fonctionnalite compatible avec
           * l'anonymat : il annonce un fait sur sa campagne, nous le
           * distribuons.
           *
           * Et on **relit ses campagnes** ensuite, pour que le bouton
           * s'eteigne : sans cela il resterait actif et un second appui
           * repondrait « deja annonce » sans rien faire.
           */
          onAnnoncerLArrivee={async () => {
            try {
              const resultat = await annoncerLArrivee(
                ecran.campagne.id,
                telephone,
              );
              annoncer(
                resultat.deja_annonce
                  ? "Arrivée déjà annoncée"
                  : `${resultat.prevenus} personne${resultat.prevenus > 1 ? "s" : ""} prévenue${resultat.prevenus > 1 ? "s" : ""}`,
              );
              recharger();
            } catch {
              annoncer("L'annonce n'a pas pu être envoyée");
            }
          }}
          onCloturer={() =>
            setEcran({ nom: "decision", campagne: ecran.campagne })
          }
        />
      ) : null}

      {ecran.nom === "decision" ? (
        <Decision
          campagne={ecran.campagne}
          telephone={telephone}
          onCloturee={recharger}
          onFermer={retourTableau}
          onCommander={() => setEcran({ nom: "justificatif" })}
        />
      ) : null}

      {ecran.nom === "justificatif" ? (
        <Justificatif onRetour={retourTableau} />
      ) : null}

      {ecran.nom === "portefeuille" ? (
        <Portefeuille onStatistiques={ouvrirStatistiques} />
      ) : null}

      {ecran.nom === "demandes" ? (
        <FilDemandes
          onRetour={retourTableau}
          onLancerCampagne={(demande) =>
            setEcran({ nom: "creer", depuis: demande })
          }
        />
      ) : null}

      {ecran.nom === "questions" ? (
        <QuestionsRecues onRetour={retourTableau} />
      ) : null}

      {ecran.nom === "statistiques" ? (
        <Statistiques
          onPortefeuille={() => {
            setOnglet("portefeuille");
            setEcran({ nom: "portefeuille" });
          }}
          /* ⚠️ **Le meme verrou qu'au tableau de bord.** L'ecran 21 offre un
             second chemin vers la creation ; le laisser ouvert ferait un
             contournement du premier, et c'est exactement par la que ce genre
             de regle se perd. */
          onCreer={
            peutCreer ? () => setEcran({ nom: "creer" }) : undefined
          }
        />
      ) : null}

          <Fugitif message={message} />

          {navigation ? (
            <BarreNavGroupeur actif={onglet} onChanger={changerDOnglet} />
          ) : null}
        </div>
      </div>
    </div>
  );
}
