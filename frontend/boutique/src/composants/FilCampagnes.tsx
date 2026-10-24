import { AnimatePresence, motion } from "framer-motion";
import {
  BadgeCheck,
  ChevronsDown,
  Clock,
  MapPin,
  MessageCircle,
  Share2,
  Store,
  Users,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { CampagneResume } from "@commun/api/types";
import { Jauge } from "@/composants/Jauge";
import { Avatar, Bouton, fusionner } from "@commun/composants/ui";
import { Visuel } from "@/composants/Visuel";
import { francs, tempsRestant } from "@commun/outils/formats";

/**
 * Le fil vertical de l'accueil, sur téléphone.
 *
 * **Une campagne par écran, aimantée au défilement** — le geste qu'on connaît
 * des réseaux sociaux, appliqué aux achats groupés. C'est une demande
 * explicite du produit, et elle se tient : le pouce fait défiler, le produit
 * occupe tout l'écran, la décision d'acheter se prend sans avoir rien à lire
 * de plus que le prix, la jauge et le temps qui reste.
 *
 * Le conteneur gère lui-même son défilement au lieu de laisser faire la
 * page : sinon l'aimantation entrerait en conflit avec la barre d'adresse du
 * navigateur mobile, qui se rétracte et change la hauteur de l'écran en
 * cours de geste.
 */
export function FilCampagnes({
  campagnes,
  surFin,
}: {
  campagnes: CampagneResume[];
  surFin?: () => void;
}) {
  const [actif, setActif] = useState(0);
  const [indiceVu, setIndiceVu] = useState(false);
  const conteneur = useRef<HTMLDivElement>(null);
  const sentinelle = useRef<HTMLDivElement>(null);

  // Quelle carte occupe l'écran : on s'en sert pour n'animer que celle-là.
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

  // Chargement de la suite quand on approche du bas du fil.
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
    <div
      ref={conteneur}
      className="fil-vertical relative h-[calc(100dvh-8.5rem)] overflow-y-auto"
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

      {/* Le geste n'est évident que si on l'a déjà vu ailleurs : on le montre
          une fois, puis on s'efface dès le premier défilement. */}
      <AnimatePresence>
        {!indiceVu && campagnes.length > 1 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: 10 }}
            className="pointer-events-none absolute inset-x-0 bottom-6 flex justify-center"
          >
            <motion.span
              animate={{ y: [0, 9, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
              className="verre-sombre flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold text-white"
            >
              <ChevronsDown className="size-3.5" />
              Faites défiler
            </motion.span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

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
  const remise =
    campagne.prix_courant < campagne.prix_unitaire
      ? Math.round(
          ((campagne.prix_unitaire - campagne.prix_courant) / campagne.prix_unitaire) * 100,
        )
      : 0;

  const partager = async () => {
    const lien = `${window.location.origin}/campagnes/${campagne.id}`;
    // `share` n'existe que sur mobile et en HTTPS ; ailleurs on recopie le
    // lien, ce qui rend le bouton utile partout plutôt que grisé.
    if (navigator.share) {
      try {
        await navigator.share({ title: campagne.titre, url: lien });
        return;
      } catch {
        /* Partage refusé : on retombe sur la copie. */
      }
    }
    await navigator.clipboard?.writeText(lien);
  };

  return (
    <section
      data-rang={rang}
      className="ecran-fil relative h-[calc(100dvh-8.5rem)] w-full overflow-hidden"
    >
      {/* Le visuel bouge un peu plus lentement que le fil : un soupçon de
          profondeur, sans donner le tournis. */}
      <motion.div
        className="absolute inset-0"
        animate={{ scale: actif ? 1.04 : 1 }}
        transition={{ duration: 6, ease: "linear" }}
      >
        <Visuel source={campagne.produit.image} nom={campagne.produit.nom} />
      </motion.div>

      {/* Voile du bas : sans lui, le texte blanc devient illisible dès que la
          photo est claire. */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/88 via-black/35 to-black/15" />

      {/* Colonne d'actions, à portée de pouce. */}
      <div className="absolute bottom-36 right-3 flex flex-col items-center gap-5 text-white">
        <ActionFil
          icone={<Store className="size-6" />}
          libelle="Boutique"
          surClic={() => naviguer(`/campagnes/${campagne.id}`)}
          pastille={
            <Avatar
              nom={campagne.groupeur.nom_commerce || campagne.groupeur.nom_complet}
              taille={44}
              className="ring-2 ring-white/80"
            />
          }
        />
        <ActionFil
          icone={<MessageCircle className="size-6" />}
          libelle="Questions"
          surClic={() => naviguer(`/campagnes/${campagne.id}#discussion`)}
        />
        <ActionFil
          icone={<Share2 className="size-6" />}
          libelle="Partager"
          surClic={partager}
        />
      </div>

      <div className="absolute inset-x-0 bottom-0 space-y-3 p-4 pr-20 text-white">
        <motion.div
          initial={false}
          animate={actif ? { opacity: 1, y: 0 } : { opacity: 0.6, y: 10 }}
          transition={{ duration: 0.4 }}
          className="space-y-3"
        >
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="verre-sombre rounded-full px-2.5 py-1 text-xs font-semibold">
              {campagne.produit.categorie_nom}
            </span>
            <span className="verre-sombre flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold">
              <Clock className="size-3" />
              {tempsRestant(campagne.jours_restants)}
            </span>
            {campagne.minimum_atteint && (
              <span className="rounded-full bg-emerald-500 px-2.5 py-1 text-xs font-bold">
                Objectif atteint
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 text-sm">
            {campagne.groupeur.badge_confiance && <BadgeCheck className="size-4" />}
            <span className="font-semibold">
              {campagne.groupeur.nom_commerce || campagne.groupeur.nom_complet}
            </span>
            {campagne.groupeur.reputation &&
              Number(campagne.groupeur.reputation.note) > 0 && (
                <span className="text-white/80">
                  · {campagne.groupeur.reputation.note}/5
                </span>
              )}
          </div>

          <h2 className="text-[1.6rem] font-extrabold leading-tight drop-shadow-sm">
            {campagne.titre}
          </h2>

          <div className="flex items-end gap-2">
            <span className="tabulaire text-3xl font-extrabold">
              {francs(campagne.prix_courant)}
            </span>
            {remise > 0 && (
              <>
                <span className="tabulaire text-sm text-white/70 line-through">
                  {francs(campagne.prix_unitaire)}
                </span>
                <span className="rounded-full bg-white/95 px-2 py-0.5 text-xs font-bold text-[color:var(--color-mangue-600)]">
                  −{remise} %
                </span>
              </>
            )}
          </div>

          <div className="space-y-1.5">
            <Jauge pourcentage={campagne.pourcentage} atteint={campagne.minimum_atteint} />
            <div className="tabulaire flex items-center justify-between text-xs text-white/85">
              <span>
                {campagne.quantite_reservee} / {campagne.quantite_minimale} pièces
              </span>
              <span className="flex items-center gap-1">
                <Users className="size-3.5" />
                {campagne.nombre_participants} participants
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-1">
            <Bouton
              taille="lg"
              className="flex-1"
              onClick={() => naviguer(`/campagnes/${campagne.id}`)}
            >
              Rejoindre
            </Bouton>
          </div>

          <p className="flex items-center gap-1 pb-1 text-xs text-white/75">
            <MapPin className="size-3" />
            Retrait : {campagne.point_remise}
          </p>
        </motion.div>
      </div>
    </section>
  );
}

function ActionFil({
  icone,
  libelle,
  surClic,
  pastille,
}: {
  icone: React.ReactNode;
  libelle: string;
  surClic: () => void;
  pastille?: React.ReactNode;
}) {
  return (
    <button
      onClick={surClic}
      className={fusionner(
        "flex flex-col items-center gap-1 transition-transform active:scale-90",
        "drop-shadow-[0_2px_6px_rgba(0,0,0,0.45)]",
      )}
      aria-label={libelle}
    >
      {pastille ?? (
        <span className="grid size-11 place-items-center rounded-full bg-white/15 backdrop-blur">
          {icone}
        </span>
      )}
      <span className="text-[0.65rem] font-semibold">{libelle}</span>
    </button>
  );
}
