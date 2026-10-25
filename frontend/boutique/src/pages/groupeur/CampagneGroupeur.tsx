import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  BadgeCheck,
  Banknote,
  Check,
  CircleCheck,
  Megaphone,
  PackageCheck,
  Phone,
  Rocket,
  Scale,
  ScanLine,
  Send,
  Users,
} from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import type { Campagne, Participant } from "@commun/api/types";
import { Feuille } from "@commun/composants/Feuille";
import { Jauge } from "@/composants/Jauge";
import {
  Alerte,
  Avatar,
  Bouton,
  Carte,
  Champ,
  Etiquette,
  EtatVide,
  fusionner,
  Squelette,
} from "@commun/composants/ui";
import { codeLisible, dateLongue, francs, telephoneLisible } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/**
 * Le pilotage d'une campagne par son groupeur.
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
  const [feuilleRetrait, setFeuilleRetrait] = useState(false);
  const [feuilleScan, setFeuilleScan] = useState(false);

  const tout = async () => {
    await Promise.all([recharger(), rechargerParticipants()]);
  };

  const publier = useAction(async () => {
    await api.post(`/groupeur/campagnes/${id}/publier/`);
    await tout();
  });
  const cloturer = useAction(async () => {
    await api.post(`/groupeur/campagnes/${id}/cloturer/`);
    await tout();
  });
  const maintenir = useAction(async () => {
    await api.post(`/api/groupeur/campagnes/${id}/maintenir/`);
    await tout();
  });
  const annuler = useAction(async (motif: string) => {
    await api.post(`/api/groupeur/campagnes/${id}/annuler/`, { motif });
    await tout();
  });
  const miseADisposition = useAction(async (point: string) => {
    await api.post(`/groupeur/campagnes/${id}/mise-a-disposition/`, {
      point_remise: point,
    });
    await tout();
  });

  if (chargement) {
    return (
      <div className="mx-auto w-full max-w-6xl space-y-5 px-4 py-6 lg:px-8 lg:py-9">
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
    <div className="mx-auto max-w-3xl space-y-5 px-4 py-6">
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
          <Mesure
            valeur={francs(campagne.montant_collecte)}
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
          <Etape
            icone={Rocket}
            titre="Publier la campagne"
            texte="Elle apparaîtra au catalogue et les acheteurs pourront participer."
            action={
              <Bouton chargement={publier.envoi} onClick={() => void publier.lancer(undefined as never)}>
                Publier
              </Bouton>
            }
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
            texte={`${francs(campagne.montant_collecte)} collectés. Vous recevez tout, moins 1 500 FCFA de frais fixes.`}
            action={<Bouton onClick={() => setFeuilleRetrait(true)}>Demander le retrait</Bouton>}
          />
        )}

        {["decaissee", "approvisionnement"].includes(campagne.statut) && (
          <Etape
            icone={Megaphone}
            titre="Annoncez l'arrivée de la marchandise"
            texte="Tous les participants recevront une notification avec le point de remise et leur code de retrait."
            action={
              <FormulaireDisposition
                defaut={campagne.point_remise}
                envoi={miseADisposition.envoi}
                surEnvoi={(point) => void miseADisposition.lancer(point)}
              />
            }
          />
        )}

        {campagne.statut === "distribution" && (
          <Etape
            icone={ScanLine}
            titre={`${retires} / ${payes.length} colis remis`}
            texte="Saisissez ou scannez le code que présente chaque participant."
            action={<Bouton onClick={() => setFeuilleScan(true)}>Valider un retrait</Bouton>}
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

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,22rem)] lg:items-start">
      {/* ── Suivi nominatif ──────────────────────────────────────────────── */}
      <section className="space-y-3 lg:order-1">
        <h2 className="flex items-center gap-2 text-lg font-bold">
          <Users className="size-5" />
          Qui a payé
          <span className="texte-doux text-sm font-normal">({payes.length})</span>
        </h2>

        {payes.length === 0 ? (
          <EtatVide
            icone={<Users className="size-7" />}
            titre="Aucun paiement pour l'instant"
            texte="Dès qu'un acheteur règle sa part, il apparaît ici — et vous recevez une notification."
          />
        ) : (
          <ul className="space-y-2">
            {payes.map((participant, rang) => (
              <motion.li
                key={participant.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: Math.min(rang, 8) * 0.04 }}
              >
                <Carte className="flex items-center gap-3 !p-3">
                  <Avatar nom={participant.nom_complet} taille={40} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold">{participant.nom_complet}</p>
                    <a
                      href={`tel:+228${participant.telephone}`}
                      className="texte-doux tabulaire flex items-center gap-1 text-xs"
                    >
                      <Phone className="size-3" />
                      {telephoneLisible(participant.telephone)}
                    </a>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="tabulaire font-bold">
                      {francs(participant.montant_total)}
                    </p>
                    <p className="texte-doux tabulaire text-xs">
                      {participant.quantite} pièce{participant.quantite > 1 ? "s" : ""}
                    </p>
                  </div>
                  {participant.statut === "retiree" ? (
                    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                      <Check className="size-4" strokeWidth={3} />
                    </span>
                  ) : (
                    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-accent-doux text-[color:var(--color-accent)]">
                      <BadgeCheck className="size-4" />
                    </span>
                  )}
                </Carte>
              </motion.li>
            ))}
          </ul>
        )}
      </section>

      {/* Les chiffres de l'offre, gardés sous les yeux pendant qu'on
          parcourt la liste des participants. */}
      <Carte className="space-y-2 text-sm lg:sticky lg:top-24">
        <h2 className="font-bold">Détails</h2>
        <Ligne libelle="Prix affiché" valeur={francs(campagne.prix_unitaire)} />
        <Ligne libelle="Prix courant" valeur={francs(campagne.prix_courant)} />
        <Ligne libelle="Minimum" valeur={`${campagne.quantite_minimale} pièces`} />
        <Ligne libelle="Date limite" valeur={dateLongue(campagne.date_limite)} />
        <Ligne libelle="Point de remise" valeur={campagne.point_remise} />
      </Carte>

      </div>

      <FeuilleRetrait
        ouverte={feuilleRetrait}
        surFermeture={() => setFeuilleRetrait(false)}
        campagne={campagne}
        surSucces={tout}
      />
      <FeuilleScan
        ouverte={feuilleScan}
        surFermeture={() => setFeuilleScan(false)}
        campagneId={campagne.id}
        surSucces={tout}
      />
    </div>
  );
}

function etiquetteStatut(statut: string): string {
  const table: Record<string, string> = {
    brouillon: "Brouillon",
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
    <div className="surface-douce rounded-2xl py-3">
      <p
        className={fusionner(
          "text-base font-extrabold",
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
  action: React.ReactNode;
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

function FormulaireDisposition({
  defaut,
  envoi,
  surEnvoi,
}: {
  defaut: string;
  envoi: boolean;
  surEnvoi: (point: string) => void;
}) {
  const [point, setPoint] = useState(defaut);
  return (
    <div className="flex w-full flex-col gap-2 sm:w-64">
      <input
        value={point}
        onChange={(evenement) => setPoint(evenement.target.value)}
        placeholder="Point de remise"
        className="surface h-11 rounded-2xl px-3 text-sm outline-none focus:border-[color:var(--color-accent)]"
        aria-label="Point de remise"
      />
      <Bouton
        chargement={envoi}
        icone={<Send className="size-4" />}
        onClick={() => surEnvoi(point)}
      >
        Prévenir les participants
      </Bouton>
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

  const frais = 1500;
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
            Les frais sont fixes : 1 500 FCFA par campagne, quel que soit le
            montant collecté. Aucun abonnement, aucune commission.
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

// ── Validation d'un retrait ────────────────────────────────────────────────

function FeuilleScan({
  ouverte,
  surFermeture,
  campagneId,
  surSucces,
}: {
  ouverte: boolean;
  surFermeture: () => void;
  campagneId: number;
  surSucces: () => Promise<void>;
}) {
  const [code, setCode] = useState("");
  const [valide, setValide] = useState<{ acheteur: string; quantite: number } | null>(
    null,
  );

  const valider = useAction(async () => {
    const retour = await api.post<{ acheteur: string; quantite: number }>(
      `/groupeur/campagnes/${campagneId}/retrait/`,
      { code: code.trim() },
    );
    setValide(retour);
    setCode("");
    await surSucces();
    return retour;
  });

  return (
    <Feuille
      ouverte={ouverte}
      surFermeture={() => {
        setValide(null);
        surFermeture();
      }}
      titre="Valider un retrait"
    >
      <div className="space-y-4 py-2">
        <AnimatePresence>
          {valide && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3 rounded-2xl bg-emerald-50 p-4 text-sm dark:bg-emerald-950/50"
            >
              <span className="grid size-10 shrink-0 place-items-center rounded-full bg-emerald-500 text-white">
                <Check className="size-5" strokeWidth={3} />
              </span>
              <div className="text-emerald-900 dark:text-emerald-200">
                <p className="font-bold">Colis remis à {valide.acheteur}</p>
                <p>
                  {valide.quantite} pièce{valide.quantite > 1 ? "s" : ""} —
                  livraison prouvée, réclamation sans fondement impossible.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <Champ
          etiquette="Code de retrait"
          placeholder="A9PE KDXQ"
          value={code}
          onChange={(evenement) => setCode(evenement.target.value.toUpperCase())}
          aide="Saisissez le code dicté par le participant, ou collez le contenu du QR scanné."
          className="tabulaire tracking-[0.18em]"
          autoFocus
        />

        <Alerte>{valider.erreur?.message}</Alerte>

        <Bouton
          pleineLargeur
          taille="lg"
          chargement={valider.envoi}
          disabled={code.trim().length < 4}
          onClick={() => void valider.lancer(undefined as never)}
          icone={<ScanLine className="size-4" />}
        >
          Valider le retrait
        </Bouton>

        <p className="texte-doux text-xs">
          Un code validé vaut preuve de livraison : il ferme définitivement
          toute contestation sur cette part. {codeLisible("")}
        </p>
      </div>
    </Feuille>
  );
}
