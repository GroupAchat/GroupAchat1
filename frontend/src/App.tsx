import { AnimatePresence, motion } from "framer-motion";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";

import { BarreOnglets, EnTete, RetourEnHaut } from "@/composants/Coque";
import { FournisseurSession } from "@commun/contexte/Session";
import Accueil from "@/pages/Accueil";
import { Connexion, Inscription } from "@/pages/Authentification";
import Catalogue from "@/pages/Catalogue";
import Communaute from "@/pages/Communaute";
import FicheCampagne from "@/pages/FicheCampagne";
import MesAchats, { DetailAchat } from "@/pages/MesAchats";
import Notifications from "@/pages/Notifications";
import Profil, { DevenirGroupeur } from "@/pages/Profil";
import CampagneGroupeur from "@/pages/groupeur/CampagneGroupeur";
import EspaceGroupeur from "@/pages/groupeur/EspaceGroupeur";
import NouvelleCampagne from "@/pages/groupeur/NouvelleCampagne";
import TableauDeBord, { MesCampagnes } from "@/pages/groupeur/TableauDeBord";

/**
 * La boutique : acheteurs et groupeurs.
 *
 * L'administration est une application distincte (`admin.html`, port 5174) :
 * la frontière entre les deux est réelle, et non une affaire de route.
 */

function Pages() {
  const emplacement = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.main
        key={emplacement.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.22, ease: "easeOut" }}
        // Marge basse pour la barre d'onglets, qui flotte au-dessus du contenu.
        className="pb-20 md:pb-0"
      >
        <Routes location={emplacement}>
          <Route path="/" element={<Accueil />} />
          <Route path="/catalogue" element={<Catalogue />} />
          <Route path="/campagnes/:id" element={<FicheCampagne />} />
          <Route path="/communaute" element={<Communaute />} />
          <Route path="/mes-achats" element={<MesAchats />} />
          <Route path="/mes-achats/:id" element={<DetailAchat />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/profil" element={<Profil />} />
          <Route path="/profil/devenir-groupeur" element={<DevenirGroupeur />} />
          <Route path="/connexion" element={<Connexion />} />
          <Route path="/inscription" element={<Inscription />} />

          <Route path="/groupeur" element={<EspaceGroupeur />}>
            <Route index element={<TableauDeBord />} />
            <Route path="campagnes" element={<MesCampagnes />} />
            <Route path="campagnes/nouvelle" element={<NouvelleCampagne />} />
            <Route path="campagnes/:id" element={<CampagneGroupeur />} />
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

export default function App() {
  return (
    <FournisseurSession>
      <BrowserRouter>
        <RetourEnHaut />
        <EnTete />
        <Pages />
        <BarreOnglets />
      </BrowserRouter>
    </FournisseurSession>
  );
}
