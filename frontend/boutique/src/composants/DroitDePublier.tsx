import { motion } from "framer-motion";
import {
  CalendarCheck,
  ChevronRight,
  Infinity as Illimite,
  Layers,
  Sparkles,
} from "lucide-react";

import type { DroitDePublier } from "@commun/api/types";
import { Alerte, Bouton, Carte, fusionner } from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { dateLongue, francs, pluriel } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";
import { Link } from "react-router-dom";

/**
 * Le droit de publier, tel que le voit l'OAG.
 *
 * **Publier se paie, et il choisit comment.** L'abonnement s'adresse à celui
 * qui publie régulièrement ; le pack à celui qui essaie, ou qui lance un
 * groupage de loin en loin. Les deux compteurs sont indépendants : un
 * abonnement qui s'achève ne prend pas les publications déjà payées.
 *
 * Ce qui se dit ici et ne doit pas se taire : la publication se consomme
 * **à la mise en ligne**, et elle n'est pas rendue si le groupage échoue.
 * Une règle de facturation découverte après coup se lit comme une mauvaise
 * surprise, même quand elle est juste.
 */

export function useDroitDePublier() {
  return useRequete<DroitDePublier>("/groupeur/publication/");
}

export function CarteDroitDePublier({ compact }: { compact?: boolean } = {}) {
  const { donnees: droit, recharger } = useDroitDePublier();
  if (!droit) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Carte className="space-y-4">
        <div className="flex flex-wrap items-start gap-4">
          <span
            className={fusionner(
              "grid size-12 shrink-0 place-items-center rounded-2xl text-white",
              droit.peut_publier
                ? "bg-[color:var(--color-marine-800)]"
                : "bg-amber-600",
            )}
          >
            {droit.abonnement_actif ? (
              <Illimite className="size-6" />
            ) : (
              <Layers className="size-6" />
            )}
          </span>

          <div className="min-w-0 flex-1">
            <p className="texte-doux text-sm">Droit de publier</p>
            <p className="text-xl font-extrabold">
              {droit.abonnement_actif
                ? "Publications illimitées"
                : droit.publications_restantes > 0
                  ? `${droit.publications_restantes} ${pluriel(
                      droit.publications_restantes,
                      "publication",
                    )} en réserve`
                  : "Aucune publication disponible"}
            </p>
            {droit.abonnement_actif && droit.expire_le ? (
              <p className="texte-doux flex items-center gap-1.5 text-sm">
                <CalendarCheck className="size-3.5" />
                Jusqu'au {dateLongue(droit.expire_le).split(" à ")[0]}
                {droit.publications_restantes > 0 &&
                  ` · ${droit.publications_restantes} en réserve pour après`}
              </p>
            ) : (
              <p className="texte-doux text-sm">
                Une publication se consomme à la mise en ligne, jamais au
                brouillon.
              </p>
            )}
          </div>
        </div>

        {/* **L'argumentaire n'a rien à faire sur le tableau de bord.** Ce
            qu'on y cherche chaque matin, c'est l'état : puis-je publier,
            jusqu'à quand. Les deux formules et leurs boutons d'achat vivent
            sur la page du compte, et reviennent d'eux-mêmes au moment où
            l'on publie sans en avoir. */}
        {compact ? (
          <Link
            to="/groupeur/profil"
            className={fusionner(
              "flex items-center justify-between gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition-colors",
              droit.peut_publier
                ? "surface-douce hover:brightness-97"
                : "degrade-accent text-white",
            )}
          >
            {droit.peut_publier ? "Gérer mon droit de publier" : "En prendre"}
            <ChevronRight className="size-4" />
          </Link>
        ) : (
          <OffrePublication droit={droit} surAchat={recharger} />
        )}
      </Carte>
    </motion.div>
  );
}

/** Les deux formules de publication, empilées pour un confort 100% mobile. */
export function OffrePublication({
  droit,
  surAchat,
}: {
  droit: DroitDePublier;
  surAchat: () => void;
}) {
  const { rafraichir } = useSession();

  const abonnement = useActionAchat(
    "/groupeur/publication/abonnement/", surAchat, rafraichir,
  );
  const pack = useActionAchat("/groupeur/publication/pack/", surAchat, rafraichir);

  return (
    <div className="space-y-3.5">
      <div className="flex flex-col gap-3">
        <Formule
          titre="Abonnement illimité"
          badge="Recommandé"
          prix={droit.prix_abonnement}
          unite={`par mois · ${droit.duree_jours} jours`}
          detail="Publications d'offres en illimité"
          points={10}
          vedette
          action={
            <Bouton
              pleineLargeur
              chargement={abonnement.envoi}
              onClick={() => void abonnement.lancer(undefined as never)}
              className="font-bold bg-orange-600 hover:bg-orange-700 text-white"
            >
              {droit.abonnement_actif ? "Prolonger d'un mois (2 000 F)" : "M'abonner — 2 000 FCFA"}
            </Bouton>
          }
        />
        <Formule
          titre="Ticket de publication"
          badge="À l'unité"
          prix={droit.prix_pack}
          unite="pack de 10 publications"
          detail={`${droit.publications_par_pack} créations d'offres sans limite de temps`}
          points={2}
          pointsUneFois
          action={
            <Bouton
              ton="contour"
              pleineLargeur
              chargement={pack.envoi}
              onClick={() => void pack.lancer(undefined as never)}
              className="font-bold border-slate-300 hover:bg-slate-50 text-slate-800"
            >
              Prendre un ticket ({francs(droit.prix_pack)})
            </Bouton>
          }
        />
      </div>

      {droit.abonnement_actif && (
        <p className="texte-doux text-xs">
          Prolonger avant l'échéance <strong>ajoute</strong> trente jours à
          ceux qui restent.
        </p>
      )}
      <p className="texte-doux text-xs">
        Une publication consommée n'est pas rendue si le groupage échoue :
        elle paie la mise en ligne, pas la réussite.
      </p>
      <Alerte>{abonnement.erreur?.message ?? pack.erreur?.message}</Alerte>
      <p className="texte-doux text-xs">
        Paiement simulé dans cette version.
      </p>
    </div>
  );
}

function useActionAchat(
  chemin: string,
  surAchat: () => void,
  rafraichir: () => Promise<unknown>,
) {
  return useAction(async () => {
    const retour = await api.post<DroitDePublier>(chemin);
    surAchat();
    // Les points viennent de changer : le grade et la commission suivent.
    await rafraichir();
    return retour;
  });
}

function Formule({
  titre,
  badge,
  prix,
  unite,
  detail,
  points,
  pointsUneFois,
  vedette,
  action,
}: {
  titre: string;
  badge?: string;
  prix: number;
  unite: string;
  detail: string;
  points: number;
  pointsUneFois?: boolean;
  vedette?: boolean;
  action: React.ReactNode;
}) {
  return (
    <div
      className={fusionner(
        "rounded-2xl border p-3.5 space-y-3 transition-colors",
        vedette
          ? "border-orange-200/90 bg-orange-50/30 shadow-xs"
          : "surface border-slate-200/80 shadow-xs",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-extrabold text-sm text-slate-900">{titre}</span>
            {badge && (
              <span
                className={fusionner(
                  "rounded-full px-2 py-0.5 text-[10px] font-bold",
                  vedette
                    ? "bg-orange-100 text-orange-800"
                    : "bg-slate-100 text-slate-700",
                )}
              >
                {badge}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-600 mt-1">{detail}</p>
          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-orange-700 bg-orange-100/70 px-2 py-0.5 rounded-full mt-1.5">
            <Sparkles className="size-3 text-orange-600" />
            +{points} points fidélité
            {pointsUneFois && " (à l'achat)"}
          </span>
        </div>

        <div className="shrink-0 text-right">
          <span className="tabulaire text-base font-black text-slate-900 block leading-tight">
            {francs(prix)}
          </span>
          <span className="texte-doux block text-[10px] mt-0.5">{unite}</span>
        </div>
      </div>

      <div className="pt-0.5">{action}</div>
    </div>
  );
}
