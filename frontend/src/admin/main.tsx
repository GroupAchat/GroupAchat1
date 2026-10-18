import { StrictMode, useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "../index.css";
import { lireLeTableauDeBordAdmin } from "../api/administration";
import { useRequete } from "../api/useRequete";
import {
  lireLaSession,
  oublierLaSession,
  retenirLaSession,
} from "./jeton";
import { seDeconnecter, type SessionAdmin } from "../api/sessionAdmin";
import Sidebar, { type EcranAdmin } from "./mise-en-page/Sidebar";
import DemandeJeton from "./pages/DemandeJeton";
import DossiersKyc from "./pages/DossiersKyc";
import Groupages from "./pages/Groupages";
import TableauDeBordAdmin from "./pages/TableauDeBordAdmin";
import Retraits from "./pages/Retraits";

/**
 * Le point d'entree de l'administration — **une application a part.**
 *
 * ## Pourquoi un autre port, et pas un quatrieme role dans `App.tsx`
 *
 * L'administration etait a l'origine un role du selecteur de demonstration, a
 * cote de l'acheteur et du groupeur. C'etait commode et faux sur le fond :
 * **personne ne passe d'acheteur a administrateur.** Les deux publics du
 * produit entrent par la meme porte et peuvent changer d'avis — un acheteur
 * devient groupeur — tandis que l'administrateur est un employe de Group
 * Achat, dont l'outil n'a aucune raison d'etre servi par le meme programme que
 * la boutique.
 *
 * Les separer a trois consequences concretes :
 *
 * - **le code d'administration ne part pas dans le paquet du public.** Les
 *   deux constructions sont independantes (`dist/` et `dist-admin/`) : les
 *   montants detenus, les files de travail et les libelles d'alertes ne sont
 *   plus telecharges par chaque acheteur de Lome, sur un forfait limite ;
 * - **on peut fermer l'administration au reseau** sans toucher a la boutique.
 *   Deux ports, c'est deux regles de pare-feu possibles ;
 * - **plus de chemin, meme de demonstration, entre la boutique et l'outil
 *   interne.**
 *
 * ## Les ecrans
 *
 * | | Ecran | Fichier |
 * |---|---|---|
 * | A1 | Tableau de bord | `pages/TableauDeBordAdmin` |
 * | A2 | Dossiers KYC | `pages/DossiersKyc` |
 * | A3 | Retraits des groupeurs | `pages/Retraits` |
 * | A4 | Groupages, tous etats | `pages/Groupages` |
 *
 * ⚠️ **Le port different n'est pas une mesure de securite.** Il n'authentifie
 * personne, et il ne faut jamais compter dessus. Ce qui ferme ces ecrans est
 * la **connexion par identifiant et mot de passe** demandee a l'entree — voir
 * `api/sessionAdmin.ts`.
 *
 * ⚠️ Ce paragraphe ajoutait : *« et ce jeton lui-meme ne distingue pas deux
 * administrateurs »*. C'etait vrai du jeton partage qu'on recopiait depuis le
 * `.env` du serveur ; ce ne l'est plus. Chaque administrateur a son compte, sa
 * session, et signe les decisions KYC de son nom.
 */

/**
 * Le routeur — quatre ecrans derriere une barre laterale.
 *
 * Un `useState` suffit : l'outil interne n'a pas d'adresse profonde, et il ne
 * doit pas en avoir. Pouvoir envoyer par message le lien d'un dossier serait
 * une mauvaise idee — ces adresses porteraient un identifiant de personne.
 *
 * ## Le jeton est demande une fois, a l'entree
 *
 * ⚠️ **Il ne l'etait auparavant qu'a l'ouverture de l'ecran A2**, et c'etait
 * defendable tant que le tableau de bord lisait des constantes locales : il
 * n'affichait alors que des compteurs, aucune donnee personnelle. Ce n'est
 * plus vrai — il interroge `/api/administration/`, qui voit les montants
 * detenus, les groupeurs et leurs numeros Mobile Money.
 *
 * La porte est donc remontee a l'entree. Mieux vaut une serrure la ou commence
 * ce qu'elle protege.
 */
function Administration() {
  const [ecran, setEcran] = useState<EcranAdmin>("tableau-de-bord");
  const [session, setSession] = useState(lireLaSession);
  const [jetonRefuse, setJetonRefuse] = useState(false);
  const jeton = session?.jeton ?? "";

  const ouvrirLaSession = (nouvelle: SessionAdmin) => {
    retenirLaSession(nouvelle);
    setSession(nouvelle);
    setJetonRefuse(false);
  };

  /* La deconnexion volontaire, par le bouton de la barre laterale.
     ⚠️ **Elle ferme la session cote serveur**, et c'est tout l'interet par
     rapport a l'ancien jeton partage : oublier une valeur dans le navigateur
     ne la rendait pas invalide, elle restait bonne pour qui l'avait notee.
     Ici la session est detruite en base.
     Le `catch` est vide a dessein : si l'appel echoue — serveur injoignable,
     session deja expiree — on oublie quand meme le jeton localement. Refuser
     de deconnecter quelqu'un parce que le reseau est coupe serait le pire des
     comportements sur un poste partage. */
  const fermerLaSession = useCallback(() => {
    const actuelle = lireLaSession();
    if (actuelle) {
      void seDeconnecter(actuelle.jeton).catch(() => {});
    }
    oublierLaSession();
    setSession(null);
    setJetonRefuse(false);
  }, []);

  /* `useCallback` : cette fonction part en dependance d'effets dans les
     ecrans, et une nouvelle reference a chaque rendu les relancerait en
     boucle. */
  /* Le refus subi : le serveur a repondu 401, donc la session est deja morte
     cote serveur — expiration des douze heures, ou `is_staff` retire. Rien a
     fermer, seulement a oublier. */
  const refuserLeJeton = useCallback(() => {
    oublierLaSession();
    setSession(null);
    setJetonRefuse(true);
  }, []);

  /**
   * Les compteurs de la barre laterale.
   *
   * Charges ici plutot que dans chaque ecran : la barre les affiche en
   * permanence, et c'est tout son interet — l'administrateur sait ou il a du
   * travail **sans ouvrir les ecrans**.
   *
   * ⚠️ Cela fait une seconde requete au tableau de bord quand c'est lui qui
   * est affiche. C'est assume : le partager demanderait un contexte, pour un
   * gain d'une requete sur un ecran interne consulte depuis un bureau — pas
   * depuis le forfait mobile que le §5 cherche a menager.
   */
  const bord = useRequete(
    (signal) => lireLeTableauDeBordAdmin(jeton, signal),
    [jeton],
    jeton !== "",
  );

  const [compteurs, setCompteurs] = useState<
    Partial<Record<EcranAdmin, { nombre: number; urgent?: boolean }>>
  >({});

  useEffect(() => {
    const donnees = bord.donnees;
    if (!donnees) {
      return;
    }
    const file = (id: string) =>
      donnees.files.find((entree) => entree.id === id)?.nombre ?? 0;

    setCompteurs({
      /* `urgent` sur les retraits seulement : c'est la seule file ou
         quelqu'un attend son argent pour pouvoir travailler. */
      retraits: {
        nombre: file("retraits"),
        urgent: file("retraits") > 0,
      },
      dossiers: { nombre: file("kyc") },
    });
  }, [bord.donnees]);

  if (!session) {
    return (
      <DemandeJeton
        onSession={ouvrirLaSession}
        erreur={
          jetonRefuse
            ? "Votre session a pris fin — douze heures écoulées, ou accès retiré. Reconnectez-vous."
            : undefined
        }
      />
    );
  }

  return (
    <Sidebar
      actif={ecran}
      compteurs={compteurs}
      onNaviguer={setEcran}
      nomAdmin={session.nom}
      onDeconnexion={fermerLaSession}
    >
      {ecran === "tableau-de-bord" ? (
        <TableauDeBordAdmin
          jeton={jeton}
          onNaviguer={setEcran}
          onJetonRefuse={refuserLeJeton}
        />
      ) : null}
      {ecran === "retraits" ? (
        <Retraits jeton={jeton} onJetonRefuse={refuserLeJeton} />
      ) : null}
      {ecran === "groupages" ? (
        <Groupages jeton={jeton} onJetonRefuse={refuserLeJeton} />
      ) : null}
      {ecran === "dossiers" ? (
        <DossiersKyc
          jeton={jeton}
          onRetour={() => setEcran("tableau-de-bord")}
          onJetonRefuse={refuserLeJeton}
        />
      ) : null}
    </Sidebar>
  );
}

const racine = document.getElementById("root");
if (!racine) {
  throw new Error("Element #root introuvable dans admin.html");
}

createRoot(racine).render(
  <StrictMode>
    <Administration />
  </StrictMode>,
);
