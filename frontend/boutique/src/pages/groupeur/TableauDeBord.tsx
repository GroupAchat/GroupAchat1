import { motion } from "framer-motion";
import {
  ArrowRight,
  Boxes,
  FileText,
  Landmark,
  PackageCheck,
  Plus,
  Star,
  TrendingUp,
  Users,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";

import type { Campagne, Page, TableauDeBordGroupeur } from "@commun/api/types";
import { AvisRecus } from "@/composants/Avis";
import { Anneau } from "@/composants/Jauge";
import { Jauge } from "@/composants/Jauge";
import { Bouton, Carte, Etiquette, EtatVide, Squelette } from "@commun/composants/ui";

import { BandeauGrade } from "../../composants/BandeauGrade";
import { CarteDroitDePublier } from "@/composants/DroitDePublier";
import { Visuel } from "@/composants/Visuel";
import { useSession } from "@commun/contexte/Session";
import { francs, tempsRestant } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

const LIBELLES_STATUT: Record<string, { texte: string; ton: "neutre" | "accent" | "succes" | "alerte" }> = {
  brouillon: { texte: "Brouillon", ton: "neutre" },
  en_verification: { texte: "En vérification", ton: "alerte" },
  en_cours: { texte: "Collecte en cours", ton: "accent" },
  financee: { texte: "Financée", ton: "succes" },
  decaissee: { texte: "Fonds reçus", ton: "succes" },
  approvisionnement: { texte: "Approvisionnement", ton: "alerte" },
  distribution: { texte: "Distribution", ton: "alerte" },
  terminee: { texte: "Terminée", ton: "neutre" },
  annulee: { texte: "Annulée", ton: "neutre" },
};

/** Le tableau de bord de l'OAG : l'état de son activité en un écran. */
export default function TableauDeBord() {
  const { utilisateur } = useSession();
  const { donnees: bord, chargement } = useRequete<TableauDeBordGroupeur>(
    "/groupeur/tableau-de-bord/",
  );
  const { donnees: campagnes } = useRequete<Page<Campagne>>("/groupeur/campagnes/");

  const liste = campagnes?.results ?? [];
  const aSuivre = liste.filter((campagne) =>
    ["en_cours", "financee", "approvisionnement", "distribution"].includes(campagne.statut),
  );

  return (
    <div className="w-full space-y-4 px-3.5 py-4 pb-24">
      <header className="flex items-center justify-between gap-2">
        <div>
          <p className="texte-doux text-xs">Espace OAG</p>
          <h1 className="text-xl font-extrabold text-slate-900">
            Bonjour {utilisateur?.prenom}
          </h1>
        </div>
        <Link to="/groupeur/campagnes/nouvelle">
          <Bouton taille="sm" icone={<Plus className="size-3.5" />}>
            Nouvelle offre
          </Bouton>
        </Link>
      </header>

      {/* Attestation d'historique bancaire certifiée (Prêts bancaires BCEAO / Togo) */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Carte className="space-y-3 border-indigo-200/80 bg-gradient-to-r from-indigo-50/70 to-blue-50/50 p-3.5">
          <div className="flex items-start gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-indigo-600 text-white shadow-xs">
              <Landmark className="size-5" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-slate-900 leading-tight">
                Attestation d'historique bancaire certifiée
              </p>
              <p className="texte-doux text-xs mt-0.5 leading-snug">
                Générez votre rapport officiel certifié pour vos dossiers de crédit (Ecobank, Coris, Orabank Togo).
              </p>
            </div>
          </div>
          <Link to="/groupeur/historique-bancaire" className="block">
            <Bouton pleineLargeur ton="contour" taille="sm" icone={<FileText className="size-3.5" />}>
              Générer l'attestation
            </Bouton>
          </Link>
        </Carte>
      </motion.div>

      {/* Ce qui attend un geste avant les chiffres */}
      {bord && bord.campagnes.a_distribuer > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Carte className="flex items-center gap-3 border-[color:var(--color-accent)] p-3.5">
            <span className="bg-accent-doux grid size-11 place-items-center rounded-xl text-[color:var(--color-accent)] shrink-0">
              <PackageCheck className="size-5" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-bold text-sm text-slate-900">
                {bord.campagnes.a_distribuer} campagne
                {bord.campagnes.a_distribuer > 1 ? "s" : ""} en distribution
              </p>
              <p className="texte-doux text-xs mt-0.5">
                Scannez les codes de retrait de vos participants.
              </p>
            </div>
            <Link to="/groupeur/campagnes" className="shrink-0">
              <Bouton taille="sm" ton="contour">Voir</Bouton>
            </Link>
          </Carte>
        </motion.div>
      )}

      {chargement || !bord ? (
        <div className="grid grid-cols-2 gap-2.5">
          {Array.from({ length: 4 }, (_, rang) => (
            <Squelette key={rang} className="h-24 rounded-2xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-2.5">
          <Tuile
            icone={Wallet}
            libelle="Consigné séquestre"
            valeur={francs(bord.collecte.montant_consigne)}
            detail={`${bord.collecte.pieces} pcs vendues`}
            index={0}
            vedette
          />
          <Tuile
            icone={Users}
            libelle="Participants"
            valeur={String(bord.collecte.participants)}
            detail={`${bord.reputation.participants_servis} déjà servis`}
            index={1}
          />
          <Tuile
            icone={TrendingUp}
            libelle="Déjà retiré"
            valeur={francs(bord.decaissements.montant_recu)}
            detail={`${francs(bord.decaissements.frais_payes)} com.`}
            index={2}
          />
          <Tuile
            icone={Star}
            libelle="Réputation"
            valeur={`${bord.reputation.note}/5`}
            detail={`${bord.reputation.campagnes_terminees} réussies`}
            index={3}
          />
        </div>
      )}

      <div className="space-y-4">
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">Campagnes à suivre</h2>
            <Link
              to="/groupeur/campagnes"
              className="flex items-center gap-1 text-xs font-semibold text-[color:var(--color-accent)]"
            >
              Toutes ({liste.length})
              <ArrowRight className="size-3.5" />
            </Link>
          </div>

          {aSuivre.length === 0 ? (
            <EtatVide
              icone={<Boxes className="size-7" />}
              titre="Aucune campagne active"
              texte="Lancez votre premier groupage : photos, prix, minimum de pièces, date limite."
              action={
                <Link to="/groupeur/campagnes/nouvelle">
                  <Bouton taille="sm">Créer une offre</Bouton>
                </Link>
              }
            />
          ) : (
            <ul className="space-y-2.5">
              {aSuivre.map((campagne, rang) => (
                <LigneCampagne key={campagne.id} campagne={campagne} index={rang} />
              ))}
            </ul>
          )}
        </section>

        <div className="space-y-3">
          <BandeauGrade />
          <CarteDroitDePublier compact />
        </div>

        {utilisateur && <AvisRecus groupeurId={utilisateur.id} />}
      </div>
    </div>
  );
}

function Tuile({
  icone: Icone,
  libelle,
  valeur,
  detail,
  index,
  vedette,
}: {
  icone: typeof Wallet;
  libelle: string;
  valeur: string;
  detail: string;
  index: number;
  vedette?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Carte
        className={
          vedette
            ? "degrade-accent relative overflow-hidden border-transparent text-white !p-3 space-y-1 shadow-xs"
            : "surface !p-3 space-y-1 border border-slate-200/80 shadow-xs"
        }
      >
        <div className="flex items-center justify-between">
          <Icone className={vedette ? "size-4 text-white" : "size-4 text-orange-600"} />
        </div>
        <p
          className={
            vedette ? "text-[11px] font-medium text-white/80 leading-tight truncate" : "texte-doux text-[11px] font-medium leading-tight truncate"
          }
        >
          {libelle}
        </p>
        <p className="tabulaire text-base font-black leading-tight truncate">{valeur}</p>
        <p className={vedette ? "text-[10px] text-white/70 truncate" : "texte-doux text-[10px] truncate"}>
          {detail}
        </p>
      </Carte>
    </motion.div>
  );
}

export function LigneCampagne({
  campagne,
  index,
}: {
  campagne: Campagne;
  index: number;
}) {
  const statut = LIBELLES_STATUT[campagne.statut] ?? LIBELLES_STATUT.brouillon;
  return (
    <motion.li
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index, 6) * 0.05 }}
    >
      <Link to={`/groupeur/campagnes/${campagne.id}`}>
        <Carte survol className="flex gap-4">
          <div className="size-20 shrink-0 overflow-hidden rounded-2xl">
            <Visuel
              source={campagne.produit.medias?.[0]?.vignette ?? null}
              nom={campagne.produit.nom}
            />
          </div>
          <div className="min-w-0 flex-1 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <h3 className="line-clamp-1 font-bold">{campagne.titre}</h3>
              <Etiquette ton={statut.ton}>{statut.texte}</Etiquette>
            </div>
            <Jauge
              pourcentage={campagne.pourcentage}
              atteint={campagne.minimum_atteint}
              compact
            />
            <div className="tabulaire flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
              <span>
                <strong>{campagne.quantite_reservee}</strong> / {campagne.quantite_minimale}{" "}
                pièces
              </span>
              <span className="texte-doux">
                {campagne.nombre_participants} participants
              </span>
              <span className="font-semibold text-[color:var(--color-accent)]">
                {francs(campagne.montant_collecte ?? 0)}
              </span>
              {campagne.statut === "en_cours" && (
                <span className="texte-doux ml-auto">
                  {tempsRestant(campagne.jours_restants)}
                </span>
              )}
            </div>
          </div>
        </Carte>
      </Link>
    </motion.li>
  );
}

/** La liste complète, pour l'onglet « Toutes ». */
export function MesCampagnes() {
  const { donnees, chargement } = useRequete<Page<Campagne>>("/groupeur/campagnes/");
  const campagnes = donnees?.results ?? [];

  const financees = campagnes.filter((c) => c.statut === "financee").length;

  return (
    <div className="w-full space-y-4 px-3.5 py-4 pb-24">
      <header className="flex items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-extrabold text-slate-900">Mes offres</h1>
          <p className="texte-doux text-xs">
            {campagnes.length} groupage(s)
            {financees > 0 && ` · ${financees} prêt(s) à décaisser`}
          </p>
        </div>
        <Link to="/groupeur/campagnes/nouvelle">
          <Bouton taille="sm" icone={<Plus className="size-3.5" />}>Nouvelle</Bouton>
        </Link>
      </header>

      {/* Attestation d'historique bancaire certifiée (Prêts bancaires BCEAO / Togo) */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Carte className="space-y-3 border-indigo-200/80 bg-gradient-to-r from-indigo-50/70 to-blue-50/50 p-3.5">
          <div className="flex items-start gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-indigo-600 text-white shadow-xs">
              <Landmark className="size-5" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-slate-900 leading-tight">
                Attestation d'historique bancaire certifiée
              </p>
              <p className="texte-doux text-xs mt-0.5 leading-snug">
                Générez votre rapport officiel certifié pour vos dossiers de crédit (Ecobank, Coris, Orabank Togo).
              </p>
            </div>
          </div>
          <Link to="/groupeur/historique-bancaire" className="block">
            <Bouton pleineLargeur ton="contour" taille="sm" icone={<FileText className="size-3.5" />}>
              Générer l'attestation
            </Bouton>
          </Link>
        </Carte>
      </motion.div>

      {chargement ? (
        <div className="space-y-3">
          <Squelette className="h-28" />
          <Squelette className="h-28" />
        </div>
      ) : campagnes.length === 0 ? (
        <EtatVide
          icone={<Boxes className="size-7" />}
          titre="Aucune campagne"
          texte="Créez votre premier groupage en moins de deux minutes."
          action={
            <Link to="/groupeur/campagnes/nouvelle">
              <Bouton>Créer une campagne</Bouton>
            </Link>
          }
        />
      ) : (
        <ul className="space-y-3">
          {campagnes.map((campagne, rang) => (
            <LigneCampagne key={campagne.id} campagne={campagne} index={rang} />
          ))}
        </ul>
      )}
    </div>
  );
}

export { Anneau };
