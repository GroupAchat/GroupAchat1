import { useMemo, useState } from "react";
import ApplicationAcheteur from "./acheteur/ApplicationAcheteur";
import ApplicationGroupeur from "./groupeur/ApplicationGroupeur";
import {
  ecrireProfil,
  ecrireTelephoneGroupeur,
  lireProfil,
  lireTelephoneGroupeur,
} from "./domaine/profil";
import useEstBureau from "./hooks/useEstBureau";
import type { MonDossierApi } from "./api/dossiers";
import { type Role, roleDepuisAdresse } from "./domaine/role";
import { groupageDepuisAdresse } from "./domaine/partage";
import ChoixProfil from "./pages/ChoixProfil";
import Inscription from "./groupeur/pages/Inscription";
import PageDemarrage from "./pages/PageDemarrage";
import TourneeLivreur from "./livreur/pages/TourneeLivreur";

/**
 * Le point d'entree de **la boutique** : acheteur, groupeur, livreur.
 *
 * | Role | Ecrans | Chrome | Comment on y entre, en vrai |
 * |---|---|---|---|
 * | **Acheteur** | 0 a 12 | Orange | On ouvre le site, on repond a l'ecran de profil |
 * | **Groupeur** | 13 a 21 | **Bleu** | Meme porte, puis inscription et dossier KYC |
 * | **Livreur** | 22 | Neutre, page isolee | On ouvre un lien recu le matin |
 *
 * **L'administration n'est plus ici.** L'ecran A1 a sa propre application, sur
 * le port 5174 (`admin.html`, `src/admin/main.tsx`, `vite.admin.config.ts`).
 * La raison est de fond et non technique : un acheteur peut devenir groupeur,
 * c'est meme le mouvement que le produit cherche — mais **personne ne passe
 * d'acheteur a administrateur.** Les trois consequences concretes de cette
 * separation sont detaillees dans l'en-tete de `src/admin/main.tsx`.
 *
 * ## Le parcours d'ouverture
 *
 * ```
 * Telephone : demarrage → choix du profil → « Je veux acheter »        → le fil
 *                          (une seule fois)  « Je veux etre groupeur » → inscription → tableau de bord
 * Ordinateur :            choix du profil → idem
 *                          (une seule fois)
 * ```
 *
 * **Le choix du profil est desormais demande sur ordinateur aussi**, alors
 * qu'il etait auparavant saute au-dela de 768 px. Ce changement repare un
 * trou reel : sur grand ecran, il n'existait **aucun chemin** vers le cote
 * groupeur hors du selecteur de demonstration. Un visiteur venu lancer des
 * groupages depuis son ordinateur arrivait sur le catalogue et n'avait pas de
 * porte.
 *
 * ⚠️ **Et c'est en tension avec le §1.5**, qui demande qu'on arrive
 * **directement** sur le fil a la premiere ouverture et range « un ecran au
 * lancement » parmi les choses a ne jamais dessiner. La tension existait deja
 * sur telephone ; elle s'etend maintenant au bureau, ou l'argument du §1.5 est
 * le plus fort — un site marchand s'ouvre sur son catalogue, pas sur une
 * question. Trois choses la bornent, et si l'une saute l'ecran redevient le
 * mur que le §1.5 interdit :
 *
 * - **le chemin acheteur ne demande rien** : un clic, et on est sur le
 *   catalogue. Pas de compte, pas de numero. C'est un aiguillage, pas un mur
 *   d'authentification ;
 * - **il est propose en premier et en bouton plein**, l'autre en contour ;
 * - **il ne vient qu'une fois.** C'est ce que `domaine/profil.ts` garantit en
 *   retenant le choix hors de React. Avant, l'ecran revenait a chaque
 *   rechargement, ce qui violait cette troisieme condition sans que personne
 *   ne l'ait decide.
 *
 * **Le livreur n'entre pas par le meme chemin que les deux autres.** Un
 * acheteur et un groupeur repondent a l'ecran de profil ; un livreur ouvre un
 * lien recu le matin, qui ne couvre que la tournee du jour. C'est pourquoi son
 * ecran se demande par l'adresse — `?role=livreur` — et non par un choix dans
 * l'interface : on ne « devient » pas livreur.
 *
 * Le jour ou les liens de tournee seront signes, c'est ce meme chemin qui
 * portera le jeton, et `domaine/role.ts` est l'endroit ou le lire.
 *
 * ⚠️ **Ne jamais inverser les chromes** (§1.2). Un ecran groupeur avec un
 * bouton orange, ou un ecran acheteur avec un onglet actif bleu, casse le seul
 * repere permanent qu'ont les deux publics.
 */

/** Les etapes d'ouverture, avant d'entrer dans l'un des trois produits. */
type Ouverture = "demarrage" | "choix" | "inscription" | "entre";

export default function App() {
  const estBureau = useEstBureau();

  /**
   * Lu **une seule fois** au montage, et jamais relu ensuite.
   *
   * `useMemo` sans dependance, et non un appel direct dans le corps : le corps
   * d'un composant est reexecute a chaque rendu, et sous `StrictMode` deux
   * fois de suite au montage. Une lecture de `localStorage` par rendu serait
   * du travail inutile, et surtout l'etat initial ci-dessous doit etre calcule
   * sur **la meme** valeur que l'etape d'ouverture, sans quoi les deux
   * pourraient se contredire.
   */
  const profilRetenu = useMemo(() => lireProfil(), []);

  /**
   * Un `?role=livreur` dans l'adresse l'emporte sur le profil retenu.
   *
   * L'ordre compte : quelqu'un qui a deja navigue comme acheteur, puis qui
   * ouvre le lien de tournee qu'on vient de lui envoyer, doit arriver sur sa
   * tournee — pas sur le fil, en se demandant pourquoi le lien ne marche pas.
   */
  const roleDemande = useMemo(() => roleDepuisAdresse(), []);

  /**
   * Un `?groupage=` dans l'adresse : quelqu'un a recu le lien d'une fiche.
   *
   * ⚠️ **Il saute l'ecran de choix de profil**, et c'est le cas ou le §1.5 est
   * le plus imperatif : on arrive d'une conversation WhatsApp, sur un produit
   * precis, souvent pour la premiere fois. Poser « voulez-vous acheter ou
   * devenir groupeur ? » devant un produit qu'on vient nous recommander est
   * exactement le mur que ce paragraphe interdit — et c'est aussi le meilleur
   * moyen de perdre la visite.
   *
   * On **ne retient pas** ce profil, a la difference du bouton « Je veux
   * acheter » : personne n'a choisi, donc rien n'a ete decide. L'ecran de
   * choix reviendra a la prochaine ouverture sans lien.
   */
  const ficheDemandee = useMemo(() => groupageDepuisAdresse(), []);

  const [role, setRole] = useState<Role>(
    roleDemande ?? (ficheDemandee ? "acheteur" : undefined) ?? profilRetenu ?? "acheteur",
  );

  /**
   * Qui a deja choisi entre directement, sur telephone comme sur ordinateur.
   * C'est la troisieme condition du §1.5 : l'ecran ne vient qu'une fois.
   */
  const [ouverture, setOuverture] = useState<Ouverture>(
    roleDemande || ficheDemandee || profilRetenu ? "entre" : "demarrage",
  );

  /**
   * Sur grand ecran, **la page de demarrage est sautee, mais plus le choix de
   * profil.** Un ecran de lancement plein avec un logo est un usage
   * d'application mobile : sur un ordinateur il ne represente rien, puisqu'il
   * n'y a aucun temps de demarrage a couvrir. L'aiguillage, lui, repond a une
   * question que le visiteur de bureau se pose aussi.
   */
  const etape: Ouverture =
    estBureau && ouverture === "demarrage" ? "choix" : ouverture;

  /** Entrer dans la boutique en retenant le profil, pour ne plus reposer la question. */
  const entrerCommeAcheteur = () => {
    ecrireProfil("acheteur");
    setRole("acheteur");
    setOuverture("entre");
  };

  /**
   * Le numero avec lequel le dossier KYC a ete depose (§10.5).
   *
   * ⚠️ **C'est une cle de lecture, pas un etat.** L'etat du dossier appartient
   * au serveur : `ApplicationGroupeur` le relit a chaque ouverture avec ce
   * numero. Retenir l'etat lui-meme dans le navigateur laisserait un groupeur
   * refuse se declarer valide en modifiant son stockage local — le verrou de
   * `Campagne.save()` l'arreterait cote serveur, mais seulement apres lui
   * avoir fait remplir tout un formulaire pour rien.
   *
   * Vide pour un groupeur **deja valide**, qui est le cas de toutes les
   * sessions suivantes : le numero s'efface des que le dossier est valide,
   * puisqu'il n'y a plus de reponse a attendre.
   */
  const [telephoneGroupeur, setTelephoneGroupeur] = useState(
    lireTelephoneGroupeur,
  );

  /**
   * Ce que l'inscription vient de deposer — pour l'afficher sans attendre.
   *
   * L'ecran suivant pourrait tout relire depuis l'API, mais il ferait alors
   * patienter devant un squelette quelqu'un qui vient a l'instant de recevoir
   * sa reponse. On affiche ce que le serveur a deja dit, et la relecture
   * prendra le relais.
   */
  const [dossierFrais, setDossierFrais] = useState<MonDossierApi>();

  const entrerCommeGroupeur = (depot: {
    courriel: string;
    pseudonyme: string;
    telephone: string;
    dossier: MonDossierApi;
  }) => {
    ecrireProfil("groupeur");
    ecrireTelephoneGroupeur(depot.telephone);
    setTelephoneGroupeur(depot.telephone);
    setDossierFrais(depot.dossier);
    setRole("groupeur");
    setOuverture("entre");
  };

  return (
    <>
      {etape === "demarrage" ? (
        <PageDemarrage onTermine={() => setOuverture("choix")} />
      ) : null}

      {etape === "choix" ? (
        <ChoixProfil
          onAcheteur={entrerCommeAcheteur}
          onGroupeur={() => setOuverture("inscription")}
        />
      ) : null}

      {etape === "inscription" ? (
        <Inscription
          onRetour={() => setOuverture("choix")}
          onTermine={entrerCommeGroupeur}
        />
      ) : null}

      {etape === "entre" ? (
        <>
          {role === "acheteur" ? (
            <ApplicationAcheteur
              /* ⚠️ **Il change de produit, pas d'ecran.** Le pied de page
                 propose « Devenir groupeur » ; le cote groupeur a son propre
                 chrome et son propre routeur, donc seul `App` peut basculer.
                 Il mene au depot de dossier (ecran 13), pas directement au
                 tableau de bord : le KYC du §10.5 reste la porte. */
              onDevenirGroupeur={() => setOuverture("inscription")}
            />
          ) : null}
          {role === "groupeur" ? (
            <ApplicationGroupeur
              telephone={telephoneGroupeur}
              dossierFrais={dossierFrais}
              onDossierValide={() => {
                /* ⚠️ **On garde son numero.** Il n'identifiait pas que le
                   dossier KYC : c'est la cle de lecture de tout son espace de
                   travail — campagnes, portefeuille, questions. L'effacer
                   ici vidait son tableau de bord au moment precis ou il
                   devenait utile. On oublie seulement le depot provisoire,
                   dont la relecture a pris le relais. */
                setDossierFrais(undefined);
              }}
              onReprendreLeDossier={() => setOuverture("inscription")}
            />
          ) : null}
          {role === "livreur" ? <TourneeLivreur /> : null}
        </>
      ) : null}
    </>
  );
}
