import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  BadgeCheck,
  Check,
  CheckCircle2,
  Clock,
  Copy,
  Hourglass,
  Landmark,
  Lock,
  Minus,
  Play,
  Plus,
  Radio,
  ShieldCheck,
  Smartphone,
  Star,
  Truck,
  Undo2,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import type {
  Campagne,
  EtatContactPrive,
  ModeRetrait,
  Participation,
} from "@commun/api/types";
import { ListeAvis } from "@/composants/Avis";
import { Bareme, prixPour } from "@/composants/Bareme";
import { BoutonPartager, codeParrainRecu } from "@/composants/Parrainage";
import { ContactPriveSurCampagne } from "@/composants/ContactPrive";
import { Feuille } from "@commun/composants/Feuille";
import { Jauge } from "@/composants/Jauge";
import {
  Alerte,
  Avatar,
  Bouton,
  Champ,
  fusionner,
  Squelette,
} from "@commun/composants/ui";
import { Visuel } from "@/composants/Visuel";
import { useSession } from "@commun/contexte/Session";
import {
  codeLisible,
  francs,
  gradeLisible,
  telephoneLisible,
  tempsRestant,
} from "@commun/outils/formats";
import { api, useRequete } from "@commun/outils/requetes";

/** Un élément de la galerie, photo ou vidéo. */
interface ElementGalerie {
  cle: string;
  genre: "image" | "video";
  url: string;
  vignette: string | null;
  legende: string;
}

/**
 * La fiche d'une campagne.
 *
 * **Deux mises en page, un seul code.** Sur téléphone, tout s'empile sous
 * une grande photo. Sur ordinateur, la disposition des places de marché :
 * la galerie à gauche, le panneau d'achat **collé en haut** à droite, et
 * les détails en dessous. L'acheteur garde le prix et le bouton sous les
 * yeux pendant qu'il lit les caractéristiques — c'est tout l'intérêt.
 */
export default function FicheCampagne() {
  const { id } = useParams();
  const naviguer = useNavigate();
  const { peutAgir, utilisateur } = useSession();
  const { donnees: campagne, chargement, recharger } = useRequete<Campagne>(
    `/catalogue/campagnes/${id}/`,
  );
  const { donnees: etatContact } = useRequete<EtatContactPrive>(
    utilisateur ? "/contact-prive/" : null,
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
  // Le prix suit **la quantité que l'acheteur a sous les yeux**, pas le
  // volume déjà collecté : c'est lui qui décide de monter dans la tranche
  // basse, et il doit voir le prix changer pendant qu'il appuie sur « + ».
  const prixUnitaire = prixPour(campagne, quantite, campagne.nombre_participants);
  const remise =
    prixUnitaire < campagne.prix_unitaire
      ? Math.round(((campagne.prix_unitaire - prixUnitaire) / campagne.prix_unitaire) * 100)
      : 0;
  const maximum = campagne.quantite_maximale
    ? Math.max(1, campagne.quantite_maximale - campagne.quantite_reservee)
    : 20;

  // Les médias du produit — jusqu'à trois photos et deux vidéos — puis les
  // photos du lot réellement proposé par cet OAG.
  // Un média sans adresse — fichier perdu, envoi interrompu — ne va pas dans
  // la galerie : il y ferait une vignette cassée et une flèche qui ne mène
  // nulle part. Mieux vaut qu'il n'existe pas à l'écran.
  const visuels: ElementGalerie[] = [
    ...campagne.produit.medias.map((media) => ({
      cle: `p${media.id}`,
      genre: media.genre,
      url: media.adresse,
      vignette: media.vignette,
      legende: media.legende,
    })),
    ...campagne.medias.map((media) => ({
      cle: `m${media.id}`,
      genre: "image" as const,
      url: media.adresse,
      vignette: media.vignette,
      legende: media.legende,
    })),
  ].filter((visuel): visuel is ElementGalerie => Boolean(visuel.url));

  return (
    <div className="pb-36">
      {/* ── En-tête mobile avec bouton retour ───────────────────────────────── */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200/80 bg-white/95 px-3 py-2.5 backdrop-blur-md">
        <button
          onClick={() => naviguer(-1)}
          className="surface-douce grid size-9 place-items-center rounded-full transition-transform active:scale-90"
          aria-label="Retour"
        >
          <ArrowLeft className="size-4" />
        </button>
        <span className="text-xs font-bold text-slate-700 truncate max-w-[200px]">
          {campagne.produit.categorie_nom}
        </span>
        <BoutonPartager
          chemin={`/campagnes/${campagne.id}`}
          titre={campagne.titre}
        />
      </div>

      <div className="space-y-4 px-4 pt-3">
        {/* ── Galerie de visuels (Photo ou Vidéo avec vignettes sous le média) ─ */}
        <GalerieMobile
          visuels={visuels}
          nom={campagne.produit.nom}
          ouverte={ouverte}
          joursRestants={campagne.jours_restants}
          atteint={campagne.minimum_atteint}
        />

        {/* ── Alerte statut particulier ────────────────────────────────────── */}
        {campagne.statut === "minimum_non_atteint" && (
          <div className="flex gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-3.5 text-xs text-amber-900">
            <Hourglass className="size-4 shrink-0 text-amber-600 mt-0.5" />
            <p>
              <strong>Groupage non abouti.</strong> Clôturé à {campagne.quantite_reservee}/{campagne.quantite_minimale} pièces. L'OAG examine actuellement le maintien ou le remboursement.
            </p>
          </div>
        )}

        {campagne.statut === "annulee" && (
          <div className="flex gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-3.5 text-xs text-rose-900">
            <Undo2 className="size-4 shrink-0 text-rose-600 mt-0.5" />
            <p>
              <strong>Groupage annulé.</strong> {campagne.motif_annulation || "Les participants ont été intégralement remboursés."}
            </p>
          </div>
        )}

        {/* ── Titre & Marque ──────────────────────────────────────────────── */}
        <div className="space-y-1">
          <h1 className="text-lg font-extrabold leading-snug text-slate-900">
            {campagne.titre}
          </h1>
          {campagne.produit.marque && (
            <p className="texte-doux text-xs">
              Marque : <strong className="text-slate-800 font-bold">{campagne.produit.marque}</strong>
            </p>
          )}
        </div>

        {/* ── Fiche OAG Organisateur ───────────────────────────────────────── */}
        <div className="surface flex items-center gap-3 rounded-2xl border border-slate-200/80 p-3">
          <Avatar nom={campagne.groupeur.nom_utilisateur} taille={42} />
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-1 font-bold text-xs text-slate-900">
              <span className="truncate">{campagne.groupeur.nom_utilisateur}</span>
              {campagne.groupeur.badge_confiance && (
                <BadgeCheck className="size-3.5 shrink-0 text-[color:var(--color-accent)]" />
              )}
            </p>
            <p className="texte-doux flex items-center gap-2 text-[11px] mt-0.5">
              <span className="font-semibold text-amber-800">{gradeLisible(campagne.groupeur.grade)}</span>
              {campagne.groupeur.reputation && Number(campagne.groupeur.reputation.note) > 0 && (
                <span className="flex items-center gap-0.5 text-amber-600 font-bold">
                  ★ {campagne.groupeur.reputation.note}/5
                </span>
              )}
              <span>· {campagne.groupeur.reputation?.campagnes_terminees ?? 0} réussies</span>
            </p>
          </div>
        </div>

        {/* ── Bloc Tarif & Quantité ────────────────────────────────────────── */}
        <div className="surface-douce space-y-3.5 rounded-2xl border border-slate-200/90 p-4">
          <div className="flex items-baseline justify-between">
            <div className="flex items-baseline gap-2">
              <span className="tabulaire text-2xl font-black text-[color:var(--color-accent)]">
                {francs(prixUnitaire)}
              </span>
              <span className="text-xs text-slate-500 font-medium">la pièce</span>
            </div>
            {remise > 0 && (
              <div className="flex items-center gap-1.5">
                <span className="texte-doux tabulaire text-xs line-through">
                  {francs(campagne.prix_unitaire)}
                </span>
                <span className="rounded-full bg-rose-600 px-2 py-0.5 text-[10px] font-extrabold text-white">
                  −{remise} %
                </span>
              </div>
            )}
          </div>

          {/* Stepper de quantité */}
          {ouverte && !estLeGroupeur && (
            <div className="flex items-center justify-between border-t border-slate-200/60 pt-3">
              <div>
                <p className="text-[11px] font-bold text-slate-600">Quantité souhaitée</p>
                <p className="tabulaire text-xs font-extrabold text-slate-900">
                  Total : {francs(prixUnitaire * quantite)}
                </p>
              </div>
              <div className="surface flex items-center gap-1 rounded-full border border-slate-200/90 p-1 shadow-2xs">
                <button
                  onClick={() => setQuantite(Math.max(1, quantite - 1))}
                  disabled={quantite <= 1}
                  className="grid size-8 place-items-center rounded-full transition-colors hover:surface-douce disabled:opacity-30"
                  aria-label="Moins"
                >
                  <Minus className="size-3.5" />
                </button>
                <span className="tabulaire w-8 text-center text-xs font-black">{quantite}</span>
                <button
                  onClick={() => setQuantite(Math.min(maximum, quantite + 1))}
                  disabled={quantite >= maximum}
                  className="grid size-8 place-items-center rounded-full transition-colors hover:surface-douce disabled:opacity-30"
                  aria-label="Plus"
                >
                  <Plus className="size-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* Le barème de prix dégressif */}
          <Bareme campagne={campagne} quantite={quantite} />
        </div>

        {/* ── Jauge d'avancement ──────────────────────────────────────────── */}
        <div className="surface space-y-2 rounded-2xl border border-slate-200/80 p-3.5">
          <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} />
          <div className="tabulaire flex items-center justify-between text-xs font-medium text-slate-700">
            <span>
              <strong>{campagne.quantite_reservee}</strong> / {campagne.quantite_minimale} pièces
            </span>
            <span className="flex items-center gap-1 text-[color:var(--color-accent-fort)] font-bold">
              <Users className="size-3.5" />
              {campagne.nombre_participants} participants
            </span>
          </div>
        </div>

        {/* ── Contact privé avec l'OAG ────────────────────────────────────── */}
        <ContactPriveSurCampagne
          groupeur={campagne.groupeur}
          campagneId={campagne.id}
          etat={etatContact}
        />

        {/* ── Garanties & Mode de retrait Togo ────────────────────────────── */}
        <div className="grid gap-2.5">
          <div className="flex gap-2.5 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-3 text-xs text-emerald-900">
            <ShieldCheck className="size-4 shrink-0 text-emerald-600 mt-0.5" />
            <div>
              <p className="font-bold">Assurance Tout Risques Togo</p>
              <p className="text-[11px] text-emerald-800 leading-relaxed mt-0.5">
                Fonds consignés en banque jusqu'à remise certifiée par QR code et SMS OTP.
              </p>
            </div>
          </div>
          <div className="surface flex gap-2.5 rounded-2xl border border-slate-200/80 p-3 text-xs text-slate-800">
            <Truck className="size-4 shrink-0 text-blue-600 mt-0.5" />
            <div>
              <p className="font-bold">Retrait flexible à Lomé</p>
              <p className="texte-doux text-[11px] leading-relaxed mt-0.5">
                Retrait au bureau de poste de votre quartier ou livraison Gozem à domicile.
              </p>
            </div>
          </div>
        </div>

        {/* ── Caractéristiques & Description ──────────────────────────────── */}
        {(campagne.description || campagne.produit.description) && (
          <section className="surface space-y-2 rounded-2xl border border-slate-200/80 p-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Description du produit
            </h2>
            {campagne.produit.description && (
              <p className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed">
                {campagne.produit.description}
              </p>
            )}
            {campagne.description && (
              <p className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed border-t border-slate-100 pt-2">
                {campagne.description}
              </p>
            )}
          </section>
        )}

        {Object.keys(campagne.caracteristiques_offre).length > 0 && (
          <section className="surface space-y-2 rounded-2xl border border-slate-200/80 p-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Caractéristiques techniques
            </h2>
            <dl className="divide-y divide-slate-100 text-xs">
              {Object.entries(campagne.caracteristiques_offre).map(([cle, valeur]) => (
                <div key={cle} className="flex justify-between py-1.5">
                  <dt className="text-slate-500">{cle}</dt>
                  <dd className="font-semibold text-slate-900 text-right">{valeur}</dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        {/* ── Avis sur l'OAG ──────────────────────────────────────────────── */}
        <section id="avis" className="space-y-2.5 pt-1">
          <h2 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-500">
            <Star className="size-3.5 fill-amber-400 text-amber-400" />
            Avis vérifiés sur l'OAG
          </h2>
          <ListeAvis groupeurId={campagne.groupeur.id} />
        </section>
      </div>

      {/* ── Barre d'action sticky au-dessus de la barre d'onglets ─────────── */}
      {ouverte && !estLeGroupeur && (
        <div className="fixed bottom-[var(--hauteur-onglets)] left-1/2 -translate-x-1/2 z-30 w-full max-w-md border-t border-slate-200/90 bg-white/95 backdrop-blur-md p-3 shadow-lg">
          <div className="flex items-center gap-3">
            <div className="shrink-0">
              <p className="text-[10px] text-slate-500 font-semibold">Ma part ({quantite})</p>
              <p className="tabulaire text-base font-black text-slate-900">
                {francs(prixUnitaire * quantite)}
              </p>
            </div>
            <Bouton
              taille="lg"
              className="degrade-accent flex-1 font-bold text-white shadow-md border-none py-2.5 text-xs"
              onClick={() => setFeuilleOuverte(true)}
            >
              Participer au Club
            </Bouton>
          </div>
        </div>
      )}

      {estLeGroupeur && (
        <div className="fixed bottom-[var(--hauteur-onglets)] left-1/2 -translate-x-1/2 z-30 w-full max-w-md border-t border-slate-200/90 bg-white/95 backdrop-blur-md p-3 shadow-lg">
          <Link to={`/groupeur/campagnes/${campagne.id}`}>
            <Bouton ton="contour" pleineLargeur>
              Gérer mon offre (Espace OAG)
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

function GalerieMobile({
  visuels,
  nom,
  ouverte,
  joursRestants,
  atteint,
}: {
  visuels: ElementGalerie[];
  nom: string;
  ouverte: boolean;
  joursRestants: number;
  atteint: boolean;
}) {
  const [actif, setActif] = useState(0);
  const courant = visuels[actif];

  return (
    <div className="space-y-3">
      {/* ── Grande div d'affichage produit agrandie et lumineuse ───────────── */}
      <div className="relative h-[400px] sm:h-[450px] w-full overflow-hidden rounded-3xl bg-gradient-to-b from-slate-50 via-white to-slate-50 shadow-sm border border-slate-200/80 flex items-center justify-center p-3">
        {courant?.genre === "video" ? (
          <video
            key={courant.cle}
            src={courant.url}
            poster={courant.vignette ?? undefined}
            controls
            playsInline
            preload="metadata"
            className="size-full bg-black object-contain rounded-2xl"
          />
        ) : (
          <Visuel
            source={courant?.vignette ?? null}
            nom={nom}
            mode="contain"
            className="size-full object-contain drop-shadow-sm"
          />
        )}

        {/* Badges flottants en haut sans assombrir la photo */}
        <div className="absolute top-3.5 left-3.5 right-3.5 flex items-center justify-between pointer-events-none">
          <div className="flex flex-wrap gap-1.5">
            {ouverte ? (
              <span className="flex items-center gap-1 rounded-full bg-amber-500/95 px-2.5 py-1 text-xs font-bold text-white shadow-xs backdrop-blur-md">
                <Clock className="size-3.5" />
                {tempsRestant(joursRestants)}
              </span>
            ) : (
              <span className="rounded-full bg-slate-800/90 px-2.5 py-1 text-xs font-bold text-white">
                Collecte close
              </span>
            )}
            {atteint && (
              <span className="rounded-full bg-emerald-600 px-2.5 py-1 text-xs font-bold text-white shadow-xs">
                Objectif atteint
              </span>
            )}
          </div>
        </div>
      </div>

      {visuels.length > 1 && (
        <div className="sans-barre flex gap-2.5 overflow-x-auto pb-1 px-1">
          {visuels.map((visuel, rang) => (
            <button
              key={visuel.cle}
              onClick={() => setActif(rang)}
              className={fusionner(
                "relative size-20 shrink-0 overflow-hidden rounded-2xl border-2 p-1 bg-white shadow-2xs transition-all",
                rang === actif
                  ? "border-[color:var(--color-accent)] ring-2 ring-[color:var(--color-accent)]/20 scale-105"
                  : "border-slate-200 opacity-60 hover:opacity-100",
              )}
            >
              <Visuel source={visuel.vignette} nom={nom} mode="contain" className="size-full object-contain" />
              {visuel.genre === "video" && (
                <span className="absolute inset-0 grid place-items-center bg-black/35 rounded-xl">
                  <Play className="size-3.5 fill-white text-white" />
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── La feuille de participation et de paiement ─────────────────────────────

const BUREAUX_POSTE_LOME = [
  "Tokoin",
  "Assivito",
  "Nyékonakpoé",
  "Hédzranawoé",
  "Cacaveli",
  "Agoè-Nyivé",
];

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
  const { utilisateur } = useSession();

  const [etapePaiement, setEtapePaiement] = useState<"formulaire" | "passerelle" | "succes">("formulaire");
  const [operateur, setOperateur] = useState<"tmoney" | "flooz">("tmoney");
  const [telephone, setTelephone] = useState(() => utilisateur?.telephone ?? "");
  const [mode, setMode] = useState<ModeRetrait>("poste");
  const [bureau, setBureau] = useState("");
  const [adresse, setAdresse] = useState("");
  const [codeCopie, setCodeCopie] = useState(false);
  const [etapePasserelle, setEtapePasserelle] = useState<1 | 2 | 3>(1);
  const [minuteurUssd, setMinuteurUssd] = useState(25);
  const [reussite, setReussite] = useState<Participation | null>(null);
  const [transactionInfo, setTransactionInfo] = useState<{ reference: string; montant: number; operateur: string } | null>(null);
  const [erreurPaiement, setErreurPaiement] = useState<string | null>(null);
  const [enTraitement, setEnTraitement] = useState(false);

  // Synchronise le téléphone de l'utilisateur quand il est chargé
  useEffect(() => {
    if (utilisateur?.telephone && !telephone) {
      setTelephone(utilisateur.telephone);
    }
  }, [utilisateur?.telephone, telephone]);

  // Décompte de session USSD en direct
  useEffect(() => {
    if (etapePaiement !== "passerelle") return;
    const intervalle = setInterval(() => {
      setMinuteurUssd((m) => (m > 1 ? m - 1 : 1));
    }, 1000);
    return () => clearInterval(intervalle);
  }, [etapePaiement]);

  const destinationDite = (mode === "poste" ? bureau : adresse).trim().length > 2;
  const telephoneChiffres = telephone.replace(/\D/g, "");
  const telephoneValide = telephoneChiffres.length >= 8;
  const pretAPayer = destinationDite && telephoneValide;

  const maximum = campagne.quantite_maximale
    ? Math.max(1, campagne.quantite_maximale - campagne.quantite_reservee)
    : 20;
  const prix = campagne.prix_courant;
  const total = prix * quantite;

  const reinitialiser = () => {
    setEtapePaiement("formulaire");
    setReussite(null);
    setTransactionInfo(null);
    setErreurPaiement(null);
    setEnTraitement(false);
    surFermeture();
  };

  const lancerPaiement = async () => {
    if (!pretAPayer || enTraitement) return;
    setErreurPaiement(null);
    setEnTraitement(true);
    setEtapePaiement("passerelle");
    setEtapePasserelle(1);
    setMinuteurUssd(25);

    try {
      // 1. Création de la part de commande
      const participation = await api.post<Participation>("/participations/", {
        campagne: campagne.id,
        quantite,
        mode_retrait: mode,
        bureau_poste: mode === "poste" ? bureau.trim() : "",
        adresse_livraison: mode === "livraison" ? adresse.trim() : "",
        code_parrainage: codeParrainRecu(),
      });

      // 2. Simulation de l'envoi de la requête USSD
      await new Promise((r) => setTimeout(r, 700));
      setEtapePasserelle(2);

      // Simulation du délai d'approbation PIN par l'opérateur (2.4s réalistes)
      await new Promise((r) => setTimeout(r, 2400));

      // 3. Encaissement effectif et séquestre sur le backend
      const retour = await api.post<{
        participation: Participation;
        transaction?: { reference: string; montant: number; operateur: string };
      }>(`/participations/${participation.id}/payer/`, {
        operateur,
        numero: telephoneChiffres,
      });

      setEtapePasserelle(3);
      await new Promise((r) => setTimeout(r, 650));

      setReussite(retour.participation);
      setTransactionInfo(retour.transaction ?? null);
      setEtapePaiement("succes");
      await surSucces();
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Une erreur est survenue lors de l'opération Mobile Money. Veuillez réessayer.";
      setErreurPaiement(message);
      setEtapePaiement("formulaire");
    } finally {
      setEnTraitement(false);
    }
  };

  const copierCode = async (code: string) => {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(code);
      setCodeCopie(true);
      setTimeout(() => setCodeCopie(false), 2200);
    }
  };

  return (
    <Feuille
      ouverte={ouverte}
      surFermeture={reinitialiser}
      titre={
        etapePaiement === "succes"
          ? "Paiement validé"
          : etapePaiement === "passerelle"
            ? "Passerelle Mobile Money"
            : "Participer à la campagne"
      }
    >
      <AnimatePresence mode="wait">
        {/* ── 1. ÉCRAN DE SUCCÈS & REÇU OFFICIEL ─────────────────────────────── */}
        {etapePaiement === "succes" && reussite ? (
          <motion.div
            key="succes"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-4 py-2"
          >
            {/* Badge de félicitations */}
            <div className="text-center space-y-2">
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 16 }}
                className="mx-auto grid size-16 place-items-center rounded-full bg-emerald-500 text-white shadow-lg shadow-emerald-500/25"
              >
                <Check className="size-8" strokeWidth={3} />
              </motion.span>
              <h3 className="text-xl font-black text-slate-900">
                Paiement Réussi & Garanti !
              </h3>
              <p className="texte-doux text-xs max-w-xs mx-auto">
                Votre part est réservée. Vos fonds sont sécurisés sous séquestre certifié jusqu'à la remise de votre colis.
              </p>
            </div>

            {/* Reçu électronique officiel */}
            <div className="rounded-2xl border border-slate-200/90 bg-gradient-to-b from-slate-50 to-white p-4 space-y-3 shadow-xs">
              <div className="flex items-center justify-between border-b border-slate-200/70 pb-2.5">
                <div className="flex items-center gap-2">
                  <span
                    className="size-3 rounded-full"
                    style={{ background: operateur === "tmoney" ? "#ffd400" : "#00a0e3" }}
                  />
                  <span className="text-xs font-bold text-slate-900">
                    Reçu {operateur === "tmoney" ? "T-Money TogoCom" : "Moov Money Flooz"}
                  </span>
                </div>
                <span className="rounded-full bg-emerald-100 text-emerald-800 px-2 py-0.5 text-[10px] font-bold">
                  ✓ Validé
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <p className="texte-doux text-[11px]">Réf. Transaction</p>
                  <p className="font-mono font-bold text-slate-900 truncate">
                    {transactionInfo?.reference || `TXN-${operateur.toUpperCase()}-${reussite.id}-9281`}
                  </p>
                </div>
                <div className="text-right">
                  <p className="texte-doux text-[11px]">Montant prélevé</p>
                  <p className="tabulaire font-black text-emerald-700 text-sm">
                    {francs(reussite.montant_total)}
                  </p>
                </div>
                <div>
                  <p className="texte-doux text-[11px]">Numéro débité</p>
                  <p className="font-semibold text-slate-800">
                    +228 {telephoneLisible(telephoneChiffres)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="texte-doux text-[11px]">Statut séquestre</p>
                  <p className="font-bold text-amber-700 text-[11px]">
                    🔒 Consigné
                  </p>
                </div>
              </div>
            </div>

            {/* Cartouche officiel de retrait */}
            <div className="rounded-2xl border-2 border-dashed border-orange-300 bg-orange-50/60 p-4 space-y-3 text-center">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-orange-900">
                  Votre Code de retrait officiel
                </p>
                <div className="mt-1 flex items-center justify-center gap-2">
                  <span className="tabulaire font-mono text-2xl font-black tracking-widest text-slate-900">
                    {codeLisible(reussite.code_retrait ?? "")}
                  </span>
                  <button
                    onClick={() => void copierCode(reussite.code_retrait ?? "")}
                    className="surface-douce grid size-8 place-items-center rounded-lg text-slate-700 hover:text-slate-900 active:scale-90 transition-transform"
                    aria-label="Copier le code de retrait"
                  >
                    <Copy className="size-4" />
                  </button>
                </div>
                {codeCopie && (
                  <p className="text-[11px] font-bold text-emerald-700 mt-1">
                    ✓ Code de retrait copié dans le presse-papier !
                  </p>
                )}
              </div>

              {reussite.code_otp_sms && (
                <div className="rounded-xl bg-white p-2.5 border border-orange-200 text-left flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-bold text-orange-900">Code OTP SMS de secours :</p>
                    <p className="font-mono text-xs font-black tracking-widest text-slate-800">
                      {reussite.code_otp_sms}
                    </p>
                  </div>
                  <span className="text-[10px] text-orange-700/80 font-medium">À dicter à l'agent</span>
                </div>
              )}

              <p className="text-[11px] text-slate-600 border-t border-orange-200/80 pt-2 text-left flex items-start gap-1.5">
                <Landmark className="size-3.5 shrink-0 mt-0.5 text-orange-600" />
                <span><strong>Destination :</strong> {reussite.destination}</span>
              </p>
            </div>

            {/* Actions principales */}
            <div className="space-y-2 pt-1">
              <Bouton
                pleineLargeur
                taille="lg"
                className="degrade-accent text-white font-bold shadow-md"
                onClick={() => naviguer(`/mes-achats/${reussite.id}`)}
              >
                Voir ma commande et mon QR code
              </Bouton>
              <Bouton
                pleineLargeur
                ton="contour"
                onClick={() => {
                  reinitialiser();
                  naviguer("/catalogue");
                }}
              >
                Continuer mes achats
              </Bouton>
            </div>
          </motion.div>
        ) : etapePaiement === "passerelle" ? (
          /* ── 2. ÉCRAN DE LA PASSERELLE USSD MOBILE MONEY ─────────────────── */
          <motion.div
            key="passerelle"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4 py-2"
          >
            {/* En-tête opérateur officiel */}
            <div
              className={fusionner(
                "rounded-2xl p-4 text-white shadow-sm flex items-center justify-between",
                operateur === "tmoney"
                  ? "bg-gradient-to-r from-amber-500 to-yellow-500 text-slate-950 font-bold"
                  : "bg-gradient-to-r from-sky-600 to-blue-600 text-white font-bold"
              )}
            >
              <div className="flex items-center gap-2.5">
                <span className="grid size-9 place-items-center rounded-xl bg-white/20 backdrop-blur-xs">
                  <Smartphone className="size-5" />
                </span>
                <div>
                  <p className="text-xs uppercase tracking-wider opacity-90">
                    {operateur === "tmoney" ? "Passerelle Sécurisée T-Money" : "Passerelle Sécurisée Flooz"}
                  </p>
                  <p className="text-sm font-black">
                    {operateur === "tmoney" ? "TogoCom (*145#)" : "Moov Africa (*155#)"}
                  </p>
                </div>
              </div>
              <span className="rounded-full bg-black/15 px-2.5 py-1 text-[11px] font-bold backdrop-blur-xs flex items-center gap-1">
                <Lock className="size-3" /> 256-bit
              </span>
            </div>

            {/* Simulation Réaliste de l'écran Mobile USSD Prompt */}
            <div className="rounded-3xl border-2 border-slate-800 bg-slate-950 p-4 text-white shadow-xl space-y-3.5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2 text-[10px] text-slate-400">
                <span>Réseau mobile Lomé (Togo)</span>
                <span className="flex items-center gap-1 text-amber-400 font-bold">
                  <Radio className="size-3 animate-pulse" /> Session USSD active ({minuteurUssd}s)
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="rounded-xl bg-slate-900 p-3 border border-slate-800 space-y-1.5">
                  <p className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">
                    Notification USSD Push envoyée sur le mobile
                  </p>
                  <p className="font-extrabold text-sm text-white">
                    GROUP ACHAT TOGO
                  </p>
                  <div className="flex justify-between text-xs pt-1 border-t border-slate-800">
                    <span className="text-slate-400">Montant à prélever :</span>
                    <span className="font-black text-amber-400">{francs(total)}</span>
                  </div>
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Numéro de compte :</span>
                    <span className="font-mono text-slate-200">+228 {telephoneLisible(telephoneChiffres)}</span>
                  </div>
                </div>

                {/* Simulation de la boîte de dialogue de code PIN */}
                <div className="rounded-xl bg-slate-900/90 p-3 text-center space-y-2 border border-slate-800">
                  <p className="text-[11px] text-slate-300 font-medium">
                    Saisissez votre code PIN secret sur votre mobile pour approuver :
                  </p>
                  <div className="flex justify-center items-center gap-2 py-1">
                    {[1, 2, 3, 4].map((i) => (
                      <span
                        key={i}
                        className={fusionner(
                          "size-3 rounded-full transition-all duration-300",
                          etapePasserelle >= 2
                            ? "bg-amber-400 scale-110 shadow-xs shadow-amber-400"
                            : "bg-slate-700"
                        )}
                      />
                    ))}
                  </div>
                  <p className="text-[10px] text-slate-400">
                    {etapePasserelle === 1 && "Émission de la requête au serveur opérateur..."}
                    {etapePasserelle === 2 && "En attente de confirmation opérateur..."}
                    {etapePasserelle === 3 && "✓ Code secret validé avec succès !"}
                  </p>
                </div>
              </div>

              {/* Étapes en direct */}
              <div className="space-y-1.5 border-t border-slate-800/80 pt-2 text-[11px]">
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle2 className="size-3.5 shrink-0" />
                  <span>Connexion établie avec {operateur === "tmoney" ? "T-Money TogoCom" : "Moov Money Flooz"}</span>
                </div>
                <div className={fusionner(
                  "flex items-center gap-2",
                  etapePasserelle >= 2 ? "text-emerald-400" : "text-slate-500"
                )}>
                  {etapePasserelle >= 2 ? (
                    <CheckCircle2 className="size-3.5 shrink-0" />
                  ) : (
                    <Clock className="size-3.5 shrink-0 animate-spin" />
                  )}
                  <span>Vérification sécurisée du code secret PIN</span>
                </div>
                <div className={fusionner(
                  "flex items-center gap-2",
                  etapePasserelle === 3 ? "text-emerald-400 font-bold" : "text-slate-500"
                )}>
                  {etapePasserelle === 3 ? (
                    <CheckCircle2 className="size-3.5 shrink-0" />
                  ) : (
                    <Lock className="size-3.5 shrink-0" />
                  )}
                  <span>Garantie séquestre et consignation des fonds</span>
                </div>
              </div>
            </div>

            <p className="texte-doux text-center text-[11px]">
              Ne fermez pas cette page. La validation s'effectue automatiquement avec l'opérateur.
            </p>

            <button
              onClick={() => setEtapePaiement("formulaire")}
              disabled={enTraitement && etapePasserelle === 3}
              className="w-full text-center text-xs font-semibold text-slate-500 hover:text-slate-800 py-1"
            >
              Annuler et revenir en arrière
            </button>
          </motion.div>
        ) : !peutAgir ? (
          /* ── 3. INVITATION À LA CONNEXION (AVEC REDIRECTION PROPRE) ───────── */
          <motion.div key="connexion" className="space-y-4 py-2">
            <div className="rounded-2xl bg-orange-50 border border-orange-200 p-4 text-center space-y-1.5">
              <span className="mx-auto grid size-12 place-items-center rounded-full bg-orange-100 text-orange-600">
                <Lock className="size-6" />
              </span>
              <h3 className="text-base font-extrabold text-slate-900">
                Connectez-vous pour commander
              </h3>
              <p className="texte-doux text-xs max-w-xs mx-auto">
                Pour rejoindre ce groupage et sécuriser votre achat avec un code de retrait, identifiez-vous en 1 minute.
              </p>
            </div>
            <Link to={`/inscription?retour=/campagnes/${campagne.id}`}>
              <Bouton pleineLargeur taille="lg" className="degrade-accent text-white font-bold">
                Créer mon compte
              </Bouton>
            </Link>
            <Link to={`/connexion?retour=/campagnes/${campagne.id}`}>
              <Bouton ton="contour" pleineLargeur>
                J'ai déjà un compte
              </Bouton>
            </Link>
          </motion.div>
        ) : (
          /* ── 4. FORMULAIRE DE COMMANDE & PAIEMENT MOBILE MONEY ───────────── */
          <motion.div key="paiement" className="space-y-4 py-1">
            {/* Quantité & Montant dynamique */}
            <div>
              <p className="mb-1.5 text-xs font-bold text-slate-700">Quantité souhaitée</p>
              <div className="flex items-center justify-between gap-4">
                <div className="surface flex items-center gap-1 rounded-full p-1 border border-slate-200">
                  <button
                    onClick={() => surQuantite(Math.max(1, quantite - 1))}
                    disabled={quantite <= 1}
                    className="grid size-9 place-items-center rounded-full transition-colors hover:surface-douce disabled:opacity-30"
                    aria-label="Moins"
                  >
                    <Minus className="size-4" />
                  </button>
                  <span className="tabulaire w-10 text-center text-base font-black">
                    {quantite}
                  </span>
                  <button
                    onClick={() => surQuantite(Math.min(maximum, quantite + 1))}
                    disabled={quantite >= maximum}
                    className="grid size-9 place-items-center rounded-full transition-colors hover:surface-douce disabled:opacity-30"
                    aria-label="Plus"
                  >
                    <Plus className="size-4" />
                  </button>
                </div>
                <div className="text-right">
                  <p className="texte-doux text-[11px]">Sous-total commande</p>
                  <p className="tabulaire text-lg font-black text-slate-900">
                    {francs(total)}
                  </p>
                </div>
              </div>
            </div>

            {/* Où récupérer votre colis */}
            <div className="space-y-2.5">
              <p className="text-xs font-bold text-slate-700">Lieu de retrait ou de livraison</p>
              <div className="grid grid-cols-2 gap-2.5">
                {(
                  [
                    {
                      cle: "poste",
                      nom: "Bureau de poste",
                      detail: "La Poste du Togo",
                      icone: Landmark,
                    },
                    {
                      cle: "livraison",
                      nom: "Livré chez moi",
                      detail: "À domicile à Lomé",
                      icone: Truck,
                    },
                  ] as const
                ).map((choix) => (
                  <button
                    key={choix.cle}
                    type="button"
                    onClick={() => setMode(choix.cle)}
                    className={fusionner(
                      "rounded-2xl border p-3 text-left transition-all flex flex-col justify-between",
                      mode === choix.cle
                        ? "border-[color:var(--color-accent)] bg-accent-doux shadow-xs ring-1 ring-[color:var(--color-accent)]"
                        : "surface hover:border-slate-300",
                    )}
                  >
                    <div>
                      <choix.icone
                        className={fusionner(
                          "mb-1.5 size-4",
                          mode === choix.cle ? "text-[color:var(--color-accent)]" : "text-slate-600",
                        )}
                      />
                      <span className="block text-xs font-bold leading-tight text-slate-900">
                        {choix.nom}
                      </span>
                    </div>
                    <span className="texte-doux block text-[10px] leading-snug mt-1">
                      {choix.detail}
                    </span>
                  </button>
                ))}
              </div>

              {mode === "poste" ? (
                <div className="space-y-1.5">
                  <Champ
                    etiquette="Quel bureau de poste vous arrange"
                    placeholder="Ex : Bureau de poste de Tokoin"
                    value={bureau}
                    maxLength={120}
                    onChange={(e) => setBureau(e.target.value)}
                  />
                  {/* Suggestions rapides de bureaux à Lomé */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                    <span className="text-[10px] text-slate-500 font-semibold">Bureaux :</span>
                    {BUREAUX_POSTE_LOME.map((nom) => (
                      <button
                        key={nom}
                        type="button"
                        onClick={() => setBureau(`Bureau de poste de ${nom}`)}
                        className={fusionner(
                          "rounded-full px-2 py-0.5 text-[10px] font-bold transition-all",
                          bureau === `Bureau de poste de ${nom}`
                            ? "bg-slate-900 text-white shadow-2xs"
                            : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                        )}
                      >
                        {nom}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <Champ
                  etiquette="Votre adresse de livraison à Lomé"
                  placeholder="Quartier, rue, maison ou repère"
                  value={adresse}
                  maxLength={250}
                  onChange={(e) => setAdresse(e.target.value)}
                  aide="Seule l'agence de livraison partenaire y a accès. L'OAG ne la voit pas."
                />
              )}
            </div>

            {/* Moyen de paiement Mobile Money */}
            <div className="space-y-2">
              <p className="text-xs font-bold text-slate-700">Moyen de paiement Mobile Money</p>
              <div className="grid grid-cols-2 gap-2.5">
                {(
                  [
                    { cle: "tmoney", nom: "T-Money", code: "*145#", operateur: "TogoCom", teinte: "#ffd400" },
                    { cle: "flooz", nom: "Flooz", code: "*155#", operateur: "Moov Africa", teinte: "#00a0e3" },
                  ] as const
                ).map((moyen) => (
                  <button
                    key={moyen.cle}
                    type="button"
                    onClick={() => setOperateur(moyen.cle)}
                    className={fusionner(
                      "flex items-center gap-2.5 rounded-2xl border p-2.5 text-left transition-all",
                      operateur === moyen.cle
                        ? "border-[color:var(--color-accent)] bg-accent-doux shadow-xs ring-1 ring-[color:var(--color-accent)]"
                        : "surface hover:border-slate-300",
                    )}
                  >
                    <span
                      className="size-8 shrink-0 rounded-xl shadow-xs grid place-items-center font-black text-xs text-slate-900"
                      style={{ background: moyen.teinte }}
                    >
                      {moyen.cle === "tmoney" ? "TM" : "FL"}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs font-extrabold text-slate-900">{moyen.nom}</p>
                      <p className="texte-doux text-[10px]">{moyen.operateur} ({moyen.code})</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Saisie du numéro Mobile Money */}
            <div>
              <Champ
                etiquette={`Numéro ${operateur === "tmoney" ? "T-Money Togo" : "Moov Money Flooz"} à débiter`}
                type="tel"
                inputMode="tel"
                placeholder="90 12 34 56"
                prefixe="+228"
                maxLength={12}
                value={telephone}
                onChange={(e) => setTelephone(e.target.value)}
                aide="Ce numéro recevra la demande de validation USSD sur le téléphone."
              />
            </div>

            {/* Récapitulatif financier et garantie séquestre */}
            <div className="rounded-2xl bg-slate-50 border border-slate-200/90 p-3 space-y-1.5 text-xs">
              <div className="flex justify-between text-slate-600">
                <span>Total des articles ({quantite})</span>
                <span className="tabulaire font-semibold">{francs(total)}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Frais de passerelle Mobile Money</span>
                <span className="font-bold text-emerald-700">0 FCFA (Offerts)</span>
              </div>
              <div className="flex justify-between text-slate-900 font-black border-t border-slate-200/80 pt-1.5 text-sm">
                <span>Total net à régler</span>
                <span className="tabulaire text-[color:var(--color-accent)]">{francs(total)}</span>
              </div>
              <p className="text-[10px] text-slate-500 pt-1 flex items-center gap-1">
                <ShieldCheck className="size-3.5 text-emerald-600 shrink-0" />
                Fonds protégés : bloqués sous séquestre jusqu'à la remise.
              </p>
            </div>

            {erreurPaiement && <Alerte>{erreurPaiement}</Alerte>}

            {/* Bouton de confirmation */}
            <Bouton
              pleineLargeur
              taille="lg"
              className="degrade-accent text-white font-black shadow-lg"
              disabled={!pretAPayer || enTraitement}
              chargement={enTraitement}
              onClick={() => void lancerPaiement()}
            >
              {!destinationDite
                ? "Dites d'abord où livrer"
                : !telephoneValide
                  ? "Entrez votre numéro (+228)"
                  : `Payer ${francs(total)} par ${operateur === "tmoney" ? "T-Money" : "Flooz"}`}
            </Bouton>
          </motion.div>
        )}
      </AnimatePresence>
    </Feuille>
  );
}

function SqueletteFiche() {
  return (
    <div className="space-y-4 p-4 pb-28">
      <Squelette className="aspect-[4/3] w-full rounded-3xl" />
      <Squelette className="h-6 w-3/4 rounded-xl" />
      <Squelette className="h-4 w-1/3 rounded-lg" />
      <Squelette className="h-28 w-full rounded-2xl" />
      <Squelette className="h-16 w-full rounded-2xl" />
    </div>
  );
}
