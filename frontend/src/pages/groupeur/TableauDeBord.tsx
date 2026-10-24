import { motion } from "framer-motion";
import {
  ArrowRight,
  Boxes,
  PackageCheck,
  Plus,
  Star,
  TrendingUp,
  Users,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";

import type { Campagne, Page, TableauDeBordGroupeur } from "@commun/api/types";
import { Anneau } from "@/composants/Jauge";
import { Jauge } from "@/composants/Jauge";
import { Bouton, Carte, Etiquette, EtatVide, Squelette } from "@commun/composants/ui";
import { Visuel } from "@/composants/Visuel";
import { useSession } from "@commun/contexte/Session";
import { francs, tempsRestant } from "@commun/outils/formats";
import { useRequete } from "@commun/outils/requetes";

const LIBELLES_STATUT: Record<string, { texte: string; ton: "neutre" | "accent" | "succes" | "alerte" }> = {
  brouillon: { texte: "Brouillon", ton: "neutre" },
  en_cours: { texte: "Collecte en cours", ton: "accent" },
  financee: { texte: "Financée", ton: "succes" },
  decaissee: { texte: "Fonds reçus", ton: "succes" },
  approvisionnement: { texte: "Approvisionnement", ton: "alerte" },
  distribution: { texte: "Distribution", ton: "alerte" },
  terminee: { texte: "Terminée", ton: "neutre" },
  annulee: { texte: "Annulée", ton: "neutre" },
};

/** Le tableau de bord du groupeur : l'état de son activité en un écran. */
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
    <div className="mx-auto w-full max-w-[86rem] space-y-6 px-4 py-6 lg:px-8 lg:py-9">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="texte-doux text-sm">Espace groupeur</p>
          <h1 className="text-2xl font-extrabold">
            Bonjour {utilisateur?.prenom}
          </h1>
        </div>
        <Link to="/groupeur/campagnes/nouvelle">
          <Bouton icone={<Plus className="size-4" />}>Nouvelle campagne</Bouton>
        </Link>
      </header>

      {chargement || !bord ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }, (_, rang) => (
            <Squelette key={rang} className="h-28" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Tuile
            icone={Wallet}
            libelle="Consigné en séquestre"
            valeur={francs(bord.collecte.montant_consigne)}
            detail={`${bord.collecte.pieces} pièces vendues`}
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
            detail={`${francs(bord.decaissements.frais_payes)} de frais`}
            index={2}
          />
          <Tuile
            icone={Star}
            libelle="Réputation"
            valeur={`${bord.reputation.note}/5`}
            detail={`${bord.reputation.campagnes_terminees} campagnes menées à terme`}
            index={3}
          />
        </div>
      )}

      {bord && bord.campagnes.a_distribuer > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Carte className="flex flex-wrap items-center gap-4 border-[color:var(--color-accent)]">
            <span className="grid size-12 place-items-center rounded-2xl bg-accent-doux text-[color:var(--color-accent)]">
              <PackageCheck className="size-6" />
            </span>
            <div className="flex-1">
              <p className="font-bold">
                {bord.campagnes.a_distribuer} campagne
                {bord.campagnes.a_distribuer > 1 ? "s" : ""} en distribution
              </p>
              <p className="texte-doux text-sm">
                Scannez les codes de retrait de vos participants.
              </p>
            </div>
          </Carte>
        </motion.div>
      )}

      <section className="space-y-3">
        <div className="flex items-end justify-between">
          <h2 className="text-lg font-bold">Campagnes à suivre</h2>
          <Link
            to="/groupeur/campagnes"
            className="flex items-center gap-1 text-sm font-semibold text-[color:var(--color-accent)]"
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
                <Bouton>Créer une campagne</Bouton>
              </Link>
            }
          />
        ) : (
          <ul className="space-y-3">
            {aSuivre.map((campagne, rang) => (
              <LigneCampagne key={campagne.id} campagne={campagne} index={rang} />
            ))}
          </ul>
        )}
      </section>
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
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07 }}
    >
      <Carte
        className={
          vedette
            ? "relative overflow-hidden border-transparent text-white"
            : undefined
        }
      >
        {vedette && <span className="degrade-accent absolute inset-0 -z-10" />}
        <Icone className={vedette ? "size-5" : "size-5 text-[color:var(--color-accent)]"} />
        <p
          className={
            vedette ? "mt-3 text-sm text-white/80" : "texte-doux mt-3 text-sm"
          }
        >
          {libelle}
        </p>
        <p className="tabulaire mt-0.5 text-xl font-extrabold">{valeur}</p>
        <p className={vedette ? "text-xs text-white/70" : "texte-doux text-xs"}>
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
              source={campagne.produit.images?.[0]?.image ?? null}
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
    <div className="mx-auto max-w-4xl space-y-5 px-4 py-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold">Mes campagnes</h1>
          <p className="texte-doux text-sm">
            {campagnes.length} au total
            {financees > 0 && ` · ${financees} prête(s) à décaisser`}
          </p>
        </div>
        <Link to="/groupeur/campagnes/nouvelle">
          <Bouton icone={<Plus className="size-4" />}>Nouvelle</Bouton>
        </Link>
      </header>

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
