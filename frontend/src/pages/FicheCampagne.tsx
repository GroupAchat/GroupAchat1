import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  BadgeCheck,
  Check,
  Clock,
  MapPin,
  Minus,
  Plus,
  ShieldCheck,
  Star,
  TrendingDown,
  Users,
} from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import type { Campagne, Participation } from "@commun/api/types";
import { Discussion } from "@/composants/Discussion";
import { Feuille } from "@commun/composants/Feuille";
import { Jauge } from "@/composants/Jauge";
import { Alerte, Avatar, Bouton, Carte, Etiquette, fusionner, Squelette } from "@commun/composants/ui";
import { Visuel } from "@/composants/Visuel";
import { useSession } from "@commun/contexte/Session";
import { dateLongue, francs, tempsRestant } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/** La fiche d'une campagne : tout ce qu'il faut pour décider, puis payer. */
export default function FicheCampagne() {
  const { id } = useParams();
  const naviguer = useNavigate();
  const { peutAgir, utilisateur } = useSession();
  const { donnees: campagne, chargement, recharger } = useRequete<Campagne>(
    `/catalogue/campagnes/${id}/`,
  );
  const [quantite, setQuantite] = useState(1);
  const [feuilleOuverte, setFeuilleOuverte] = useState(false);

  if (chargement) return <SqueletteFiche />;
  if (!campagne) {
    return (
      <div className="mx-auto max-w-lg px-4 py-20 text-center">
        <p className="texte-doux">Cette campagne est introuvable.</p>
        <Link to="/catalogue" className="mt-4 inline-block">
          <Bouton ton="contour">Retour au catalogue</Bouton>
        </Link>
      </div>
    );
  }

  const estLeGroupeur = utilisateur?.id === campagne.groupeur.id;
  const ouverte = campagne.collecte_ouverte;
  const prixUnitaire = campagne.prix_courant;
  const remise =
    prixUnitaire < campagne.prix_unitaire
      ? Math.round(((campagne.prix_unitaire - prixUnitaire) / campagne.prix_unitaire) * 100)
      : 0;
  const prochainPalier = campagne.paliers.find(
    (palier) => palier.quantite_min > campagne.quantite_reservee,
  );

  return (
    <div className="pb-28 md:pb-10">
      {/* ── Visuel ─────────────────────────────────────────────────────────── */}
      <div className="relative aspect-[4/3] w-full overflow-hidden md:aspect-[21/9]">
        <Visuel
          source={campagne.produit.images[0]?.image ?? null}
          nom={campagne.produit.nom}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/25" />
        <button
          onClick={() => naviguer(-1)}
          className="verre-sombre absolute left-4 top-4 grid size-10 place-items-center rounded-full text-white"
          aria-label="Retour"
        >
          <ArrowLeft className="size-5" />
        </button>
        <div className="absolute bottom-4 left-4 right-4 flex flex-wrap gap-1.5">
          <Etiquette ton="sombre">{campagne.produit.categorie_nom}</Etiquette>
          {ouverte ? (
            <Etiquette ton="sombre">
              <Clock className="size-3" />
              {tempsRestant(campagne.jours_restants)}
            </Etiquette>
          ) : (
            <Etiquette ton="sombre">Collecte close</Etiquette>
          )}
          {campagne.minimum_atteint && (
            <span className="rounded-full bg-emerald-500 px-2.5 py-1 text-xs font-bold text-white">
              Objectif atteint
            </span>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-3xl space-y-6 px-4 py-6">
        <motion.header
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          <h1 className="text-2xl font-extrabold leading-tight">{campagne.titre}</h1>

          <div className="flex items-end gap-2.5">
            <span className="tabulaire text-3xl font-extrabold text-[color:var(--color-accent)]">
              {francs(prixUnitaire)}
            </span>
            {remise > 0 && (
              <>
                <span className="texte-doux tabulaire text-sm line-through">
                  {francs(campagne.prix_unitaire)}
                </span>
                <Etiquette ton="accent">−{remise} %</Etiquette>
              </>
            )}
          </div>

          <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} />
          <div className="tabulaire flex items-center justify-between text-sm">
            <span className="font-semibold">
              {campagne.quantite_reservee} / {campagne.quantite_minimale} pièces
            </span>
            <span className="texte-doux flex items-center gap-1">
              <Users className="size-4" />
              {campagne.nombre_participants} participants
            </span>
          </div>
        </motion.header>

        {/* ── Paliers ────────────────────────────────────────────────────── */}
        {campagne.paliers.length > 0 && (
          <Carte className="space-y-3">
            <h2 className="flex items-center gap-2 font-bold">
              <TrendingDown className="size-4 text-[color:var(--color-accent)]" />
              Plus on est nombreux, moins c'est cher
            </h2>
            <ul className="space-y-2">
              {campagne.paliers.map((palier) => {
                const franchi = campagne.quantite_reservee >= palier.quantite_min;
                return (
                  <li
                    key={palier.id}
                    className={fusionner(
                      "flex items-center justify-between rounded-xl px-3 py-2.5 text-sm transition-colors",
                      franchi ? "bg-accent-doux" : "surface-douce",
                    )}
                  >
                    <span className="flex items-center gap-2">
                      {franchi && (
                        <Check className="size-4 text-[color:var(--color-accent)]" />
                      )}
                      À partir de {palier.quantite_min} pièces
                    </span>
                    <span className="tabulaire font-bold">
                      {francs(palier.prix_unitaire)}
                    </span>
                  </li>
                );
              })}
            </ul>
            {prochainPalier && (
              <p className="texte-doux text-sm">
                Encore{" "}
                <strong className="text-[color:var(--color-accent)]">
                  {prochainPalier.quantite_min - campagne.quantite_reservee} pièces
                </strong>{" "}
                et le prix tombe à {francs(prochainPalier.prix_unitaire)} pour tous.
              </p>
            )}
          </Carte>
        )}

        {/* ── Groupeur ───────────────────────────────────────────────────── */}
        <Carte className="flex items-center gap-3">
          <Avatar
            nom={campagne.groupeur.nom_commerce || campagne.groupeur.nom_complet}
            taille={48}
          />
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-1.5 font-bold">
              <span className="truncate">
                {campagne.groupeur.nom_commerce || campagne.groupeur.nom_complet}
              </span>
              {campagne.groupeur.badge_confiance && (
                <BadgeCheck className="size-4 shrink-0 text-[color:var(--color-accent)]" />
              )}
            </p>
            <p className="texte-doux flex flex-wrap items-center gap-x-3 text-sm">
              {campagne.groupeur.reputation &&
                Number(campagne.groupeur.reputation.note) > 0 && (
                  <span className="flex items-center gap-1">
                    <Star className="size-3.5 fill-amber-400 text-amber-400" />
                    {campagne.groupeur.reputation.note}/5
                  </span>
                )}
              <span>
                {campagne.groupeur.reputation?.campagnes_terminees ?? 0} campagne
                {(campagne.groupeur.reputation?.campagnes_terminees ?? 0) > 1 ? "s" : ""} menée
                {(campagne.groupeur.reputation?.campagnes_terminees ?? 0) > 1 ? "s" : ""} à terme
              </span>
            </p>
          </div>
        </Carte>

        {/* ── Garantie ───────────────────────────────────────────────────── */}
        <div className="flex gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/40">
          <ShieldCheck className="size-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <p className="text-sm text-emerald-900 dark:text-emerald-200">
            <strong>Livré ou remboursé.</strong> Votre part reste consignée : elle
            n'est versée au groupeur qu'une fois la campagne financée, et vous
            récupérez tout si le minimum n'est pas atteint.
          </p>
        </div>

        {/* ── Détails ────────────────────────────────────────────────────── */}
        {(campagne.description || campagne.produit.description) && (
          <section className="space-y-2">
            <h2 className="font-bold">Le produit</h2>
            <p className="texte-doux whitespace-pre-wrap text-[0.95rem] leading-relaxed">
              {campagne.produit.description}
            </p>
            {campagne.description && (
              <p className="whitespace-pre-wrap text-[0.95rem] leading-relaxed">
                {campagne.description}
              </p>
            )}
          </section>
        )}

        {Object.keys(campagne.caracteristiques_offre).length > 0 && (
          <Carte className="space-y-2">
            <h2 className="font-bold">Caractéristiques</h2>
            <dl className="divide-y text-sm">
              {Object.entries(campagne.caracteristiques_offre).map(([cle, valeur]) => (
                <div key={cle} className="flex justify-between gap-4 py-2">
                  <dt className="texte-doux">{cle}</dt>
                  <dd className="text-right font-medium">{valeur}</dd>
                </div>
              ))}
            </dl>
          </Carte>
        )}

        <Carte className="space-y-2 text-sm">
          <h2 className="font-bold">Retrait</h2>
          <p className="flex items-center gap-2">
            <MapPin className="size-4 shrink-0 text-[color:var(--color-accent)]" />
            {campagne.point_remise}
          </p>
          <p className="texte-doux flex items-center gap-2">
            <Clock className="size-4 shrink-0" />
            Collecte jusqu'au {dateLongue(campagne.date_limite)}
          </p>
        </Carte>

        <Discussion campagneId={campagne.id} />
      </div>

      {/* ── Barre d'action, collée en bas sur téléphone ──────────────────── */}
      {ouverte && !estLeGroupeur && (
        <div
          className="verre fixed inset-x-0 bottom-0 z-30 border-t p-3 md:hidden"
          style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
        >
          <div className="flex items-center gap-3">
            <div className="shrink-0">
              <p className="texte-doux text-xs">Ma part</p>
              <p className="tabulaire font-extrabold">
                {francs(prixUnitaire * quantite)}
              </p>
            </div>
            <Bouton
              taille="lg"
              className="flex-1"
              onClick={() => setFeuilleOuverte(true)}
            >
              Participer
            </Bouton>
          </div>
        </div>
      )}

      {ouverte && !estLeGroupeur && (
        <div className="mx-auto hidden max-w-3xl px-4 md:block">
          <Bouton taille="lg" pleineLargeur onClick={() => setFeuilleOuverte(true)}>
            Participer — {francs(prixUnitaire * quantite)}
          </Bouton>
        </div>
      )}

      {estLeGroupeur && (
        <div className="mx-auto max-w-3xl px-4">
          <Link to={`/groupeur/campagnes/${campagne.id}`}>
            <Bouton ton="contour" pleineLargeur>
              Gérer ma campagne
            </Bouton>
          </Link>
        </div>
      )}

      <FeuilleParticipation
        ouverte={feuilleOuverte}
        surFermeture={() => setFeuilleOuverte(false)}
        campagne={campagne}
        quantite={quantite}
        surQuantite={setQuantite}
        peutAgir={peutAgir}
        surSucces={async () => {
          setFeuilleOuverte(false);
          await recharger();
        }}
      />
    </div>
  );
}

// ── La feuille de participation et de paiement ─────────────────────────────

function FeuilleParticipation({
  ouverte,
  surFermeture,
  campagne,
  quantite,
  surQuantite,
  peutAgir,
  surSucces,
}: {
  ouverte: boolean;
  surFermeture: () => void;
  campagne: Campagne;
  quantite: number;
  surQuantite: (valeur: number) => void;
  peutAgir: boolean;
  surSucces: () => Promise<void>;
}) {
  const naviguer = useNavigate();
  const [operateur, setOperateur] = useState<"tmoney" | "flooz">("tmoney");
  const [reussite, setReussite] = useState<Participation | null>(null);

  const maximum = campagne.quantite_maximale
    ? Math.max(1, campagne.quantite_maximale - campagne.quantite_reservee)
    : 20;
  const prix = campagne.prix_courant;

  const payer = useAction(async () => {
    const participation = await api.post<Participation>("/participations/", {
      campagne: campagne.id,
      quantite,
    });
    const retour = await api.post<{ participation: Participation }>(
      `/participations/${participation.id}/payer/`,
      { operateur },
    );
    setReussite(retour.participation);
    await surSucces();
    return retour.participation;
  });

  return (
    <Feuille
      ouverte={ouverte}
      surFermeture={() => {
        setReussite(null);
        surFermeture();
      }}
      titre={reussite ? "Paiement confirmé" : "Participer à la campagne"}
    >
      <AnimatePresence mode="wait">
        {reussite ? (
          <motion.div
            key="reussite"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-4 py-2 text-center"
          >
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 16 }}
              className="mx-auto grid size-16 place-items-center rounded-full bg-emerald-500 text-white"
            >
              <Check className="size-8" strokeWidth={3} />
            </motion.span>
            <div>
              <p className="text-lg font-bold">Votre part est consignée</p>
              <p className="texte-doux mt-1 text-sm">
                {francs(reussite.montant_total)} bloqués jusqu'à la livraison.
                Votre code de retrait vous attend.
              </p>
            </div>
            <div className="surface-douce rounded-2xl p-4">
              <p className="texte-doux text-xs">Code de retrait</p>
              <p className="tabulaire mt-1 text-2xl font-extrabold tracking-[0.2em]">
                {reussite.code_retrait}
              </p>
            </div>
            <Bouton
              pleineLargeur
              taille="lg"
              onClick={() => naviguer(`/mes-achats/${reussite.id}`)}
            >
              Voir mon QR code
            </Bouton>
          </motion.div>
        ) : !peutAgir ? (
          <motion.div key="connexion" className="space-y-4 py-2">
            <p className="texte-doux text-sm">
              Pour participer, créez votre compte et vérifiez votre numéro. Cela
              prend moins d'une minute.
            </p>
            <Link to="/inscription">
              <Bouton pleineLargeur taille="lg">
                Créer mon compte
              </Bouton>
            </Link>
            <Link to="/connexion">
              <Bouton ton="contour" pleineLargeur>
                J'ai déjà un compte
              </Bouton>
            </Link>
          </motion.div>
        ) : (
          <motion.div key="paiement" className="space-y-5 py-2">
            <div>
              <p className="mb-2 text-sm font-medium">Quantité</p>
              <div className="flex items-center justify-between gap-4">
                <div className="surface flex items-center gap-1 rounded-full p-1">
                  <button
                    onClick={() => surQuantite(Math.max(1, quantite - 1))}
                    disabled={quantite <= 1}
                    className="grid size-10 place-items-center rounded-full transition-colors hover:surface-douce disabled:opacity-40"
                    aria-label="Moins"
                  >
                    <Minus className="size-4" />
                  </button>
                  <span className="tabulaire w-10 text-center text-lg font-bold">
                    {quantite}
                  </span>
                  <button
                    onClick={() => surQuantite(Math.min(maximum, quantite + 1))}
                    disabled={quantite >= maximum}
                    className="grid size-10 place-items-center rounded-full transition-colors hover:surface-douce disabled:opacity-40"
                    aria-label="Plus"
                  >
                    <Plus className="size-4" />
                  </button>
                </div>
                <div className="text-right">
                  <p className="texte-doux text-xs">Total</p>
                  <p className="tabulaire text-xl font-extrabold">
                    {francs(prix * quantite)}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <p className="mb-2 text-sm font-medium">Payer avec</p>
              <div className="grid grid-cols-2 gap-3">
                {(
                  [
                    { cle: "tmoney", nom: "T-Money", teinte: "#ffd400" },
                    { cle: "flooz", nom: "Flooz", teinte: "#00a0e3" },
                  ] as const
                ).map((moyen) => (
                  <button
                    key={moyen.cle}
                    onClick={() => setOperateur(moyen.cle)}
                    className={fusionner(
                      "flex items-center gap-3 rounded-2xl border p-3 text-left transition-all",
                      operateur === moyen.cle
                        ? "border-[color:var(--color-accent)] bg-accent-doux"
                        : "surface",
                    )}
                  >
                    <span
                      className="size-9 shrink-0 rounded-xl"
                      style={{ background: moyen.teinte }}
                    />
                    <span className="text-sm font-semibold">{moyen.nom}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Honnêteté de la démonstration : on ne laisse pas croire qu'un
                vrai paiement part. */}
            <p className="surface-douce rounded-xl px-3 py-2 text-xs texte-doux">
              Démonstration : aucun paiement réel n'est effectué. La part est
              consignée dans le séquestre de la plateforme.
            </p>

            <Alerte>{payer.erreur?.message}</Alerte>

            <Bouton
              pleineLargeur
              taille="lg"
              chargement={payer.envoi}
              onClick={() => void payer.lancer(undefined as never)}
            >
              Payer {francs(prix * quantite)}
            </Bouton>
          </motion.div>
        )}
      </AnimatePresence>
    </Feuille>
  );
}

function SqueletteFiche() {
  return (
    <div>
      <Squelette className="aspect-[4/3] rounded-none md:aspect-[21/9]" />
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-6">
        <Squelette className="h-7 w-3/4" />
        <Squelette className="h-9 w-40" />
        <Squelette className="h-3 w-full rounded-full" />
        <Squelette className="h-28" />
        <Squelette className="h-20" />
      </div>
    </div>
  );
}
