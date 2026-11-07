import { motion } from "framer-motion";
import {
  ArrowLeft,
  BadgeCheck,
  Banknote,
  Check,
  CircleCheck,
  Megaphone,
  PackageCheck,
  Rocket,
  Scale,
  Send,
  Hourglass,
  ShieldAlert,
  ShieldCheck,
  Truck,
  Users,
} from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import type { Campagne, Participant } from "@commun/api/types";
import { PhotosDuLot } from "@/composants/PhotosDuLot";
import { Feuille } from "@commun/composants/Feuille";
import { Jauge } from "@/composants/Jauge";
import { OffrePublication, useDroitDePublier } from "@/composants/DroitDePublier";
import {
  Alerte,
  Avatar,
  Bouton,
  Carte,
  Etiquette,
  EtatVide,
  fusionner,
  Squelette,
} from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import {
  commissionSur,
  dateLongue,
  francs,
  francsCourt,
  gradeLisible,
  tauxCommission,
  telephoneLisible,
} from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/**
 * Le pilotage d'une campagne par son OAG.
 *
 * C'est ici que se joue ce qui remplace la liste WhatsApp : **qui a payé
 * combien, en temps réel**, et les quelques gestes qui font avancer la
 * campagne — publier, clôturer, retirer les fonds, annoncer l'arrivée,
 * valider les codes.
 */
export default function CampagneGroupeur() {
  const { id } = useParams();
  const { donnees: campagne, chargement, recharger } = useRequete<Campagne>(
    `/groupeur/campagnes/${id}/`,
  );
  const { donnees: participants, recharger: rechargerParticipants } = useRequete<
    Participant[]
  >(`/groupeur/campagnes/${id}/participants/`);
  // Publier se paie : l'ecran doit savoir ce qu'il reste **avant** d'offrir
  // le bouton, et quoi proposer si la reserve est vide.
  const { donnees: droit, recharger: rechargerDroit } = useDroitDePublier();
  const [feuilleRetrait, setFeuilleRetrait] = useState(false);

  const tout = async () => {
    await Promise.all([recharger(), rechargerParticipants()]);
  };

  const publier = useAction(async () => {
    const retour = await api.post(`/groupeur/campagnes/${id}/publier/`);
    await tout();
    await rechargerDroit();
    return retour;
  });
  const cloturer = useAction(async () => {
    await api.post(`/groupeur/campagnes/${id}/cloturer/`);
    await tout();
  });
  // Sans le préfixe `/api` : le client le pose déjà. Avec, la requête
  // partait sur `/api/api/...` et les deux boutons de la décision — tenir le
  // groupage ou y renoncer — ne faisaient rien d'autre qu'un 404 silencieux.
  const maintenir = useAction(async () => {
    await api.post(`/groupeur/campagnes/${id}/maintenir/`);
    await tout();
  });
  const annuler = useAction(async (motif: string) => {
    await api.post(`/groupeur/campagnes/${id}/annuler/`, { motif });
    await tout();
  });
  const miseADisposition = useAction(async () => {
    await api.post(`/groupeur/campagnes/${id}/mise-a-disposition/`);
    await tout();
  });

  if (chargement) {
    return (
      <div className="w-full space-y-4 px-3.5 py-4 pb-24">
        <Squelette className="h-8 w-48" />
        <Squelette className="h-32" />
        <Squelette className="h-48" />
      </div>
    );
  }
  if (!campagne) {
    return <div className="px-4 py-20 text-center texte-doux">Campagne introuvable.</div>;
  }

  const payes = (participants ?? []).filter((p) => p.statut !== "en_attente_paiement");
  const retires = payes.filter((p) => p.statut === "retiree").length;
  const erreurAction =
    publier.erreur?.message ??
    cloturer.erreur?.message ??
    maintenir.erreur?.message ??
    annuler.erreur?.message ??
    miseADisposition.erreur?.message;

  return (
    <div className="w-full space-y-4 px-3.5 py-4 pb-24">
      <Link
        to="/groupeur/campagnes"
        className="texte-doux inline-flex items-center gap-1.5 text-sm font-semibold"
      >
        <ArrowLeft className="size-4" />
        Mes campagnes
      </Link>

      <header className="space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h1 className="text-2xl font-extrabold leading-tight">{campagne.titre}</h1>
          <Etiquette ton="accent">{etiquetteStatut(campagne.statut)}</Etiquette>
        </div>

        <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} />
        <div className="tabulaire grid grid-cols-3 gap-3 text-center">
          <Mesure
            valeur={`${campagne.quantite_reservee}/${campagne.quantite_minimale}`}
            libelle="pièces"
          />
          <Mesure valeur={String(campagne.nombre_participants)} libelle="participants" />
          {/* Forme courte : « 1,3 M » tient dans un tiers de 360 pixels, là
              où « 1 250 000 FCFA » se cassait sur trois lignes. Le montant
              exact reste juste dessous, dans les détails. */}
          <Mesure
            valeur={francsCourt(campagne.montant_collecte)}
            libelle="collecté"
            vedette
          />
        </div>
      </header>

      <Alerte>{erreurAction}</Alerte>

      {/* ── Les gestes du moment ─────────────────────────────────────────── */}
      <Carte className="space-y-3">
        <h2 className="font-bold">Prochaine étape</h2>

        {campagne.statut === "brouillon" && (
          <>
            <Etape
              icone={Rocket}
              titre="Publier la campagne"
              texte={
                droit?.abonnement_actif
                  ? "Votre abonnement couvre les publications sans compter."
                  : droit && droit.publications_restantes > 0
                    ? `Elle consommera une de vos ${droit.publications_restantes} publications.`
                    : "Elle apparaîtra au catalogue et les acheteurs pourront participer."
              }
              action={
                <Bouton
                  chargement={publier.envoi}
                  disabled={droit ? !droit.peut_publier : false}
                  onClick={() => void publier.lancer(undefined as never)}
                >
                  Publier
                </Bouton>
              }
            />

            {/* Le refus ne se contente pas de dire non : il montre les deux
                formules sur place. Renvoyer l'OAG chercher ailleurs au
                moment ou il voulait publier, c'est le perdre. */}
            {droit && !droit.peut_publier && (
              <div className="border-t pt-3">
                <p className="mb-3 text-sm font-semibold">
                  Publier demande un abonnement ou un pack
                </p>
                <OffrePublication droit={droit} surAchat={rechargerDroit} />
              </div>
            )}
          </>
        )}

        {/* La relecture avant vitrine depend du grade : systematique en
            Bronze, une sur quatre en Argent, jamais en Or. Le dire ici, et
            non seulement dans une notification, evite de croire a un bug. */}
        {campagne.statut === "en_verification" && (
          <Etape
            icone={Hourglass}
            titre="En vérification"
            texte="L'équipe relit votre groupage avant qu'il apparaisse au catalogue — en général sous 24 heures. Vous serez prévenu de la décision."
          />
        )}

        {campagne.statut === "brouillon" && campagne.motif_annulation && (
          <Etape
            icone={ShieldAlert}
            titre="Groupage à corriger"
            texte={`${campagne.motif_annulation} Votre publication vous a été rendue : corrigez, puis publiez à nouveau.`}
          />
        )}

        {campagne.statut === "en_cours" && (
          <Etape
            icone={Users}
            titre={
              campagne.minimum_atteint
                ? "Minimum atteint — vous pouvez clôturer"
                : "Collecte en cours"
            }
            texte={
              campagne.minimum_atteint
                ? "Clôturez pour figer la collecte et demander vos fonds."
                : `Encore ${campagne.quantite_minimale - campagne.quantite_reservee} pièces avant le minimum. Au-delà de la date limite, la campagne est annulée et tout le monde est remboursé.`
            }
            action={
              <Bouton
                ton={campagne.minimum_atteint ? "accent" : "contour"}
                chargement={cloturer.envoi}
                onClick={() => void cloturer.lancer(undefined as never)}
              >
                Clôturer la collecte
              </Bouton>
            }
          />
        )}

        {campagne.statut === "minimum_non_atteint" && (
          <Etape
            icone={Scale}
            titre="Le minimum n'a pas été atteint — à vous de décider"
            texte={`La collecte s'est close à ${campagne.quantite_reservee} pièces sur ${campagne.quantite_minimale}. L'argent des participants reste consigné : vous pouvez maintenir la commande malgré le nombre, ou y renoncer et les faire rembourser. Sans réponse, ils seront remboursés automatiquement.`}
            action={
              <div className="flex flex-col gap-2 sm:flex-row">
                <Bouton
                  chargement={maintenir.envoi}
                  onClick={() => void maintenir.lancer(undefined as never)}
                >
                  Je maintiens
                </Bouton>
                <Bouton
                  ton="contour"
                  chargement={annuler.envoi}
                  onClick={() => void annuler.lancer("")}
                >
                  Renoncer et rembourser
                </Bouton>
              </div>
            }
          />
        )}

        {campagne.statut === "financee" && (
          <Etape
            icone={Banknote}
            titre="Retirez vos fonds"
            texte={`${francs(campagne.montant_collecte)} collectés. Vous recevez tout, moins la commission de votre grade.`}
            action={<Bouton onClick={() => setFeuilleRetrait(true)}>Demander le retrait</Bouton>}
          />
        )}

        {["decaissee", "approvisionnement"].includes(campagne.statut) && (
          <Etape
            icone={Megaphone}
            titre="Annoncez l'arrivée de la marchandise"
            texte="Chaque participant recevra sa destination — son bureau de poste ou sa livraison — avec son code de retrait."
            action={
              <Bouton
                chargement={miseADisposition.envoi}
                icone={<Send className="size-4" />}
                onClick={() => void miseADisposition.lancer(undefined as never)}
              >
                Prévenir les participants
              </Bouton>
            }
          />
        )}

        {/* **Vous ne scannez pas.** Le lot est parti chez le partenaire —
            La Poste, Gozem — et c'est le livreur qui scanne le code de
            chaque acheteur. Vous l'apprenez ici, colis par colis. Si vous
            pouviez valider vous-même, celui qui doit livrer signerait sa
            propre livraison. */}
        {campagne.statut === "distribution" && (
          <Etape
            icone={Truck}
            titre={`${retires} / ${payes.length} colis remis`}
            texte="L'agence partenaire livre et scanne le code de chaque acheteur. Vous êtes prévenu à chaque remise."
          />
        )}

        {campagne.statut === "terminee" && (
          <Etape
            icone={CircleCheck}
            titre="Campagne terminée"
            texte="Tous les colis ont été remis. Cette campagne compte désormais dans votre réputation."
            action={null}
          />
        )}

        {campagne.statut === "annulee" && (
          <Etape
            icone={PackageCheck}
            titre="Campagne annulée"
            texte={campagne.motif_annulation || "Les participants ont été remboursés."}
            action={null}
          />
        )}
      </Carte>

      <div className="space-y-4">
      {/* ── Suivi nominatif ──────────────────────────────────────────────── */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-extrabold text-slate-900 dark:text-slate-100">
            <Users className="size-5 text-[color:var(--color-accent)]" />
            Liste des acheteurs ayant payé
            <span className="rounded-full bg-blue-100 dark:bg-blue-950 px-2 py-0.5 text-xs font-bold text-blue-700 dark:text-blue-300">
              {payes.length}
            </span>
          </h2>
          <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-400 px-2.5 py-0.5 rounded-full">
            {retires} / {payes.length} colis remis
          </span>
        </div>

        {payes.length === 0 ? (
          <EtatVide
            icone={<Users className="size-7" />}
            titre="Aucun paiement pour l'instant"
            texte="Dès qu'un acheteur règle sa part, il apparaît ici avec son nom et la quantité commandée."
          />
        ) : (
          <ul className="space-y-2">
            {payes.map((participant, rang) => {
              const nomAcheteur = participant.nom_complet || participant.nom_utilisateur || "Acheteur";
              return (
                <motion.li
                  key={participant.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: Math.min(rang, 8) * 0.04 }}
                >
                  <Carte className="flex items-center gap-3.5 !p-3.5 border-slate-200/80 hover:border-[color:var(--color-accent)] transition-colors">
                    <Avatar nom={nomAcheteur} taille={42} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="truncate font-bold text-sm text-slate-900 dark:text-slate-100">
                          {nomAcheteur}
                        </p>
                        <span className="shrink-0 rounded-full bg-amber-100 dark:bg-amber-950/80 border border-amber-300 dark:border-amber-700/60 px-2 py-0.5 text-[11px] font-extrabold text-amber-900 dark:text-amber-200">
                          {participant.quantite} {participant.quantite > 1 ? "pièces demandées" : "pièce demandée"}
                        </span>
                      </div>
                      <p className="texte-doux flex items-center gap-1.5 text-xs mt-0.5">
                        {participant.mode_retrait === "livraison" ? (
                          <Truck className="size-3.5 text-blue-500 shrink-0" />
                        ) : (
                          <ShieldCheck className="size-3.5 text-emerald-500 shrink-0" />
                        )}
                        <span className="truncate">
                          {participant.remis_par
                            ? `Remis par ${participant.remis_par}`
                            : participant.destination}
                        </span>
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="tabulaire font-extrabold text-sm text-slate-900 dark:text-slate-100">
                        {francs(participant.montant_total)}
                      </p>
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">
                        Payé · Séquestre
                      </span>
                    </div>
                    {participant.statut === "retiree" ? (
                      <span className="grid size-8 shrink-0 place-items-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300" title="Colis retiré">
                        <Check className="size-4" strokeWidth={3} />
                      </span>
                    ) : (
                      <span className="grid size-8 shrink-0 place-items-center rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" title="En attente de retrait">
                        <BadgeCheck className="size-4" />
                      </span>
                    )}
                  </Carte>
                </motion.li>
              );
            })}
          </ul>
        )}
      </section>

      {/* Les photos du lot et les chiffres de l'offre */}
      <div className="space-y-4">
      <PhotosDuLot campagneId={campagne.id} />

      <Carte className="space-y-2 text-sm">
        <h2 className="font-bold">Détails</h2>
        <Ligne libelle="Prix unitaire" valeur={francs(campagne.prix_unitaire)} />
        <Ligne libelle="Minimum" valeur={`${campagne.quantite_minimale} pièces`} />
        <Ligne libelle="Date limite" valeur={dateLongue(campagne.date_limite)} />
        <Ligne libelle="Retrait" valeur="Au choix de chaque acheteur" />
      </Carte>
      </div>

      </div>

      <FeuilleRetrait
        ouverte={feuilleRetrait}
        surFermeture={() => setFeuilleRetrait(false)}
        campagne={campagne}
        surSucces={tout}
      />
    </div>
  );
}

function etiquetteStatut(statut: string): string {
  const table: Record<string, string> = {
    brouillon: "Brouillon",
    en_verification: "En vérification",
    minimum_non_atteint: "Minimum non atteint",
    en_cours: "Collecte en cours",
    financee: "Financée",
    decaissee: "Fonds reçus",
    approvisionnement: "Approvisionnement",
    distribution: "Distribution",
    terminee: "Terminée",
    annulee: "Annulée",
  };
  return table[statut] ?? statut;
}

function Mesure({
  valeur,
  libelle,
  vedette,
}: {
  valeur: string;
  libelle: string;
  vedette?: boolean;
}) {
  return (
    <div className="surface-douce rounded-2xl px-1 py-3">
      <p
        className={fusionner(
          "text-sm font-extrabold sm:text-base",
          vedette && "text-[color:var(--color-accent)]",
        )}
      >
        {valeur}
      </p>
      <p className="texte-doux text-xs">{libelle}</p>
    </div>
  );
}

function Ligne({ libelle, valeur }: { libelle: string; valeur: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b pb-2 last:border-0 last:pb-0">
      <span className="texte-doux">{libelle}</span>
      <span className="text-right font-medium">{valeur}</span>
    </div>
  );
}

function Etape({
  icone: Icone,
  titre,
  texte,
  action,
}: {
  icone: typeof Rocket;
  titre: string;
  texte: string;
  /** Toutes les etapes n'appellent pas un geste : certaines ne font
   *  qu'expliquer l'attente. */
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-accent-doux text-[color:var(--color-accent)]">
        <Icone className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{titre}</p>
        <p className="texte-doux text-sm leading-relaxed">{texte}</p>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

// ── Demande de décaissement ────────────────────────────────────────────────

function FeuilleRetrait({
  ouverte,
  surFermeture,
  campagne,
  surSucces,
}: {
  ouverte: boolean;
  surFermeture: () => void;
  campagne: Campagne;
  surSucces: () => Promise<void>;
}) {
  const { utilisateur } = useSession();
  const [resultat, setResultat] = useState<{
    montant_brut: number;
    frais: number;
    montant_net: number;
    numero_mobile_money: string;
  } | null>(null);

  const demande = useAction(async () => {
    const retour = await api.post<typeof resultat & object>(
      `/groupeur/campagnes/${campagne.id}/demander-retrait/`,
    );
    setResultat(retour);
    await surSucces();
    return retour;
  });

  // Le taux suit le grade : 3,5 % en Bronze, 2,5 % en Argent, 1,3 % en Or.
  // On refait ici le calcul du serveur — même arrondi vers le bas — pour que
  // l'OAG voie le net avant de confirmer, et non après.
  const centiemes = utilisateur?.points.commission_centiemes ?? 350;
  const frais = commissionSur(campagne.montant_collecte, centiemes);
  const net = Math.max(0, campagne.montant_collecte - frais);

  return (
    <Feuille
      ouverte={ouverte}
      surFermeture={() => {
        setResultat(null);
        surFermeture();
      }}
      titre={resultat ? "Demande enregistrée" : "Retirer mes fonds"}
    >
      {resultat ? (
        <div className="space-y-4 py-2 text-center">
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 16 }}
            className="mx-auto grid size-16 place-items-center rounded-full bg-emerald-500 text-white"
          >
            <Check className="size-8" strokeWidth={3} />
          </motion.span>
          <p className="text-lg font-bold">
            {francs(resultat.montant_net)} en route
          </p>
          <p className="texte-doux text-sm">
            Vers le {telephoneLisible(resultat.numero_mobile_money)}. L'équipe
            libère les fonds du séquestre — vous serez notifié dès le versement.
          </p>
        </div>
      ) : (
        <div className="space-y-4 py-2">
          <div className="surface-douce space-y-2 rounded-2xl p-4 text-sm">
            <div className="flex justify-between">
              <span className="texte-doux">Collecté</span>
              <span className="tabulaire font-semibold">
                {francs(campagne.montant_collecte)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="texte-doux">Frais de plateforme</span>
              <span className="tabulaire font-semibold">− {francs(frais)}</span>
            </div>
            <div className="flex justify-between border-t pt-2 text-base">
              <span className="font-bold">Vous recevez</span>
              <span className="tabulaire font-extrabold text-[color:var(--color-accent)]">
                {francs(net)}
              </span>
            </div>
          </div>

          <p className="texte-doux text-sm">
            La commission est de {tauxCommission(centiemes)} du montant
            collecté, au grade {gradeLisible(utilisateur?.points.grade ?? "bronze")}.
            Elle baisse à mesure que vous montez en grade.
          </p>

          <Alerte>{demande.erreur?.message}</Alerte>

          <Bouton
            pleineLargeur
            taille="lg"
            chargement={demande.envoi}
            onClick={() => void demande.lancer(undefined as never)}
          >
            Demander le versement
          </Bouton>
        </div>
      )}
    </Feuille>
  );
}

