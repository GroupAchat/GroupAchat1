import { AnimatePresence, motion } from "framer-motion";
import {
  BadgeCheck,
  ChevronsDown,
  Clock,
  Heart,
  MessageCircle,
  Play,
  Share2,
  ShieldCheck,
  Store,
  Truck,
  Users,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { CampagneResume, Categorie } from "@commun/api/types";
import { Jauge } from "@/composants/Jauge";
import { Visuel } from "@/composants/Visuel";
import { Avatar, Bouton, fusionner } from "@commun/composants/ui";
import { francs, tempsRestant } from "@commun/outils/formats";

/**
 * Clips vidéo de démonstration par catégorie pour une expérience
 * type TikTok / Instagram Reels ultra fluide et moderne.
 */
function trouverVideoCampagne(campagne: CampagneResume): string | null {
  return campagne.produit.video ?? null;
}

/**
 * Le fil vidéo vertical immersif de l'accueil (Style Reels / TikTok).
 * Défilement vertical aimanté à un écran par campagne.
 */
export function FilCampagnes({
  campagnes,
  categories,
  categorieActive,
  surChangerCategorie,
  surFin,
}: {
  campagnes: CampagneResume[];
  categories?: Categorie[];
  categorieActive?: string;
  surChangerCategorie?: (slug: string) => void;
  surFin?: () => void;
}) {
  const [actif, setActif] = useState(0);
  const [indiceVu, setIndiceVu] = useState(false);
  const conteneur = useRef<HTMLDivElement>(null);
  const sentinelle = useRef<HTMLDivElement>(null);

  // Détection de la carte active à l'écran
  useEffect(() => {
    const racine = conteneur.current;
    if (!racine) return;

    const observateur = new IntersectionObserver(
      (entrees) => {
        for (const entree of entrees) {
          if (entree.isIntersecting) {
            setActif(Number((entree.target as HTMLElement).dataset.rang));
          }
        }
      },
      { root: racine, threshold: 0.6 },
    );

    racine.querySelectorAll("[data-rang]").forEach((noeud) => observateur.observe(noeud));
    return () => observateur.disconnect();
  }, [campagnes.length]);

  // Chargement infini à l'approche de la fin
  useEffect(() => {
    const cible = sentinelle.current;
    if (!cible || !surFin) return;
    const observateur = new IntersectionObserver(
      (entrees) => entrees[0]?.isIntersecting && surFin(),
      { root: conteneur.current, rootMargin: "400px" },
    );
    observateur.observe(cible);
    return () => observateur.disconnect();
  }, [surFin, campagnes.length]);

  useEffect(() => {
    if (actif > 0) setIndiceVu(true);
  }, [actif]);

  return (
    <div className="relative flex flex-col h-[calc(100dvh-54px-var(--hauteur-onglets))] w-full overflow-hidden bg-black select-none">
      {/* ── Barre de filtres de catégories défilante (blanche & moderne) ─────────── */}
      {categories && categories.length > 0 && surChangerCategorie && (
        <div className="shrink-0 z-20 flex items-center gap-1.5 overflow-x-auto px-3 py-2 bg-white/95 border-b border-slate-200/70 shadow-xs sans-barre">
          <button
            onClick={() => surChangerCategorie("tous")}
            className={fusionner(
              "shrink-0 rounded-full px-3.5 py-1 text-xs font-bold transition-all",
              !categorieActive || categorieActive === "tous"
                ? "bg-[color:var(--color-accent,#ff6a00)] text-white shadow-xs"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200",
            )}
          >
            Pour vous
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => surChangerCategorie(cat.slug)}
              className={fusionner(
                "shrink-0 rounded-full px-3.5 py-1 text-xs font-bold transition-all",
                categorieActive === cat.slug
                  ? "bg-[color:var(--color-accent,#ff6a00)] text-white shadow-xs"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200",
              )}
            >
              {cat.nom}
            </button>
          ))}
        </div>
      )}

      {/* ── Conteneur de défilement aimanté ─────────────────────────── */}
      <div
        ref={conteneur}
        className="fil-vertical flex-1 min-h-0 h-full w-full overflow-y-auto snap-y snap-mandatory"
      >
        {campagnes.map((campagne, rang) => (
          <EcranCampagne
            key={campagne.id}
            campagne={campagne}
            rang={rang}
            actif={rang === actif}
          />
        ))}
        <div ref={sentinelle} aria-hidden />
      </div>

      {/* ── Geste de défilement (affiché au démarrage) ───────────────── */}
      <AnimatePresence>
        {!indiceVu && campagnes.length > 1 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: 10 }}
            className="pointer-events-none absolute inset-x-0 bottom-6 z-20 flex justify-center"
          >
            <motion.span
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
              className="verre-sombre flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold text-white shadow-lg"
            >
              <ChevronsDown className="size-3.5 text-amber-300" />
              Glissez vers le haut
            </motion.span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Un écran de campagne unique (format Reel / TikTok).
 */
function EcranCampagne({
  campagne,
  rang,
  actif,
}: {
  campagne: CampagneResume;
  rang: number;
  actif: boolean;
}) {
  const naviguer = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [enPause, setEnPause] = useState(false);
  const [aime, setAime] = useState(false);
  const [likes, setLikes] = useState(() => 120 + ((campagne.id * 17) % 350));
  const [toastCopie, setToastCopie] = useState(false);

  const videoUrl = trouverVideoCampagne(campagne);

  const remise =
    campagne.prix_courant < campagne.prix_unitaire
      ? Math.round(
          ((campagne.prix_unitaire - campagne.prix_courant) / campagne.prix_unitaire) * 100,
        )
      : 0;

  // Lecture / pause automatique en fonction de la visibilité
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (actif && !enPause) {
      video.play().catch(() => {
        /* Autoplay bloqué par le navigateur */
      });
    } else {
      video.pause();
    }
  }, [actif, enPause]);

  const basculerPause = () => {
    const video = videoRef.current;
    if (video) {
      if (video.paused) {
        video.play();
        setEnPause(false);
      } else {
        video.pause();
        setEnPause(true);
      }
    }
  };

  const gererLike = () => {
    if (aime) {
      setAime(false);
      setLikes((l) => l - 1);
    } else {
      setAime(true);
      setLikes((l) => l + 1);
    }
  };

  const partager = async () => {
    const lien = `${window.location.origin}/campagnes/${campagne.id}`;
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Group Achat Togo: ${campagne.titre}`,
          text: `Commandez à plusieurs à ${francs(campagne.prix_courant)} au lieu de ${francs(campagne.prix_unitaire)} sur Group Achat Togo !`,
          url: lien,
        });
        return;
      } catch {
        /* repli copie */
      }
    }
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(lien);
      setToastCopie(true);
      setTimeout(() => setToastCopie(false), 2400);
    }
  };

  return (
    <section
      data-rang={rang}
      className="ecran-fil snap-start snap-always relative h-full w-full overflow-hidden bg-slate-950"
    >
      {/* ── Fond Média : Vidéo ou Présentation Produit Nette & Centrée ────────── */}
      <div
        className="absolute inset-0 cursor-pointer overflow-hidden flex items-center justify-center"
        onClick={basculerPause}
      >
        {videoUrl ? (
          <video
            ref={videoRef}
            src={videoUrl}
            poster={campagne.produit.image ?? undefined}
            loop
            muted
            playsInline
            className="size-full object-cover"
          />
        ) : (
          <div className="relative size-full flex items-center justify-center bg-gradient-to-b from-slate-900 via-slate-950 to-black">
            {/* Halo lumineux flouté à l'arrière */}
            {campagne.produit.image && (
              <img
                src={campagne.produit.image}
                alt=""
                className="absolute inset-0 size-full object-cover opacity-20 blur-3xl scale-125"
                aria-hidden
              />
            )}
            {/* Produit net et centré, 100% visible sans zoom excessif */}
            <motion.div
              className="relative z-10 w-full flex items-center justify-center p-6 pb-48"
              animate={{ scale: actif ? 1.02 : 1 }}
              transition={{ duration: 4, ease: "easeOut" }}
            >
              <Visuel
                source={campagne.produit.image}
                nom={campagne.produit.nom}
                mode="contain"
                className="max-h-[52vh] max-w-[88%] object-contain drop-shadow-[0_20px_35px_rgba(0,0,0,0.7)]"
              />
            </motion.div>
          </div>
        )}

        {/* Indicateur visuel pause au centre */}
        <AnimatePresence>
          {enPause && (
            <motion.div
              initial={{ opacity: 0, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="absolute inset-0 z-20 flex items-center justify-center bg-black/25"
            >
              <span className="grid size-16 place-items-center rounded-full bg-black/60 text-white backdrop-blur-md">
                <Play className="size-8 translate-x-0.5 fill-white" />
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Dégradé sombre pour la lisibilité des textes ─────────────── */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/95 via-black/40 to-transparent" />

      {/* ── Colonne d'actions droite (Thumb Zone) ───────────────────── */}
      <div className="absolute bottom-24 right-3 z-20 flex flex-col items-center gap-4 text-white">
        {/* Avatar OAG */}
        <button
          onClick={() => naviguer(`/campagnes/${campagne.id}`)}
          className="group relative flex flex-col items-center"
          aria-label="Voir l'OAG"
        >
          <div className="relative">
            <Avatar
              nom={campagne.groupeur.nom_utilisateur}
              taille={46}
              className="ring-2 ring-amber-400 shadow-lg"
            />
            <span className="absolute -bottom-1 -right-1 grid size-5 place-items-center rounded-full bg-[color:var(--color-accent)] text-white shadow">
              <BadgeCheck className="size-3.5" />
            </span>
          </div>
          <span className="mt-1 text-[10px] font-bold text-white/90 drop-shadow">
            OAG
          </span>
        </button>

        {/* J'aime / Like */}
        <button
          onClick={gererLike}
          className="flex flex-col items-center gap-1 transition-transform active:scale-75"
          aria-label="J'aime"
        >
          <span
            className={fusionner(
              "grid size-11 place-items-center rounded-full backdrop-blur-md shadow-md transition-colors",
              aime ? "bg-rose-600 text-white" : "bg-black/45 text-white hover:bg-black/60",
            )}
          >
            <Heart className={fusionner("size-5", aime && "fill-white")} />
          </span>
          <span className="text-[11px] font-bold drop-shadow">{likes}</span>
        </button>

        {/* Discussion / Questions */}
        <button
          onClick={() => naviguer(`/campagnes/${campagne.id}#discussion`)}
          className="flex flex-col items-center gap-1 transition-transform active:scale-90"
          aria-label="Questions"
        >
          <span className="grid size-11 place-items-center rounded-full bg-black/45 backdrop-blur-md text-white shadow-md hover:bg-black/60">
            <MessageCircle className="size-5" />
          </span>
          <span className="text-[11px] font-bold drop-shadow">
            {campagne.nombre_participants}
          </span>
        </button>

        {/* Partager */}
        <button
          onClick={partager}
          className="flex flex-col items-center gap-1 transition-transform active:scale-90"
          aria-label="Partager"
        >
          <span className="grid size-11 place-items-center rounded-full bg-black/45 backdrop-blur-md text-white shadow-md hover:bg-black/60">
            <Share2 className="size-5" />
          </span>
          <span className="text-[11px] font-bold drop-shadow">Partager</span>
        </button>

        {/* Fiche détaillée */}
        <button
          onClick={() => naviguer(`/campagnes/${campagne.id}`)}
          className="flex flex-col items-center gap-1 transition-transform active:scale-90"
          aria-label="Détails"
        >
          <span className="grid size-11 place-items-center rounded-full bg-black/45 backdrop-blur-md text-white shadow-md hover:bg-black/60">
            <Store className="size-5" />
          </span>
          <span className="text-[11px] font-bold drop-shadow">Détails</span>
        </button>
      </div>

      {/* ── Toast de confirmation de copie de lien ───────────────────── */}
      <AnimatePresence>
        {toastCopie && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-20 inset-x-0 z-30 flex justify-center pointer-events-none"
          >
            <span className="rounded-full bg-emerald-600 px-4 py-1.5 text-xs font-bold text-white shadow-lg">
              ✓ Lien de l'offre copié !
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Informations de la campagne au bas de l'écran ─────────────── */}
      <div className="absolute inset-x-0 bottom-0 z-10 space-y-2.5 p-4 pr-16 text-white">
        <motion.div
          initial={false}
          animate={actif ? { opacity: 1, y: 0 } : { opacity: 0.6, y: 10 }}
          transition={{ duration: 0.35 }}
          className="space-y-2.5"
        >
          {/* Badges de confiance & temps restant */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs font-semibold">
            <span className="rounded-full bg-white/20 backdrop-blur-md px-2.5 py-0.5 text-[11px]">
              {campagne.produit.categorie_nom}
            </span>
            <span className="flex items-center gap-1 rounded-full bg-amber-500/90 px-2.5 py-0.5 text-[11px] font-bold text-white shadow-xs">
              <Clock className="size-3" />
              {tempsRestant(campagne.jours_restants)}
            </span>
            <span className="flex items-center gap-1 rounded-full bg-emerald-600/90 px-2 py-0.5 text-[10px] font-bold text-white">
              <ShieldCheck className="size-3" />
              Fonds Consignés
            </span>
          </div>

          {/* OAG Profil */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-white drop-shadow">
              @{campagne.groupeur.nom_utilisateur}
            </span>
            {campagne.groupeur.reputation && Number(campagne.groupeur.reputation.note) > 0 && (
              <span className="rounded bg-black/40 px-1.5 py-0.2 text-[11px] font-semibold text-amber-300">
                ★ {campagne.groupeur.reputation.note}/5
              </span>
            )}
          </div>

          {/* Titre du produit */}
          <h2 className="line-clamp-2 text-lg font-extrabold leading-snug drop-shadow-md">
            {campagne.titre}
          </h2>

          {/* Tarification groupée Togo */}
          <div className="flex items-baseline gap-2.5">
            <span className="tabulaire text-2xl font-black text-amber-300 drop-shadow">
              {francs(campagne.prix_courant)}
            </span>
            {remise > 0 && (
              <>
                <span className="tabulaire text-xs text-white/60 line-through">
                  {francs(campagne.prix_unitaire)}
                </span>
                <span className="rounded-full bg-rose-600 px-2 py-0.5 text-[11px] font-extrabold text-white shadow-xs">
                  −{remise} %
                </span>
              </>
            )}
          </div>

          {/* Jauge de réservation en temps réel */}
          <div className="space-y-1 rounded-xl bg-black/35 backdrop-blur-xs p-2">
            <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} compact />
            <div className="flex items-center justify-between text-[11px] font-semibold text-white/90">
              <span>
                {campagne.quantite_reservee} / {campagne.quantite_minimale} réservés
              </span>
              <span className="flex items-center gap-1 text-amber-300">
                <Users className="size-3" />
                {campagne.nombre_participants} participants
              </span>
            </div>
          </div>

          {/* Bouton CTA d'action principal */}
          <motion.div whileTap={{ scale: 0.98 }}>
            <Bouton
              pleineLargeur
              taille="lg"
              className="degrade-accent border-none font-black text-white shadow-xl py-3 text-sm flex items-center justify-center gap-2"
              onClick={() => naviguer(`/campagnes/${campagne.id}`)}
            >
              <span>Rejoindre le Club</span>
              <span className="rounded-full bg-white/20 px-2 py-0.5 text-xs">
                {francs(campagne.prix_courant)}
              </span>
            </Bouton>
          </motion.div>

          <p className="flex items-center gap-1 text-[10px] text-white/70">
            <Truck className="size-3 text-amber-300" />
            Retrait La Poste du Togo ou livraison à domicile Lomé
          </p>
        </motion.div>
      </div>
    </section>
  );
}
