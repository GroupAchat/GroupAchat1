import { AnimatePresence, motion } from "framer-motion";
import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";

import { BarreOnglets, EnTete, EnTeteGroupeur, RetourEnHaut } from "@/composants/Coque";
import { RamasseurDeParrainage } from "@/composants/Parrainage";
import { FournisseurSession, useSession } from "@commun/contexte/Session";
import Accueil from "@/pages/Accueil";
import { Connexion, Inscription } from "@/pages/Authentification";
import Catalogue from "@/pages/Catalogue";
import Livraison from "@/pages/Livraison";
import Communaute from "@/pages/Communaute";
import FicheCampagne from "@/pages/FicheCampagne";
import MesAchats, { DetailAchat } from "@/pages/MesAchats";
import Messages from "@/pages/Messages";
import Notifications from "@/pages/Notifications";
import Profil, { DevenirGroupeur } from "@/pages/Profil";
import Reclamations from "@/pages/Reclamations";
import AttestationBancaire from "@/pages/groupeur/AttestationBancaire";
import CampagneGroupeur from "@/pages/groupeur/CampagneGroupeur";
import CompteOag from "@/pages/groupeur/CompteOag";
import EspaceGroupeur from "@/pages/groupeur/EspaceGroupeur";
import NouvelleCampagne from "@/pages/groupeur/NouvelleCampagne";
import PortefeuilleOag from "@/pages/groupeur/PortefeuilleOag";
import TableauDeBord, { MesCampagnes } from "@/pages/groupeur/TableauDeBord";

/**
 * La boutique : acheteurs et OAG.
 *
 * L'administration est une application distincte (`admin.html`, port 5174) :
 * la frontière entre les deux est réelle, et non une affaire de route.
 */

function Pages() {
  const emplacement = useLocation();
  // La messagerie garde la **meme** cle d'un fil a l'autre : sans ca, cliquer
  // sur une conversation faisait disparaitre puis reapparaitre la page
  // entiere, colonne des fils comprise. Vrai des deux cotes : la boutique
  // et l'espace OAG servent le meme ecran.
  const messagerie = emplacement.pathname.match(
    /^(\/groupeur)?\/messages/,
  )?.[0];
  const cle = messagerie ?? emplacement.pathname;
  return (
    <AnimatePresence mode="wait">
      <motion.main
        key={cle}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.22, ease: "easeOut" }}
        // Marge basse pour la barre d'onglets, qui flotte au-dessus du contenu.
        className={
          emplacement.pathname.startsWith("/groupeur") ||
          emplacement.pathname.startsWith("/messages") ||
          emplacement.pathname === "/"
            ? ""
            : "pb-20 md:pb-0"
        }
      >
        <Routes location={emplacement}>
          <Route path="/" element={<Accueil />} />
          <Route path="/catalogue" element={<Catalogue />} />
          <Route path="/campagnes/:id" element={<FicheCampagne />} />
          <Route path="/communaute" element={<Communaute />} />
          <Route path="/mes-achats" element={<MesAchats />} />
          <Route path="/mes-achats/:id" element={<DetailAchat />} />
          {/* Une seule page pour les trois cas : la liste, un fil, et le
              fil qui n'existe pas encore. C'est la meme mise en page, et
              trois composants en auraient fait trois mises en page. */}
          <Route path="/messages" element={<Messages />} />
          <Route path="/messages/nouveau" element={<Messages />} />
          <Route path="/messages/:id" element={<Messages />} />
          {/* L'espace du livreur partenaire : il ne scanne pas depuis la
              boutique, et n'a rien a y faire d'autre. */}
          <Route path="/livraison" element={<Livraison />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/reclamations" element={<Reclamations />} />
          <Route path="/reclamations/nouvelle" element={<Reclamations />} />
          <Route path="/profil" element={<Profil />} />
          <Route path="/profil/devenir-groupeur" element={<DevenirGroupeur />} />
          <Route path="/connexion" element={<Connexion />} />
          <Route path="/inscription" element={<Inscription />} />

          <Route path="/groupeur" element={<EspaceGroupeur />}>
            <Route index element={<TableauDeBord />} />
            <Route path="campagnes" element={<MesCampagnes />} />
            <Route path="campagnes/nouvelle" element={<NouvelleCampagne />} />
            <Route path="campagnes/:id" element={<CampagneGroupeur />} />
            <Route path="portefeuille" element={<PortefeuilleOag />} />
            <Route path="historique-bancaire" element={<AttestationBancaire />} />
            {/* Le compte de l'OAG vit **dans** son espace : passer par
                /profil le renvoyait dans la boutique, onglets Accueil et
                Catalogue compris, alors qu'il venait de son outil. */}
            <Route path="profil" element={<CompteOag />} />
            {/* La messagerie **dans** l'espace de gestion : l'OAG repond a
                ses acheteurs sans sortir dans la boutique, et garde le bleu
                de son outil de travail. C'est le meme ecran, du cote OAG. */}
            <Route path="messages" element={<Messages espace="oag" />} />
            <Route path="messages/:id" element={<Messages espace="oag" />} />
          </Route>

          <Route
            path="*"
            element={
              <div className="px-4 py-24 text-center">
                <p className="text-5xl font-extrabold">404</p>
                <p className="texte-doux mt-2">Cette page n'existe pas.</p>
              </div>
            }
          />
        </Routes>
      </motion.main>
    </AnimatePresence>
  );
}

function Interface() {
  const emplacement = useLocation();
  const { profil, imposerTeinte } = useSession();
  const estEspaceGroupeur = emplacement.pathname.startsWith("/groupeur");
  // Le livreur est un partenaire, ni acheteur ni OAG : son ecran prend le
  // bleu des outils de travail, et ni les onglets ni le pied de la boutique.
  const estLivraison = emplacement.pathname.startsWith("/livraison");

  // Toujours thème clair sur l'ensemble de l'application
  useEffect(() => {
    document.documentElement.classList.remove("dark");
    document.documentElement.dataset.theme = "light";
    localStorage.setItem("ga-theme", "clair");
  }, []);

  // La couleur dit **où l'on est**, pas qui l'on est. Un OAG qui revient
  // acheter retrouve l'orange de la boutique ; le bleu est réservé à son
  // espace de travail. Sans ça, le catalogue changeait de couleur selon la
  // personne qui le regardait, et l'OAG ne se sentait plus client nulle part.
  useEffect(() => {
    if (estEspaceGroupeur || estLivraison) {
      imposerTeinte("groupeur");
    } else {
      imposerTeinte(profil === "visiteur" ? "visiteur" : "acheteur");
    }
  }, [estEspaceGroupeur, estLivraison, profil, imposerTeinte]);

  return (
    <div className="min-h-screen bg-slate-100/70 flex justify-center antialiased selection:bg-amber-500 selection:text-white">
      <div className="w-full max-w-md min-h-screen bg-[color:var(--fond,#fbfaf8)] shadow-md relative flex flex-col border-x border-slate-200/70">
        {estEspaceGroupeur || estLivraison ? (
          <EnTeteGroupeur livraison={estLivraison} />
        ) : (
          <EnTete />
        )}

        <div className="flex-1">
          <Pages />
        </div>

        {!estEspaceGroupeur && !estLivraison && <BarreOnglets />}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <FournisseurSession>
      <BrowserRouter>
        <RetourEnHaut />
        {/* Ramasse le `?p=…` d'un lien de parrainage avant toute autre
            chose : il doit survivre a la navigation, et disparaitre de
            l'adresse pour que l'invite ne reexpedie pas le lien d'un autre. */}
        <RamasseurDeParrainage />
        <Interface />
      </BrowserRouter>
    </FournisseurSession>
  );
}
