import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  BadgeCheck,
  Check,
  ChevronRight,
  Clock,
  Minus,
  Play,
  Plus,
  ShieldCheck,
  Star,
  TrendingDown,
  Truck,
  Users,
} from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import type { Campagne, Participation } from "@commun/api/types";
import { Discussion } from "@/composants/Discussion";
import { Feuille } from "@commun/composants/Feuille";
import { Jauge } from "@/composants/Jauge";
import {
  Alerte,
  Avatar,
  Bouton,
  Carte,
  Etiquette,
  fusionner,
  Squelette,
} from "@commun/composants/ui";
import { Visuel } from "@/composants/Visuel";
import { useSession } from "@commun/contexte/Session";
import { dateLongue, francs, tempsRestant } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

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
  const maximum = campagne.quantite_maximale
    ? Math.max(1, campagne.quantite_maximale - campagne.quantite_reservee)
    : 20;

  // Les médias du produit — jusqu'à trois photos et deux vidéos — puis les
  // photos du lot réellement proposé par ce groupeur.
  const visuels: ElementGalerie[] = [
    ...campagne.produit.medias.map((media) => ({
      cle: `p${media.id}`,
      genre: media.genre,
      url: media.fichier,
      vignette: media.vignette,
      legende: media.legende,
    })),
    ...campagne.medias.map((media) => ({
      cle: `m${media.id}`,
      genre: "image" as const,
      url: media.image,
      vignette: media.image,
      legende: media.legende,
    })),
  ];

  return (
    <div className="pb-28 lg:pb-14">
      {/* ── Téléphone : la grande photo d'en-tête ──────────────────────────── */}
      <div className="relative aspect-[4/3] w-full overflow-hidden lg:hidden">
        <Visuel source={visuels[0]?.vignette ?? null} nom={campagne.produit.nom} />
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

      <div className="mx-auto w-full max-w-[88rem] px-4 py-5 lg:px-10 lg:py-7">
        {/* Fil d'Ariane : sur grand écran, on doit savoir d'où l'on vient. */}
        <nav
          className="texte-doux mb-5 hidden items-center gap-1.5 text-sm lg:flex"
          aria-label="Fil d'Ariane"
        >
          <Link to="/" className="hover:text-[color:var(--color-accent)]">
            Accueil
          </Link>
          <ChevronRight className="size-3.5" />
          <Link
            to={`/catalogue?categorie=${campagne.produit.categorie_slug ?? ""}`}
            className="hover:text-[color:var(--color-accent)]"
          >
            {campagne.produit.categorie_nom}
          </Link>
          <ChevronRight className="size-3.5" />
          <span className="truncate text-[color:var(--texte)]">{campagne.titre}</span>
        </nav>

        {/* ── Galerie + panneau d'achat ───────────────────────────────────── */}
        <div className="lg:grid lg:grid-cols-[minmax(0,32rem)_minmax(0,1fr)] lg:items-start lg:gap-9 xl:grid-cols-[minmax(0,38rem)_minmax(0,1fr)]">
          <Galerie
            visuels={visuels}
            nom={campagne.produit.nom}
            className="hidden lg:block lg:sticky lg:top-24"
          />

          <div className="space-y-5">
            <header className="space-y-3">
              <div className="hidden flex-wrap gap-1.5 lg:flex">
                <Etiquette>{campagne.produit.categorie_nom}</Etiquette>
                {ouverte ? (
                  <Etiquette ton="accent">
                    <Clock className="size-3" />
                    {tempsRestant(campagne.jours_restants)}
                  </Etiquette>
                ) : (
                  <Etiquette>Collecte close</Etiquette>
                )}
                {campagne.minimum_atteint && (
                  <Etiquette ton="succes">Objectif atteint</Etiquette>
                )}
              </div>

              <h1 className="text-2xl font-extrabold leading-tight lg:text-[1.75rem]">
                {campagne.titre}
              </h1>

              {campagne.produit.marque && (
                <p className="texte-doux text-sm">
                  Marque&nbsp;: <strong>{campagne.produit.marque}</strong>
                </p>
              )}
            </header>

            {/* Le bloc prix : fond doux pour le détacher du reste, comme sur
                les places de marché où c'est l'information centrale. */}
            <div className="surface-douce space-y-4 rounded-[var(--radius-carte)] p-5">
              <div className="flex flex-wrap items-end gap-2.5">
                <span className="tabulaire text-[2rem] font-extrabold leading-none text-[color:var(--color-accent)]">
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
                <span className="texte-doux ml-auto text-sm">la pièce</span>
              </div>

              {/* Les paliers en tableau : c'est ainsi qu'on lit un prix de
                  gros, d'un coup d'œil, sans faire le calcul soi-même. */}
              {campagne.paliers.length > 0 && (
                <div className="overflow-hidden rounded-2xl border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="surface text-left">
                        <th className="px-4 py-2 font-semibold">Quantité atteinte</th>
                        <th className="px-4 py-2 text-right font-semibold">
                          Prix unitaire
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <LignePalier
                        seuil={`1 à ${campagne.paliers[0].quantite_min - 1}`}
                        prix={campagne.prix_unitaire}
                        actif={campagne.quantite_reservee < campagne.paliers[0].quantite_min}
                      />
                      {campagne.paliers.map((palier, rang) => {
                        const suivant = campagne.paliers[rang + 1];
                        const borne = suivant
                          ? `${palier.quantite_min} à ${suivant.quantite_min - 1}`
                          : `${palier.quantite_min} et plus`;
                        const actif =
                          campagne.quantite_reservee >= palier.quantite_min &&
                          (!suivant || campagne.quantite_reservee < suivant.quantite_min);
                        return (
                          <LignePalier
                            key={palier.id}
                            seuil={borne}
                            prix={palier.prix_unitaire}
                            actif={actif}
                          />
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {prochainPalier && (
                <p className="flex items-start gap-2 text-sm">
                  <TrendingDown className="mt-0.5 size-4 shrink-0 text-[color:var(--color-accent)]" />
                  <span>
                    Encore{" "}
                    <strong className="text-[color:var(--color-accent)]">
                      {prochainPalier.quantite_min - campagne.quantite_reservee} pièces
                    </strong>{" "}
                    et le prix tombe à {francs(prochainPalier.prix_unitaire)}{" "}
                    <span className="texte-doux">pour tout le monde.</span>
                  </span>
                </p>
              )}
            </div>

            {/* Avancement */}
            <div className="space-y-2">
              <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} />
              <div className="tabulaire flex flex-wrap items-center justify-between gap-2 text-sm">
                <span className="font-semibold">
                  {campagne.quantite_reservee} / {campagne.quantite_minimale} pièces
                </span>
                <span className="texte-doux flex items-center gap-1">
                  <Users className="size-4" />
                  {campagne.nombre_participants} participants
                </span>
              </div>
            </div>

            {/* Achat, sur grand écran : la quantité et le bouton sous le prix,
                visibles sans défiler. */}
            {ouverte && !estLeGroupeur && (
              <div className="hidden items-end gap-4 lg:flex">
                <div>
                  <p className="texte-doux mb-1.5 text-sm font-medium">Quantité</p>
                  <div className="surface flex w-fit items-center gap-1 rounded-full p-1">
                    <button
                      onClick={() => setQuantite(Math.max(1, quantite - 1))}
                      disabled={quantite <= 1}
                      className="grid size-9 place-items-center rounded-full transition-colors hover:surface-douce disabled:opacity-40"
                      aria-label="Moins"
                    >
                      <Minus className="size-4" />
                    </button>
                    <span className="tabulaire w-9 text-center font-bold">{quantite}</span>
                    <button
                      onClick={() => setQuantite(Math.min(maximum, quantite + 1))}
                      disabled={quantite >= maximum}
                      className="grid size-9 place-items-center rounded-full transition-colors hover:surface-douce disabled:opacity-40"
                      aria-label="Plus"
                    >
                      <Plus className="size-4" />
                    </button>
                  </div>
                </div>
                <div>
                  <p className="texte-doux mb-1.5 text-sm font-medium">Ma part</p>
                  <p className="tabulaire text-xl font-extrabold">
                    {francs(prixUnitaire * quantite)}
                  </p>
                </div>
                <Bouton
                  taille="lg"
                  className="ml-auto min-w-48"
                  onClick={() => setFeuilleOuverte(true)}
                >
                  Participer
                </Bouton>
              </div>
            )}

            {estLeGroupeur && (
              <Link to={`/groupeur/campagnes/${campagne.id}`}>
                <Bouton ton="contour" pleineLargeur>
                  Gérer ma campagne
                </Bouton>
              </Link>
            )}

            {/* Garantie et retrait, côte à côte quand il y a la place. */}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/40">
                <ShieldCheck className="size-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <p className="text-sm text-emerald-900 dark:text-emerald-200">
                  <strong>Livré ou remboursé.</strong> Votre part reste
                  consignée jusqu'à la livraison.
                </p>
              </div>
              <div className="surface flex gap-3 rounded-2xl p-4 text-sm">
                <Truck className="size-5 shrink-0 text-[color:var(--color-accent)]" />
                <div>
                  <p className="font-semibold">Retrait</p>
                  <p className="texte-doux">{campagne.point_remise}</p>
                </div>
              </div>
            </div>

            {/* Le vendeur */}
            <Carte className="flex items-center gap-3">
              <Avatar
                nom={campagne.groupeur.nom_commerce || campagne.groupeur.nom_complet}
                taille={46}
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
                    {campagne.groupeur.reputation?.campagnes_terminees ?? 0} campagnes
                    menées à terme
                  </span>
                </p>
              </div>
              <Link
                to={`/catalogue?groupeur=${campagne.groupeur.id}`}
                className="hidden shrink-0 text-sm font-semibold text-[color:var(--color-accent)] hover:underline sm:block"
              >
                Ses campagnes
              </Link>
            </Carte>
          </div>
        </div>

        {/* ── Détails et discussion ───────────────────────────────────────── */}
        <div className="mt-10 lg:grid lg:grid-cols-[minmax(0,1fr)_21rem] lg:items-start lg:gap-9">
          <div className="space-y-7">
            {(campagne.description || campagne.produit.description) && (
              <section className="space-y-2">
                <h2 className="text-lg font-bold">Le produit</h2>
                {campagne.produit.description && (
                  <p className="texte-doux whitespace-pre-wrap leading-relaxed">
                    {campagne.produit.description}
                  </p>
                )}
                {campagne.description && (
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {campagne.description}
                  </p>
                )}
              </section>
            )}

            {Object.keys(campagne.caracteristiques_offre).length > 0 && (
              <section className="space-y-3">
                <h2 className="text-lg font-bold">Caractéristiques</h2>
                <div className="overflow-hidden rounded-2xl border">
                  <dl className="divide-y text-sm">
                    {Object.entries(campagne.caracteristiques_offre).map(
                      ([cle, valeur], rang) => (
                        <div
                          key={cle}
                          className={fusionner(
                            "flex justify-between gap-6 px-4 py-2.5",
                            rang % 2 === 1 && "surface-douce",
                          )}
                        >
                          <dt className="texte-doux">{cle}</dt>
                          <dd className="text-right font-medium">{valeur}</dd>
                        </div>
                      ),
                    )}
                  </dl>
                </div>
              </section>
            )}

            <Discussion campagneId={campagne.id} />
          </div>

          {/* Aparté : ce qu'on veut garder à l'œil pendant la lecture. */}
          <aside className="mt-8 space-y-4 lg:sticky lg:top-24 lg:mt-0">
            <Carte className="space-y-3 text-sm">
              <h2 className="font-bold">En résumé</h2>
              <Ligne libelle="Prix du jour" valeur={francs(prixUnitaire)} />
              <Ligne
                libelle="Minimum"
                valeur={`${campagne.quantite_minimale} pièces`}
              />
              <Ligne
                libelle="Déjà réservé"
                valeur={`${campagne.quantite_reservee} pièces`}
              />
              <Ligne libelle="Fin de collecte" valeur={dateLongue(campagne.date_limite)} />
              <Ligne libelle="Point de remise" valeur={campagne.point_remise} />
            </Carte>

            {ouverte && !estLeGroupeur && (
              <Bouton
                taille="lg"
                pleineLargeur
                className="hidden lg:flex"
                onClick={() => setFeuilleOuverte(true)}
              >
                Participer — {francs(prixUnitaire * quantite)}
              </Bouton>
            )}
          </aside>
        </div>
      </div>

      {/* ── Barre d'action, collée en bas sur téléphone ──────────────────── */}
      {ouverte && !estLeGroupeur && (
        <div
          className="verre fixed inset-x-0 bottom-0 z-30 border-t p-3 lg:hidden"
          style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
        >
          <div className="flex items-center gap-3">
            <div className="shrink-0">
              <p className="texte-doux text-xs">Ma part</p>
              <p className="tabulaire font-extrabold">
                {francs(prixUnitaire * quantite)}
              </p>
            </div>
            <Bouton taille="lg" className="flex-1" onClick={() => setFeuilleOuverte(true)}>
              Participer
            </Bouton>
          </div>
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

/**
 * La galerie de grand écran : une grande image, des vignettes dessous.
 *
 * Les vignettes réagissent au **survol** et non au clic seul : c'est le
 * geste attendu sur une place de marché, et il évite un aller-retour de la
 * souris pour comparer deux photos.
 */
/**
 * La galerie de grand écran : un grand visuel, des vignettes carrées dessous.
 *
 * **Les vidéos se lisent sur place**, elles ne renvoient pas ailleurs. Une
 * vignette de vidéo porte un rond de lecture : sans lui, rien ne distingue
 * une image figée d'une vidéo, et personne ne clique.
 *
 * Les vignettes réagissent au survol **pour les photos seulement**. Changer
 * de visuel au passage de la souris pendant qu'une vidéo joue couperait la
 * lecture — c'est agaçant, et c'est exactement ce qu'on fait sans y penser
 * en déplaçant le curseur.
 */
function Galerie({
  visuels,
  nom,
  className,
}: {
  visuels: ElementGalerie[];
  nom: string;
  className?: string;
}) {
  const [actif, setActif] = useState(0);
  const courant = visuels[actif];

  return (
    <div className={className}>
      <div className="surface overflow-hidden rounded-[var(--radius-carte)]">
        <div className="aspect-square">
          {courant?.genre === "video" ? (
            <video
              key={courant.cle}
              src={courant.url}
              poster={courant.vignette ?? undefined}
              controls
              playsInline
              preload="metadata"
              className="size-full bg-black object-contain"
            >
              Votre navigateur ne sait pas lire cette vidéo.
            </video>
          ) : (
            <Visuel source={courant?.vignette ?? null} nom={nom} />
          )}
        </div>
      </div>

      {visuels.length > 1 && (
        <div className="sans-barre mt-3 flex gap-2.5 overflow-x-auto pb-1">
          {visuels.map((visuel, rang) => (
            <button
              key={visuel.cle}
              onMouseEnter={() => {
                // On ne suit le survol que si rien ne joue : voir plus haut.
                if (visuel.genre !== "video" && courant?.genre !== "video") {
                  setActif(rang);
                }
              }}
              onFocus={() => setActif(rang)}
              onClick={() => setActif(rang)}
              className={fusionner(
                "relative size-20 shrink-0 overflow-hidden rounded-xl border-2 transition-all",
                rang === actif
                  ? "border-[color:var(--color-accent)]"
                  : "border-transparent opacity-70 hover:opacity-100",
              )}
              aria-label={
                visuel.legende ||
                `${visuel.genre === "video" ? "Vidéo" : "Photo"} ${rang + 1}`
              }
              aria-current={rang === actif}
            >
              <Visuel source={visuel.vignette} nom={nom} />
              {visuel.genre === "video" && (
                <span className="absolute inset-0 grid place-items-center bg-black/35">
                  <span className="grid size-7 place-items-center rounded-full bg-white/90 text-black">
                    <Play className="size-3.5 fill-current" />
                  </span>
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Le décompte rassure sur ce qui reste à voir. */}
      {visuels.length > 1 && (
        <p className="texte-doux mt-2 text-xs">
          {visuels.filter((v) => v.genre === "image").length} photo
          {visuels.filter((v) => v.genre === "image").length > 1 ? "s" : ""}
          {visuels.some((v) => v.genre === "video") &&
            ` · ${visuels.filter((v) => v.genre === "video").length} vidéo${
              visuels.filter((v) => v.genre === "video").length > 1 ? "s" : ""
            }`}
        </p>
      )}
    </div>
  );
}

function LignePalier({
  seuil,
  prix,
  actif,
}: {
  seuil: string;
  prix: number;
  actif: boolean;
}) {
  return (
    <tr
      className={fusionner(
        "border-t",
        actif && "bg-accent-doux font-semibold text-[color:var(--color-accent-fort)]",
      )}
    >
      <td className="px-4 py-2.5">
        {seuil} pièces
        {actif && <span className="ml-2 text-xs font-bold">· prix actuel</span>}
      </td>
      <td className="tabulaire px-4 py-2.5 text-right">{francs(prix)}</td>
    </tr>
  );
}

function Ligne({ libelle, valeur }: { libelle: string; valeur: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b pb-2 last:border-0 last:pb-0">
      <span className="texte-doux shrink-0">{libelle}</span>
      <span className="text-right font-medium">{valeur}</span>
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
      <Squelette className="aspect-[4/3] rounded-none lg:hidden" />
      <div className="mx-auto w-full max-w-[88rem] px-4 py-5 lg:px-10 lg:py-7">
        <div className="lg:grid lg:grid-cols-[minmax(0,32rem)_minmax(0,1fr)] lg:gap-9 xl:grid-cols-[minmax(0,38rem)_minmax(0,1fr)]">
          <Squelette className="hidden aspect-square lg:block" />
          <div className="space-y-4">
            <Squelette className="h-7 w-3/4" />
            <Squelette className="h-9 w-40" />
            <Squelette className="h-36" />
            <Squelette className="h-3 w-full rounded-full" />
            <Squelette className="h-20" />
          </div>
        </div>
      </div>
    </div>
  );
}
