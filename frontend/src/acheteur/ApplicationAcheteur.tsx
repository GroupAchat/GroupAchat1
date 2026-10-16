import { useEffect, useState } from "react";
import FeuilleInscription from "./composants/FeuilleInscription";
import InviteCompte, {
  type OperationCompte,
} from "./composants/InviteCompte";
import FeuilleConnexion, {
  type Identite,
} from "./composants/FeuilleConnexion";
import type { Commande } from "../domaine/commande";
import { FILTRES_PAR_DEFAUT, type Filtres } from "../domaine/filtres";
import { formaterFrancs } from "../domaine/format";
import {
  groupageDepuisAdresse,
  inscrireLeGroupageDansLAdresse,
  lienGroupage,
  partager,
} from "../domaine/partage";
import type { Groupage } from "../domaine/groupage";
import type { NotificationApi } from "../api/notifications";
import {
  adapterCommande,
  listerMesCommandes,
  lireUnGroupage,
  payer,
} from "../api/campagnes";
import { ErreurApi, poserLeJetonAcheteur } from "../api/client";
import {
  lireLeJeton,
  lireMonProfil,
  oublierLeJeton,
  seDeconnecter,
  type Profil,
} from "../api/session";
import {
  FournisseurCatalogue,
  useCatalogue,
} from "../api/CatalogueContexte";
import {
  FournisseurNotifications,
  useNotifications,
} from "../api/NotificationsContexte";
import useEstBureau from "../hooks/useEstBureau";
import Fugitif, { useFugitif } from "../ui/Fugitif";
import BarreNav, { type OngletAcheteur } from "./mise-en-page/BarreNav";
import PanneauNotifications from "./composants/PanneauNotifications";
import PanneauQuestions from "./composants/PanneauQuestions";
import EnTeteBureau from "./mise-en-page/EnTeteBureau";
import MenuPrincipal, {
  type DestinationMenu,
} from "./mise-en-page/MenuPrincipal";
import { FournisseurNavigation } from "./mise-en-page/NavigationContexte";
import Commander, { type BrouillonPaiement } from "./pages/Commander";
import Confirmation from "./pages/Confirmation";
import DemanderProduit from "./pages/DemanderProduit";
import DetailCommande from "./pages/DetailCommande";
import DetailGroupage from "./pages/DetailGroupage";
import Fil from "./pages/Fil";
import GroupagesOuverts from "./pages/GroupagesOuverts";
import MesCommandes from "./pages/MesCommandes";
import MesDemandes from "./pages/MesDemandes";
import Paiement from "./pages/Paiement";
import PageProfil from "./pages/Profil";
import Questions from "./pages/Questions";

/**
 * Le routeur du cote acheteur — ecrans 0 a 12.
 *
 * Si vous cherchez quel ecran mene a quel autre de ce cote-la, c'est ici et
 * nulle part ailleurs. Le cote groupeur a son propre routeur,
 * `ApplicationGroupeur` : les deux n'ont ni le meme chrome, ni la meme barre
 * de navigation, ni les memes ecrans.
 *
 * ## Les ecrans construits
 *
 * | | Ecran | Fichier |
 * |---|---|---|
 * | 1 | Le fil *(telephone)* | `pages/Fil` |
 * | 2 | Catalogue | `pages/GroupagesOuverts` |
 * | 3 | Detail d'un groupage | `pages/DetailGroupage` |
 * | 4 | Connexion *(feuille)* | `composants/FeuilleConnexion` |
 * | 5 | Commander | `pages/Commander` |
 * | 6 | Paiement simule | `pages/Paiement` |
 * | 7 | Confirmation | `pages/Confirmation` |
 * | 8 | Mes commandes | `pages/MesCommandes` |
 * | 9 | Detail d'une commande | `pages/DetailCommande` |
 * | 10 | Questions publiques | `pages/Questions` |
 * | 11 | Demander un produit | `pages/DemanderProduit` |
 * | 12 | Mes demandes | `pages/MesDemandes` |
 * | — | Profil *(4e onglet, « 12 et reglages »)* | `pages/Profil` |
 *
 * Les ecrans 13 a 22 et A1 vivent ailleurs : `ApplicationGroupeur` pour le
 * cote groupeur, `pages/TourneeLivreur` pour le livreur et
 * `pages/TableauDeBordAdmin` pour l'administration. `main.tsx` choisit lequel
 * monter.
 *
 * ## Deux architectures selon la largeur
 *
 * | | Telephone | Ordinateur (≥ 768 px) |
 * |---|---|---|
 * | Ouverture | Demarrage, puis **le fil** | **Le catalogue** |
 * | Navigation | `BarreNav` en bas | `EnTeteBureau` + pied de page |
 *
 * Le fil et la barre du bas ne sont **pas montes** au-dela de 768 px : les
 * cacher en CSS leur laisserait telecharger leurs images et garder leurs
 * ecouteurs de defilement pour rien.
 *
 * La page de demarrage et le choix de profil appartiennent a `App.tsx`, qui
 * les montre avant d'entrer ici.
 *
 * ## Pas de bibliotheque de routage
 *
 * Treize ecrans enchaines n'en ont pas besoin, et chaque kilo-octet compte sur
 * l'Android d'entree de gamme du §5 du cahier des charges. **Le jour ou il
 * faudra des URL partageables** — le partage d'un groupage est un levier de
 * croissance de l'ecran 3 — ce `useState` deviendra un vrai routeur, et le
 * type `Ecran` ci-dessous donnera directement la table des routes.
 *
 * ## La regle a ne pas casser
 *
 * L'etat du parcours vit **ici**, pas dans les pages. C'est ce qui permet de
 * tenir la promesse du §1.5 : fermer la feuille de connexion ramene a l'ecran
 * 5 **intact**, parce que l'ecran 5 n'a jamais ete demonte. Deplacer cet etat
 * dans une page casserait cette promesse sans que rien ne le signale.
 */

type Ecran =
  | { nom: "fil" }
  | { nom: "catalogue" }
  | { nom: "groupage"; groupage: Groupage }
  | { nom: "commander"; groupage: Groupage }
  | { nom: "paiement"; brouillon: BrouillonPaiement }
  | { nom: "confirmation"; commande: Commande }
  | { nom: "mes-commandes" }
  | { nom: "commande"; commande: Commande }
  | { nom: "questions"; groupage: Groupage }
  | { nom: "demander" }
  | { nom: "mes-demandes" }
  | { nom: "profil" };

/** Les ecrans de premier niveau, ceux qui gardent la barre du bas. */
const ECRANS_AVEC_BARRE_NAV: Ecran["nom"][] = [
  "fil",
  "catalogue",
  "mes-commandes",
  "mes-demandes",
  "profil",
];

/**
 * Le point d'entree du cote acheteur.
 *
 * Il ne fait qu'une chose en plus du routeur : **poser le fournisseur de
 * catalogue**. Le catalogue est charge une fois ici et partage par tous les
 * ecrans, plutot que retelecharge a chaque navigation — voir
 * `api/CatalogueContexte.tsx` pour le raisonnement, qui tient au forfait de
 * donnees limite du §5.
 */
export default function ApplicationAcheteur({
  onDevenirGroupeur,
}: {
  /**
   * Vers le depot de dossier du groupeur (ecran 13).
   *
   * ⚠️ Il **change de produit**, pas d'ecran : le cote groupeur a son propre
   * chrome et son propre routeur, et c'est `App` qui bascule entre les deux.
   * Il traverse donc la coquille sans qu'elle s'en serve.
   */
  onDevenirGroupeur?: () => void;
}) {
  return (
    <FournisseurCatalogue>
      <CoquilleAcheteur onDevenirGroupeur={onDevenirGroupeur} />
    </FournisseurCatalogue>
  );
}

/**
 * Pose le fournisseur de notifications, qui a besoin de savoir si on est
 * connecte.
 *
 * ⚠️ **Un etage de plus, et pour une raison precise.** L'etat de connexion
 * vit dans `RouteurAcheteur` ; le fournisseur doit l'envelopper tout en le
 * connaissant. On lit donc le jeton **une fois de plus ici**, au lieu de le
 * faire descendre : les notifications sont nominatives, et rien ne doit etre
 * demande au serveur sans session.
 *
 * Lire le jeton deux fois ne coute rien — c'est une lecture de stockage
 * local — et le mettre en commun aurait demande un contexte supplementaire
 * pour la session, ce qui est beaucoup d'echafaudage pour un booleen.
 */
function CoquilleAcheteur({
  onDevenirGroupeur,
}: {
  onDevenirGroupeur?: () => void;
}) {
  const [connecte, setConnecte] = useState(() => lireLeJeton() !== undefined);

  return (
    <FournisseurNotifications connecte={connecte}>
      <RouteurAcheteur
        onConnexionChangee={setConnecte}
        onDevenirGroupeur={onDevenirGroupeur}
      />
    </FournisseurNotifications>
  );
}

function RouteurAcheteur({
  /** Previent la coquille qu'il faut relire les notifications. */
  onConnexionChangee,
  onDevenirGroupeur,
}: {
  onConnexionChangee: (connecte: boolean) => void;
  onDevenirGroupeur?: () => void;
}) {
  const estBureau = useEstBureau();
  const { groupages } = useCatalogue();

  /**
   * ⚠️ **La reconnexion automatique.** C'est ici qu'elle se joue.
   *
   * Au lancement, le jeton retenu est posé puis vérifié auprès du serveur.
   * S'il répond, l'acheteur est connecté sans rien avoir fait — ni code SMS,
   * ni saisie d'adresse. S'il répond 401, le jeton est périmé : on l'oublie,
   * et la feuille reviendra au moment de payer, comme pour un nouveau venu.
   *
   * **Vérifié, et pas seulement lu.** Se fier au jeton stocké afficherait
   * « connecté » à quelqu'un dont la session a expiré, qui ne le découvrirait
   * qu'au moment de payer — c'est-à-dire au pire moment.
   */
  useEffect(() => {
    const jeton = lireLeJeton();
    if (!jeton) {
      return;
    }
    poserLeJetonAcheteur(jeton);

    let abandonne = false;
    lireMonProfil()
      .then((profil) => {
        if (!abandonne) {
          setProfil(profil);
          setIdentite({
            telephone: profil.telephone,
            nom: profil.nom || undefined,
          });
        }
      })
      .catch(() => {
        /* Jeton périmé, révoqué, ou serveur injoignable. Dans les trois cas,
           on repart anonyme : le catalogue se lit sans compte (§1.5), et la
           feuille reviendra d'elle-même au paiement. */
        if (!abandonne) {
          oublierLeJeton();
          poserLeJetonAcheteur("");
        }
      });

    return () => {
      abandonne = true;
    };
  }, []);

  const [ecran, setEcran] = useState<Ecran>({ nom: "fil" });
  const [onglet, setOnglet] = useState<OngletAcheteur>("accueil");
  const [filtres, setFiltres] = useState<Filtres>(FILTRES_PAR_DEFAUT);
  const [identite, setIdentite] = useState<Identite>();
  /** Le profil complet, dont **l'adresse par défaut** qui pré-remplit l'écran 5. */
  const [profil, setProfil] = useState<Profil>();
  /** Commande en attente de connexion : le paiement reprend seul apres. */
  const [enAttenteDeConnexion, setEnAttenteDeConnexion] =
    useState<BrouillonPaiement>();
  /**
   * Connexion demandee **sans rien a reprendre ensuite**.
   *
   * Le §1.5 impose sous chaque onglet protege un lien « J'ai deja un compte —
   * me connecter ». Il n'avait rien pour s'ouvrir : la feuille ne se montait
   * que s'il y avait un paiement en attente, donc le lien ne faisait rien.
   * Deux etats distincts plutot qu'un seul, parce que les deux fins
   * diffferent — l'une reprend le paiement, l'autre reste ou elle est.
   */
  const [connexionDemandee, setConnexionDemandee] = useState(false);

  /**
   * **La porte du compte** : le message, puis l'inscription ou la connexion.
   *
   * Elle s'ouvre quand l'acheteur engage quelque chose sans compte —
   * rejoindre un groupage, poser une question. Les trois étapes vivent dans
   * un seul état parce qu'elles sont **un seul parcours** : fermer à
   * n'importe laquelle doit ramener à la page intacte, et la reprise à la fin
   * doit être la même quel que soit le chemin pris.
   *
   * ```
   * invite ──▶ inscription ──▶ reprise
   *    └────▶ connexion ───▶ reprise
   * ```
   *
   * `groupage` ne sert qu'à l'opération « rejoindre » : c'est ce qu'on ouvre
   * après. Pour une question, il n'y a rien à rouvrir — le panneau est resté
   * monté derrière la feuille, et il redevient utilisable dès que `connecte`
   * passe à vrai.
   *
   * ⚠️ **Distincte de `enAttenteDeConnexion`**, et il faut les deux.
   *
   * | | `porte` | `enAttenteDeConnexion` |
   * |---|---|---|
   * | Quand | À l'**ouverture** de l'écran 5, ou à une question | Au clic sur « Payer » |
   * | Ce qu'elle porte | Le groupage seul | Un brouillon complet |
   * | Adresse à transmettre | **aucune** | Celle de l'écran 5 |
   * | On reprend sur | L'écran 5, ou rien | L'écran 6 |
   *
   * Les fusionner reviendrait à fabriquer un faux brouillon — quantité 1,
   * adresse vide — juste pour faire tenir le premier cas dans la forme du
   * second, et cette adresse vide partirait au serveur comme adresse par
   * défaut du compte.
   */
  const [porte, setPorte] = useState<{
    operation: OperationCompte;
    groupage?: Groupage;
    etape: "invite" | "inscription" | "connexion";
  }>();

  /**
   * Le groupage dont le panneau de questions est ouvert.
   *
   * ⚠️ **Pose dans la coquille, pas dans la fiche.** Le panneau se superpose
   * a la page et doit survivre au defilement ; surtout, c'est ici que vivent
   * le numero du compte et la feuille de connexion, dont il a besoin pour
   * demander la connexion au moment de l'envoi (§1.5).
   */
  const [questionsOuvertes, setQuestionsOuvertes] = useState<
    Groupage | undefined
  >();
  const [commandesPassees, setCommandesPassees] = useState(0);

  /** De quoi dire « Lien copie » : sans ce retour, partager est invisible. */
  const { message, annoncer } = useFugitif();

  const cloche = useNotifications();

  /** Le menu principal, seule navigation du cote bureau. */
  const [menuOuvert, setMenuOuvert] = useState(false);

  const connecte = identite !== undefined;

  /**
   * La coquille relit les notifications quand la session change.
   *
   * ⚠️ **Un effet sur `connecte`, et non un appel a chaque endroit ou la
   * session bouge.** Elle bouge a cinq endroits — connexion, reprise de
   * paiement, deconnexion, relecture du jeton au demarrage — et en oublier un
   * laisserait la cloche de la personne precedente allumee pour la suivante.
   * Un seul effet sur l'etat lui-meme ne peut pas etre incomplet.
   */
  useEffect(() => {
    onConnexionChangee(connecte);
  }, [connecte, onConnexionChangee]);

  /**
   * Relit le profil complet apres une connexion.
   *
   * ⚠️ Indispensable : `onConnecte` ne renvoie qu'une `Identite` — numero et
   * nom. Sans cet appel, `profil` reste vide jusqu'au prochain chargement de
   * page, et l'onglet Profil affiche son squelette de chargement indefiniment
   * alors que la session est ouverte.
   */
  const rafraichirLeProfil = () => {
    lireMonProfil()
      .then(setProfil)
      .catch(() => {
        /* La session vient de s'ouvrir, donc l'echec est reseau. L'identite
           suffit a tout le parcours d'achat ; l'adresse par defaut
           reapparaitra au prochain lancement. */
      });
  };

  /**
   * Le groupage demande par l'adresse, au tout premier affichage.
   *
   * ⚠️ **Il passe par l'API, pas par le catalogue deja charge.** Un groupage
   * cloture quitte le catalogue mais garde sa fiche accessible par son lien
   * (regle produit) : le chercher dans la liste aurait marche pour l'ouvert et
   * echoue precisement dans le cas ou le lien sert — celui qu'on a recu hier.
   *
   * Un lien invalide ou un groupage supprime **ne bloque rien** : on reste sur
   * l'ecran d'accueil. Afficher une erreur pour un parametre d'adresse que
   * l'utilisateur n'a probablement pas tape lui-meme serait l'accuser d'une
   * faute qui n'est pas la sienne.
   */
  useEffect(() => {
    const demande = groupageDepuisAdresse();
    if (demande === undefined) {
      return;
    }
    const abandon = new AbortController();
    lireUnGroupage(demande, abandon.signal)
      .then((groupage) => setEcran({ nom: "groupage", groupage }))
      .catch(() => inscrireLeGroupageDansLAdresse(undefined));
    return () => abandon.abort();
  }, []);

  /** Sur ordinateur, le fil n'existe pas : « accueil » montre le catalogue. */
  const vue: Ecran =
    estBureau && ecran.nom === "fil" ? { nom: "catalogue" } : ecran;

  /**
   * Ouvre une fiche **et l'inscrit dans l'adresse**.
   *
   * ⚠️ Les deux vont ensemble, sinon le partage mentirait : le bouton
   * « Partager » fabrique son lien a partir de l'identifiant du groupage
   * affiche, et quelqu'un qui copie la barre d'adresse doit obtenir le meme
   * lien que quelqu'un qui appuie sur le bouton. Recharger la page revient
   * alors sur la fiche, au lieu de retomber sur le catalogue.
   */
  const ouvrirGroupage = (groupage: Groupage) => {
    inscrireLeGroupageDansLAdresse(groupage.id);
    setEcran({ nom: "groupage", groupage });
  };

  /**
   * Partage le groupage affiche.
   *
   * Le texte dit **ce qu'on partage**, pas « regarde ca » : le destinataire
   * recoit souvent le lien seul, sans contexte. Le prix y figure parce que
   * c'est l'information qui decide d'ouvrir le lien ou non.
   *
   * ⚠️ Pas de prix barre, pas de « au lieu de » — la regle vaut aussi dans un
   * message WhatsApp, qui est pourtant l'endroit ou la tentation est la plus
   * forte.
   */
  const partagerLeGroupage = async (groupage: Groupage) => {
    const resultat = await partager({
      titre: groupage.produit,
      texte: `${groupage.produit} — ${formaterFrancs(groupage.prixPart)} la part sur Group Achat.`,
      lien: lienGroupage(groupage.id),
    });
    if (resultat === "copie") {
      annoncer("Lien copié");
    } else if (resultat === "echec") {
      annoncer("Impossible de copier le lien");
    }
  };

  /**
   * Ce qu'on propose sous une fiche produit.
   *
   * Calcule ici plutot que dans l'ecran : la fiche ne connait pas le
   * catalogue, et lui faire lire le contexte la rendrait impossible a monter
   * seule.
   */
  const similaires =
    vue.nom === "groupage"
      ? (() => {
          const autres = groupages.filter((g) => g.id !== vue.groupage.id);
          const memeCategorie = autres.filter(
            (g) => g.categorie === vue.groupage.categorie,
          );
          const reste = autres.filter(
            (g) => g.categorie !== vue.groupage.categorie,
          );
          return [...memeCategorie, ...reste].slice(0, 4);
        })()
      : [];

  /**
   * Vrai quand on arrive au catalogue **par la loupe** du fil.
   *
   * L'en-tete telephone replie sa recherche derriere une loupe ; cette
   * intention doit traverser le changement d'ecran, sinon on atterrit sur
   * l'ecran de recherche avec la recherche fermee.
   */
  const [rechercheDemandee, setRechercheDemandee] = useState(false);

  const ouvrirCatalogue = () => {
    inscrireLeGroupageDansLAdresse(undefined);
    setRechercheDemandee(false);
    setOnglet("groupage");
    setEcran({ nom: "catalogue" });
  };

  /**
   * Le catalogue, **avec le champ de recherche deplie**.
   *
   * ⚠️ **Une fonction a part, et non un parametre de `ouvrirCatalogue`.**
   * Celui-ci est passe tel quel a des `onClick`, et React leur transmet
   * l'evenement : un premier argument optionnel y serait **toujours vrai**,
   * donc toute arrivee au catalogue deplierait la recherche.
   */
  const ouvrirLaRecherche = () => {
    inscrireLeGroupageDansLAdresse(undefined);
    setRechercheDemandee(true);
    setOnglet("groupage");
    setEcran({ nom: "catalogue" });
  };

  const ouvrirDemande = () => {
    /* ⚠️ **`"demander"` et non `"profil"`.** « Demander » a son propre onglet
       depuis qu'il est dans la barre du bas : marquer « Profil » comme actif
       pendant qu'on remplit le formulaire de demande allumerait le mauvais
       repere, et c'est le seul role de cette barre. */
    setOnglet("demander");
    setEcran({ nom: "demander" });
  };

  /**
   * Ouvre ce dont parle une notification.
   *
   * ⚠️ **Une cloche dont les lignes ne menent nulle part est une cloche qu'on
   * lit une fois.** On y apprend que le groupage est cloture, puis on doit
   * retrouver sa commande a la main — et on cesse de l'ouvrir.
   *
   * L'ordre n'est pas arbitraire :
   *
   * 1. **la commande d'abord**, quand la notification en designe une. C'est la
   *    que vivent le suivi et le code de livraison, donc ce qu'on cherche
   *    apres « votre commande est arrivee » ou « vous etes rembourse » ;
   * 2. **la fiche du produit** sinon, qui porte les questions publiques — donc
   *    la reponse du groupeur.
   *
   * ⚠️ **Les deux passent par l'API, pas par ce qui est deja charge.** Une
   * notification parle presque toujours d'un groupage **cloture** : c'est la
   * cloture qui la declenche. Or le catalogue ne sert que de l'ouvert. Le
   * chercher en memoire aurait donc echoue dans le cas le plus courant, et
   * reussi seulement sur les notifications dont on a le moins besoin.
   */
  const ouvrirDepuisUneNotification = async (
    notification: NotificationApi,
  ) => {
    if (notification.campagne === null) {
      ouvrirCatalogue();
      return;
    }

    const identifiant = String(notification.campagne);
    let groupage = groupages.find((candidat) => candidat.id === identifiant);
    if (groupage === undefined) {
      try {
        groupage = await lireUnGroupage(identifiant);
      } catch {
        /* Groupage supprime, ou reseau coupe. On ne bloque pas sur une
           notification : on revient au catalogue plutot que d'afficher une
           erreur pour un clic qui ne demandait rien de precis. */
        ouvrirCatalogue();
        return;
      }
    }

    if (notification.commande !== null) {
      try {
        const brutes = await listerMesCommandes();
        const brute = brutes.find(
          (candidate) => String(candidate.id) === String(notification.commande),
        );
        const commande = brute
          ? adapterCommande(brute, [groupage])
          : undefined;
        if (commande) {
          setOnglet("commandes");
          setEcran({ nom: "commande", commande });
          return;
        }
      } catch {
        /* On retombe sur la fiche du produit, qui est toujours parlante. */
      }
    }

    ouvrirGroupage(groupage);
  };

  /**
   * Declenche par « Commander », sur la fiche produit.
   *
   * ⚠️ **C'est ici que le compte est desormais exige, et c'est un
   * deplacement assume par rapport au §1.5**, qui ecrit « le compte est
   * demande au moment de payer ». Il l'est maintenant un ecran plus tot.
   *
   * Ce qui ne change pas, et qui est l'essentiel de ce paragraphe : **on
   * navigue toujours librement.** Le fil, le catalogue, les fiches produit,
   * les categories, les questions publiques se lisent sans compte. Il n'y a
   * pas de mur d'authentification a l'entree ; il y a une porte a l'entree du
   * tunnel d'achat.
   *
   * Ce que ca coute, franchement : quelqu'un venu d'un lien WhatsApp qui
   * voudrait seulement *voir* le formulaire de commande — les variantes
   * disponibles, les frais de livraison vers son quartier — doit maintenant
   * se connecter d'abord. C'est reel, et c'est le prix de la decision.
   *
   * Ce que ca rend en echange : l'ecran 5 affiche des frais de livraison et
   * pre-remplit une adresse, deux choses qui appartiennent a un compte. Les
   * demander a un inconnu, puis lui demander un code SMS a l'ecran suivant,
   * faisait saisir son adresse avant de savoir qu'un compte serait necessaire.
   */
  const demanderCommande = (groupage: Groupage) => {
    if (connecte) {
      setEcran({ nom: "commander", groupage });
      return;
    }
    setPorte({ operation: "rejoindre", groupage, etape: "invite" });
  };

  /**
   * La même porte, pour une question publique.
   *
   * `Questions` appelle déjà `onSeConnecter` à l'envoi quand il n'y a pas de
   * numéro ; ce qui change est **ce qui s'affiche alors** : un message qui dit
   * pourquoi un compte est nécessaire, plutôt qu'un formulaire de connexion
   * surgi sans explication.
   */
  const demanderUnCompte = (operation: OperationCompte) => {
    setPorte({ operation, etape: "invite" });
  };

  /**
   * Ce qui se passe quand la porte est franchie, par l'un ou l'autre chemin.
   *
   * ⚠️ **La reprise est lue avant d'effacer l'état.** `setPorte(undefined)`
   * est asynchrone, mais `porte` est la valeur capturée par ce rendu : la lire
   * après l'appel donnerait encore la bonne valeur ici, et serait un piège à
   * la première refonte. On la met de côté d'abord.
   */
  const franchirLaPorte = (nouvelleIdentite: Identite) => {
    const ouverte = porte;
    setIdentite(nouvelleIdentite);
    setPorte(undefined);
    rafraichirLeProfil();

    if (ouverte?.operation === "rejoindre" && ouverte.groupage) {
      /* L'action reprend seule : la feuille redescend sur l'ecran de
         commande, qui pre-remplira l'adresse du compte si elle existe. */
      setEcran({ nom: "commander", groupage: ouverte.groupage });
    }
  };

  /**
   * Declenche par « Payer ».
   *
   * ⚠️ **Ce n'est plus le seul point ou un compte est exige** — la porte est
   * passee a `demanderCommande`, un ecran plus tot. Ce controle **reste
   * necessaire** malgre tout, et pas par prudence decorative : une session
   * expire, et elle peut expirer entre l'ecran 5 et le clic sur « Payer ».
   * Sans lui, le paiement partirait sans jeton et echouerait en 401, devant
   * quelqu'un qui n'aurait aucun moyen de comprendre pourquoi.
   */
  const demanderPaiement = (brouillon: BrouillonPaiement) => {
    if (connecte) {
      setEcran({ nom: "paiement", brouillon });
      return;
    }
    setEnAttenteDeConnexion(brouillon);
  };

  return (
    /*
     * ⚠️ **Les destinations du chrome sont fournies ici, une seule fois.**
     *
     * Le pied de page est monte par neuf ecrans ; sans ce fournisseur, ces
     * cinq fonctions devraient traverser les neuf, dont aucun ne s'en sert.
     * Voir `mise-en-page/NavigationContexte`.
     */
    <FournisseurNavigation
      destinations={{
        onCatalogue: ouvrirCatalogue,
        /* ⚠️ **Pas de destination quand on y est déjà.** Le pied de page
           affichait « Demander un produit » sur l'écran du formulaire de
           demande, c'est-à-dire un lien vers la page courante. La règle de
           `NavigationContexte` fait le reste : une entrée sans destination ne
           se dessine pas. */
        onDemanderProduit: vue.nom === "demander" ? undefined : ouvrirDemande,
        onMesCommandes: () => {
          setOnglet("commandes");
          setEcran({ nom: "mes-commandes" });
        },
        onMesDemandes: () => {
          setOnglet("profil");
          setEcran({ nom: "mes-demandes" });
        },
        onDevenirGroupeur,
      }}
    >
    <div
      className={
        estBureau
          ? "min-h-dvh bg-white"
          : "relative mx-auto min-h-dvh max-w-[430px] bg-white"
      }
    >
      {/* L'en-tete du site, permanent sur ordinateur : on doit pouvoir revenir
          au catalogue depuis n'importe quel ecran. */}
      {estBureau ? (
        <EnTeteBureau
          recherche={filtres.recherche}
          onRecherche={(recherche) => {
            setFiltres({ ...filtres, recherche });
            setEcran({ nom: "catalogue" });
          }}
          /* Même raison que pour le pied de page : sur l'écran de demande,
             ce bouton menait à la page courante, avec le poids visuel du
             bouton d'envoi. `EnTeteBureau` ne le dessine pas sans
             destination. */
          onDemander={vue.nom === "demander" ? undefined : ouvrirDemande}
          notifications={cloche.nonLues}
          onNotifications={cloche.ouvrir}
          onMenu={() => setMenuOuvert(true)}
          menuOuvert={menuOuvert}
          onAccueil={() => {
            setFiltres(FILTRES_PAR_DEFAUT);
            setEcran({ nom: "catalogue" });
          }}
        />
      ) : null}

      {vue.nom === "fil" ? (
        <Fil
          onOuvrirGroupage={ouvrirGroupage}
          onRechercher={ouvrirLaRecherche}
          onQuestions={(groupage) => setEcran({ nom: "questions", groupage })}
          onPartager={partagerLeGroupage}
          onDemanderProduit={ouvrirDemande}
        />
      ) : null}

      {vue.nom === "catalogue" ? (
        <GroupagesOuverts
          rechercheDepliee={rechercheDemandee}
          estBureau={estBureau}
          filtres={filtres}
          onFiltres={setFiltres}
          onOuvrirGroupage={ouvrirGroupage}
          onDemanderProduit={ouvrirDemande}
        />
      ) : null}

      {vue.nom === "groupage" ? (
        <DetailGroupage
          groupage={vue.groupage}
          estBureau={estBureau}
          onRetour={() =>
            setEcran({
              nom: !estBureau && onglet === "accueil" ? "fil" : "catalogue",
            })
          }
          onCommander={() => demanderCommande(vue.groupage)}
          /*
           * ⚠️ **Le panneau sur ordinateur, l'ecran sur telephone.**
           *
           * Poser une question fait quitter la fiche, et c'est le mauvais
           * moment : on la pose parce qu'on hesite a commander. Le panneau
           * laisse le produit derriere lui.
           *
           * Sur 390 px, en revanche, un panneau dans un coin n'est pas un
           * coin : il couvrirait la fiche sans rien laisser voir, pour un
           * resultat moins lisible que l'ecran plein qui existe deja.
           */
          onQuestions={() =>
            estBureau
              ? setQuestionsOuvertes(vue.groupage)
              : setEcran({ nom: "questions", groupage: vue.groupage })
          }
          questionsOuvertes={questionsOuvertes !== undefined}
          onPartager={() => partagerLeGroupage(vue.groupage)}
          onOuvrirGroupage={ouvrirGroupage}
          /*
           * Les groupages proposes sous la fiche.
           *
           * ⚠️ **Meme categorie d'abord, et le catalogue ne contient que
           * de l'ouvert** (ecran 2) : on ne propose donc jamais un groupage
           * qu'on ne peut plus rejoindre. Si la categorie n'a rien d'autre a
           * offrir, on complete avec le reste plutot que de n'afficher
           * qu'une carte seule — une rangee d'un seul element ressemble a un
           * defaut d'affichage.
           */
          similaires={similaires}
        />
      ) : null}

      {/* L'ecran 5 reste monte pendant la connexion : quantite, variante,
          position et repere survivent a la feuille (§1.5). */}
      {vue.nom === "commander" ? (
        <Commander
          groupage={vue.groupage}
          /* Son adresse habituelle, modifiable : on se fait livrer ailleurs
             un jour sur dix. */
          adresseConnue={
            profil?.quartier
              ? { quartier: profil.quartier, repere: profil.repere }
              : undefined
          }
          estBureau={estBureau}
          telephoneConnu={identite?.telephone}
          onRetour={() => setEcran({ nom: "groupage", groupage: vue.groupage })}
          onPayer={demanderPaiement}
        />
      ) : null}

      {vue.nom === "paiement" ? (
        <Paiement
          brouillon={vue.brouillon}
          estBureau={estBureau}
          telephoneCompte={identite?.telephone}
          onRetour={() =>
            setEcran({ nom: "commander", groupage: vue.brouillon.groupage })
          }
          onPaye={async () => {
            try {
              const commande = await payer({
                campagne: vue.brouillon.groupage.id,
                /* Le numero **de livraison** saisi a l'ecran 5, qui peut
                   differer de celui du compte. L'acheteur, lui, est identifie
                   par son jeton de session. */
                telephone: vue.brouillon.telephone || undefined,
                quantite: vue.brouillon.quantite,
                variante: vue.brouillon.variante,
                /* La position est **conservee sur la commande** (§6 du
                   PRD) : c'est elle qui determinera les frais de livraison
                   reels, et c'est aussi ce que le livreur suivra. */
                quartier: vue.brouillon.position.quartier,
                repere: vue.brouillon.position.repere,
                /* ⚠️ **Generee une fois par brouillon, pas par tentative.**
                   C'est elle qui fait qu'un double appui — ou un reessai
                   apres une coupure — n'encaisse qu'une seule fois : le
                   serveur reconnait la cle et renvoie la commande existante
                   au lieu d'en creer une seconde. La regenerer ici
                   supprimerait toute la protection. */
                cle_idempotence: vue.brouillon.cleIdempotence,
              });

              setCommandesPassees((nombre) => nombre + 1);
              setEcran({
                nom: "confirmation",
                commande: {
                  ...vue.brouillon,
                  id: String(commande.id),
                  /* Le code de livraison vient **du serveur** : c'est lui qui
                     le garantit unique, et c'est celui que le livreur
                     demandera. En generer un dans le navigateur donnerait a
                     l'acheteur un code que personne ne reconnaitrait. */
                  codeLivraison: commande.code_livraison,
                  statut: "payee",
                  passeeLe: commande.passee_le.slice(0, 10),
                },
              });
              return undefined;
            } catch (cause) {
              return cause instanceof ErreurApi
                ? cause.messageLisible
                : "Le paiement n'a pas abouti. Réessayez.";
            }
          }}
        />
      ) : null}

      {vue.nom === "confirmation" ? (
        <Confirmation
          commande={vue.commande}
          estBureau={estBureau}
          /*
           * ⚠️ **« Modifier » renvoie au suivi, pas a l'ecran de commande.**
           *
           * Le bouton ne faisait rien, et le rebrancher sur l'ecran 5 aurait
           * ete pire : cet ecran prepare un **nouveau** paiement. On aurait
           * donc propose de « modifier » une adresse et fait payer une
           * seconde part. La commande est deja passee ; c'est depuis son
           * suivi (ecran 9) qu'on la corrige, tant que le groupage n'est pas
           * cloture.
           */
          onModifierAdresse={() => {
            setOnglet("commandes");
            setEcran({ nom: "commande", commande: vue.commande });
          }}
          onSuivre={() => {
            setOnglet("commandes");
            setEcran({ nom: "commande", commande: vue.commande });
          }}
          onFermer={ouvrirCatalogue}
        />
      ) : null}

      {vue.nom === "mes-commandes" ? (
        <MesCommandes
          estBureau={estBureau}
          connecte={connecte}
          telephone={identite?.telephone}
          onOuvrirCommande={(commande) =>
            setEcran({ nom: "commande", commande })
          }
          onVoirGroupages={ouvrirCatalogue}
          onSeConnecter={() => setConnexionDemandee(true)}
        />
      ) : null}

      {vue.nom === "commande" ? (
        <DetailCommande
          commande={vue.commande}
          estBureau={estBureau}
          onRetour={() => {
            setOnglet("commandes");
            setEcran({ nom: "mes-commandes" });
          }}
          onQuestions={() =>
            setEcran({ nom: "questions", groupage: vue.commande.groupage })
          }
          /*
           * ⚠️ **On relit la commande, on ne devine pas son nouvel etat.**
           *
           * Ecrire `statut: "litige"` localement aurait suffi a l'affichage et
           * aurait menti a la premiere divergence : c'est le serveur qui
           * decide ce qu'un refus produit, et il pourrait demain ouvrir autre
           * chose qu'un litige. On redemande donc la liste et on reprend la
           * ligne correspondante.
           *
           * Un echec de relecture **ne fait rien** : le refus, lui, est bien
           * enregistre, et la feuille vient de le confirmer. Afficher une
           * erreur ici ferait croire le contraire.
           */
          onRefuse={() => {
            listerMesCommandes()
              .then((brutes) => {
                const relue = brutes.find(
                  (brute) => String(brute.id) === vue.commande.id,
                );
                /* ⚠️ On passe **le groupage qu'on a deja**, et non le
                   catalogue : une commande en livraison appartient par
                   definition a un groupage cloture, donc absent du catalogue
                   — `adapterCommande` ne le trouverait pas et rendrait
                   `undefined`. Le groupage, lui, n'a pas change : seul le
                   statut de la commande vient d'etre modifie. */
                const adaptee = relue
                  ? adapterCommande(relue, [vue.commande.groupage])
                  : undefined;
                if (adaptee) {
                  setEcran({ nom: "commande", commande: adaptee });
                }
              })
              .catch(() => {});
          }}
        />
      ) : null}

      {vue.nom === "questions" ? (
        <Questions
          groupage={vue.groupage}
          estBureau={estBureau}
          telephone={identite?.telephone}
          onRetour={() => setEcran({ nom: "groupage", groupage: vue.groupage })}
          /* Poser une question demande un compte, le lire non (§1.5). La
             feuille de connexion s'ouvre donc au moment de l'envoi. */
          /* ⚠️ **La porte, comme dans le panneau de questions.** L'ecran 10
             passait encore par la feuille de connexion nue : le message qui
             explique pourquoi un compte est necessaire n'apparaissait que
             dans le panneau. Deux chemins vers la meme action, deux
             experiences differentes. */
          onSeConnecter={() => demanderUnCompte("question")}
        />
      ) : null}

      {vue.nom === "demander" ? (
        <DemanderProduit
          estBureau={estBureau}
          connecte={connecte}
          onRetour={ouvrirCatalogue}
          /* ⚠️ **L'onglet se recale, et il le faut depuis que « Demander »
             en a un.** On atterrit sur « Mes demandes », qui vit sous
             « Profil » : sans cette ligne, l'onglet « Demander » resterait
             allume sur un ecran qui n'est pas le sien. Avant, `ouvrirDemande`
             posait deja « profil », donc c'etait juste par hasard. */
          onEnvoyee={() => {
            setOnglet("profil");
            setEcran({ nom: "mes-demandes" });
          }}
          /* ⚠️ L'ecran 11 **reste monte** derriere la feuille : c'est ce qui
             preserve la saisie et la photo deja reduite. Le §1.5 ne demande
             pas seulement de ne pas montrer de mur, il demande que fermer la
             feuille ne coute rien. */
          onConnexionRequise={() => setConnexionDemandee(true)}
        />
      ) : null}

      {vue.nom === "mes-demandes" ? (
        <MesDemandes
          estBureau={estBureau}
          connecte={connecte}
          onDemanderProduit={ouvrirDemande}
          onOuvrirGroupage={(id) => {
            const groupage = groupages.find((g) => g.id === id);
            if (groupage) {
              ouvrirGroupage(groupage);
            }
          }}
          onSeConnecter={() => setConnexionDemandee(true)}
        />
      ) : null}

      {vue.nom === "profil" ? (
        <PageProfil
          estBureau={estBureau}
          connecte={connecte}
          profil={profil}
          /* Droit au formulaire, sans passer par le message : quelqu'un qui
             appuie sur « Creer mon compte » n'a pas besoin qu'on lui explique
             pourquoi un compte est utile — il vient de le demander. Le
             message ne sert qu'a interrompre une operation en cours. */
          onCreerUnCompte={() =>
            setPorte({ operation: "compte", etape: "inscription" })
          }
          /* Les commandes n'etaient atteignables que par la barre du bas,
             qui n'existe pas sur ordinateur : depuis son profil, un visiteur
             de bureau n'avait aucun chemin vers elles. */
          onMesCommandes={() => {
            setOnglet("commandes");
            setEcran({ nom: "mes-commandes" });
          }}
          onMesDemandes={() => setEcran({ nom: "mes-demandes" })}
          onDemanderProduit={ouvrirDemande}
          onSeConnecter={() => setConnexionDemandee(true)}
          onProfilMisAJour={(misAJour: Profil) => {
            setProfil(misAJour);
            /* L'identite porte le nom affiche ailleurs dans l'application :
               la laisser en arriere ferait reapparaitre l'ancien nom a
               l'ecran de commande. */
            setIdentite({
              telephone: misAJour.telephone,
              nom: misAJour.nom || undefined,
            });
          }}
          onSeDeconnecter={() => {
            void seDeconnecter();
            poserLeJetonAcheteur("");
            setIdentite(undefined);
            setProfil(undefined);
            /* On reste sur l'onglet : il montre alors son etat vide du §1.5,
               ce qui est la reponse honnete a « je viens de me deconnecter ».
               Renvoyer au fil ferait croire a une erreur. */
          }}
        />
      ) : null}

      {/* ⚠️ **La porte du compte — une seule à la fois, par construction.**
          Les trois branches lisent le même `porte.etape`, donc il est
          impossible d'en afficher deux : c'est ce qui empêche de superposer un
          message et un formulaire, où fermer celui du dessus découvrirait le
          second sans qu'on comprenne pourquoi.

          Le rappel de contexte ne porte **que le produit et le prix de la
          part** : a cet instant l'acheteur n'a choisi ni quantite ni variante,
          donc il n'y a pas de total a annoncer. Ecrire « 1 part » serait une
          quantite qu'il n'a pas demandee. */}
      {porte?.etape === "invite" ? (
        <InviteCompte
          operation={porte.operation}
          onCreerUnCompte={() => setPorte({ ...porte, etape: "inscription" })}
          onSeConnecter={() => setPorte({ ...porte, etape: "connexion" })}
          onFermer={() => setPorte(undefined)}
        />
      ) : null}

      {porte?.etape === "inscription" ? (
        <FeuilleInscription
          motif={
            porte.groupage
              ? `Vous rejoignez : ${porte.groupage.produit} — ${formaterFrancs(porte.groupage.prixPart)} la part`
              : undefined
          }
          onFermer={() => setPorte(undefined)}
          onSeConnecter={() => setPorte({ ...porte, etape: "connexion" })}
          onInscrit={franchirLaPorte}
        />
      ) : null}

      {porte?.etape === "connexion" ? (
        <FeuilleConnexion
          rappelContexte={
            porte.groupage
              ? `Vous rejoignez : ${porte.groupage.produit} — ${formaterFrancs(porte.groupage.prixPart)} la part`
              : "Votre question sera publiée sous votre compte."
          }
          /* Aucune adresse : il ne l'a pas encore saisie. C'est toute la
             difference avec la feuille du paiement ci-dessous, qui transmet
             celle de l'ecran 5 pour en faire l'adresse par defaut du compte. */
          onFermer={() => setPorte(undefined)}
          onConnecte={franchirLaPorte}
        />
      ) : null}

      {/* Ecran 4 — la feuille monte par-dessus l'ecran en cours. */}
      {enAttenteDeConnexion ? (
        <FeuilleConnexion
          rappelContexte={`Vous commandez : ${enAttenteDeConnexion.groupage.produit} — ${enAttenteDeConnexion.quantite} part${
            enAttenteDeConnexion.quantite > 1 ? "s" : ""
          }, ${formaterFrancs(enAttenteDeConnexion.total)}`}
          /* ⚠️ L'adresse qu'il vient de saisir à l'écran 5. Elle part avec le
             code et devient son adresse par défaut : on ne lui demande rien
             de plus, et sa prochaine commande arrivera pré-remplie. */
          adresse={{
            quartier: enAttenteDeConnexion.position.quartier,
            repere: enAttenteDeConnexion.position.repere,
          }}
          onFermer={() => setEnAttenteDeConnexion(undefined)}
          onConnecte={(nouvelleIdentite) => {
            setIdentite(nouvelleIdentite);
            const brouillon = enAttenteDeConnexion;
            setEnAttenteDeConnexion(undefined);
            rafraichirLeProfil();
            // L'action reprend seule : la feuille redescend sur le paiement.
            setEcran({ nom: "paiement", brouillon });
          }}
        />
      ) : null}

      {/* Le panneau de questions, pose sur la page courante. */}
      {questionsOuvertes ? (
        <PanneauQuestions
          groupage={questionsOuvertes}
          telephone={identite?.telephone}
          onFermer={() => setQuestionsOuvertes(undefined)}
          /* ⚠️ **La porte, pas la feuille de connexion nue.** Quelqu'un qui
             vient d'écrire une question et voit surgir un formulaire de
             connexion sans un mot d'explication croit avoir perdu son texte.
             Le message dit pourquoi un compte est nécessaire — la réponse du
             groupeur lui revient par là — et le panneau reste monté derrière,
             donc le texte saisi est intact. */
          onSeConnecter={() => demanderUnCompte("question")}
        />
      ) : null}

      {/* Ecran 4, sans rien a reprendre : le lien du §1.5. */}
      {cloche.ouvert ? (
        <PanneauNotifications
          notifications={cloche.notifications}
          chargement={cloche.chargement}
          erreur={cloche.erreur}
          onRecharger={cloche.recharger}
          onFermer={cloche.fermer}
          /*
           * ⚠️ **Une notification mene a ce dont elle parle, et a rien
           * d'autre.** Une cloche dont les lignes ne sont pas cliquables est
           * une cloche qu'on lit une fois : on apprend que le groupage est
           * cloture, et on doit ensuite retrouver sa commande a la main.
           *
           * L'ordre n'est pas arbitraire. La commande d'abord quand il y en a
           * une — c'est la que vivent le suivi et le code de livraison, donc
           * ce qu'on cherche apres « votre commande est arrivee ». La fiche
           * du produit sinon, qui porte les questions publiques et donc la
           * reponse du groupeur.
           */
          onOuvrir={(notification) => {
            cloche.fermer();
            void ouvrirDepuisUneNotification(notification);
          }}
        />
      ) : null}

      {/*
       * ⚠️ **Monte sans condition sur `estBureau`**, a la difference de
       * `EnTeteBureau` : il se referme de lui-meme quand la fenetre retrecit,
       * puisque seul le bouton de l'en-tete de bureau peut l'ouvrir. Le
       * conditionner ici demonterait le panneau pendant qu'il est ouvert si
       * l'on redimensionne — et React perdrait alors le verrou de defilement
       * pose sur le corps de page, qui resterait fige.
       */}
      <MenuPrincipal
        ouvert={menuOuvert}
        onFermer={() => setMenuOuvert(false)}
        actif={
          vue.nom === "catalogue"
            ? "catalogue"
            : vue.nom === "mes-commandes"
              ? "mes-commandes"
              : vue.nom === "mes-demandes"
                ? "mes-demandes"
                : vue.nom === "profil"
                  ? "profil"
                  : undefined
        }
        connecte={connecte}
        nom={identite?.nom}
        telephone={identite?.telephone}
        onAller={(destination: DestinationMenu) => {
          switch (destination) {
            case "accueil":
              setFiltres(FILTRES_PAR_DEFAUT);
              return ouvrirCatalogue();
            case "catalogue":
              return ouvrirCatalogue();
            case "mes-commandes":
              setOnglet("commandes");
              return setEcran({ nom: "mes-commandes" });
            case "mes-demandes":
              setOnglet("profil");
              return setEcran({ nom: "mes-demandes" });
            case "profil":
              setOnglet("profil");
              return setEcran({ nom: "profil" });
          }
        }}
        onSeConnecter={() => setConnexionDemandee(true)}
        onSeDeconnecter={() => {
          void seDeconnecter();
          poserLeJetonAcheteur("");
          setIdentite(undefined);
          setProfil(undefined);
        }}
      />

      <Fugitif message={message} />

      {/* ⚠️ Les deux autres feuilles l'emportent : elles ont **quelque chose
          a reprendre** apres la connexion, celle-ci n'a rien. Deux feuilles
          superposees laisseraient l'acheteur fermer celle du dessus et
          decouvrir la seconde, sans comprendre. */}
      {connexionDemandee && !enAttenteDeConnexion && !porte ? (
        <FeuilleConnexion
          rappelContexte="Connectez-vous pour retrouver vos commandes, vos demandes et votre adresse de livraison."
          onFermer={() => setConnexionDemandee(false)}
          onConnecte={(nouvelleIdentite) => {
            setIdentite(nouvelleIdentite);
            setConnexionDemandee(false);
            rafraichirLeProfil();
          }}
        />
      ) : null}

      {/* La barre du bas est un composant mobile : sur ordinateur, c'est
          l'en-tete et le pied de page qui portent la navigation. */}
      {!estBureau && ECRANS_AVEC_BARRE_NAV.includes(vue.nom) ? (
        <BarreNav
          actif={onglet}
          commandesEnCours={commandesPassees}
          onChanger={(nouvelOnglet) => {
            setOnglet(nouvelOnglet);
            switch (nouvelOnglet) {
              case "accueil":
                return setEcran({ nom: "fil" });
              case "groupage":
                return setEcran({ nom: "catalogue" });
              case "demander":
                return setEcran({ nom: "demander" });
              case "commandes":
                return setEcran({ nom: "mes-commandes" });
              case "profil":
                return setEcran({ nom: "profil" });
            }
          }}
        />
      ) : null}
    </div>
    </FournisseurNavigation>
  );
}
