import { FileCheck, MapPin, QrCode, ShieldCheck } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { Marque } from "@commun/composants/Marque";
import { useSession } from "@commun/contexte/Session";

/**
 * Le pied de page de la boutique - GROUP ACHAT (Togo).
 * Conçu pour affichage mobile fluide.
 */

const GARANTIES = [
  {
    icone: ShieldCheck,
    titre: "Assurance Tout Risques",
    texte: "Police unique couvrant l'opération de la collecte à la remise.",
  },
  {
    icone: QrCode,
    titre: "QR Code & OTP SMS",
    texte: "Double preuve sécurisée pour valider chaque retrait de colis.",
  },
  {
    icone: FileCheck,
    titre: "OAG Certifiés Notaire",
    texte: "Contrat notarié et charte de déontologie au Togo.",
  },
];

export function PiedDePage() {
  const { connecte, utilisateur } = useSession();
  const { pathname } = useLocation();

  const ecransNus = ["/connexion", "/inscription"];
  if (ecransNus.includes(pathname)) return null;

  const annee = new Date().getFullYear();

  return (
    <footer className="mt-8 bg-[color:var(--color-marine-950)] pb-[calc(var(--hauteur-onglets)+2rem)] text-white/75 text-xs">
      <div className="mx-auto w-full px-4 py-8 space-y-6">
        {/* La marque et ce qu'elle promet */}
        <div className="space-y-3">
          <Marque variante="blanc" taille="moyenne" />
          <p className="text-xs leading-relaxed text-white/80">
            GROUP ACHAT — Plateforme sécurisée d'achats groupés au Togo.
            Fonds consignés jusqu'à remise certifiée du colis.
          </p>
          <p className="flex items-center gap-1.5 text-xs text-white/60">
            <MapPin className="size-3.5" />
            Lomé, Togo · IPDCP (Loi n°2019-014)
          </p>
        </div>

        {/* Liens utiles en grille 2 colonnes compacte */}
        <div className="grid grid-cols-2 gap-4 border-t border-white/10 pt-5">
          <Colonne titre="Acheter">
            <Lien vers="/catalogue">Catalogue</Lien>
            <Lien vers="/communaute">Demandes groupage</Lien>
            <Lien vers="/reclamations">Réclamations (REC-2026)</Lien>
            {connecte && <Lien vers="/mes-achats">Mes achats & QR</Lien>}
          </Colonne>

          <Colonne titre="Espace OAG">
            {utilisateur?.est_groupeur_valide ? (
              <>
                <Lien vers="/groupeur">Tableau de bord</Lien>
                <Lien vers="/groupeur/campagnes/nouvelle">Créer une offre</Lien>
                <Lien vers="/groupeur/historique-bancaire">Attestation bancaire</Lien>
              </>
            ) : (
              <Lien vers="/profil/devenir-groupeur">Devenir OAG certifié</Lien>
            )}
            <Lien vers="/profil">Mon compte</Lien>
          </Colonne>
        </div>

        {/* Les 3 garanties du nouveau cahier des charges */}
        <div className="space-y-3 border-t border-white/10 pt-5">
          {GARANTIES.map((garantie) => (
            <div key={garantie.titre} className="flex gap-2.5 items-start">
              <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-white/10 text-white mt-0.5">
                <garantie.icone className="size-3.5" />
              </span>
              <div>
                <p className="font-semibold text-white text-xs">{garantie.titre}</p>
                <p className="text-[11px] text-white/70 leading-tight">{garantie.texte}</p>
              </div>
            </div>
          ))}
        </div>

        <p className="border-t border-white/10 pt-4 text-center text-[11px] text-white/50">
          © {annee} Group Achat · Lomé, Togo.
        </p>
      </div>
    </footer>
  );
}

function Colonne({ titre, children }: { titre: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-white/50">
        {titre}
      </p>
      <ul className="space-y-1.5">{children}</ul>
    </div>
  );
}

function Lien({ vers, children }: { vers: string; children: React.ReactNode }) {
  return (
    <li>
      <Link
        to={vers}
        className="text-xs transition-colors hover:text-white hover:underline text-white/80"
      >
        {children}
      </Link>
    </li>
  );
}
