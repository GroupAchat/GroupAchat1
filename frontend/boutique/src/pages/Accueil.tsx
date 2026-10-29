import { motion } from "framer-motion";
import { ArrowRight, QrCode, ShieldCheck, Sparkles, Wallet } from "lucide-react";
import { Link } from "react-router-dom";

import type { CampagneResume, Categorie, Page } from "@commun/api/types";
import { CarteCampagne, SqueletteCarte } from "@/composants/CarteCampagne";
import {
  CarteDerniereChance,
  TitreDerniereChance,
} from "@/composants/CarteDerniereChance";
import { FilCampagnes } from "@/composants/FilCampagnes";
import { Bouton, EtatVide, Squelette } from "@commun/composants/ui";
import { useRequete } from "@commun/outils/requetes";

/**
 * L'accueil, en deux formes selon l'écran.
 *
 * **Sur téléphone**, un fil vertical plein écran : une campagne à la fois,
 * aimantée, qu'on parcourt au pouce. **Sur ordinateur**, une bannière, les
 * rayons, les campagnes qui se terminent, puis la grille complète : le
 * geste du fil n'a pas de sens à la souris, et l'espace permet de comparer
 * plusieurs offres d'un coup d'œil.
 */

/** En deçà de ce nombre de jours, une campagne entre en « dernière chance ». */
const JOURS_URGENTS = 4;

export default function Accueil() {
  const { donnees, chargement } = useRequete<Page<CampagneResume>>(
    "/catalogue/campagnes/?tri=recent&page_size=24",
  );
  const { donnees: rayons } = useRequete<Categorie[]>("/catalogue/categories/");
  const campagnes = donnees?.results ?? [];

  // Les campagnes qui se terminent, de la plus pressée à la moins pressée.
  // Celles dont le minimum est déjà atteint restent dans la liste : leur
  // date limite approche quand même, et on peut encore les rejoindre.
  const urgentes = campagnes
    .filter((c) => c.statut === "en_cours" && c.jours_restants <= JOURS_URGENTS)
    .sort((a, b) => a.jours_restants - b.jours_restants)
    .slice(0, 6);

  return (
    <>
      {/* ── Téléphone : le fil ────────────────────────────────────────────── */}
      <div className="md:hidden">
        {chargement ? (
          <div className="h-[calc(100dvh-8.5rem)] p-4">
            <div className="squelette size-full rounded-[var(--radius-carte)]" />
          </div>
        ) : campagnes.length ? (
          <FilCampagnes campagnes={campagnes} />
        ) : (
          <EtatVide
            icone={<Sparkles className="size-7" />}
            titre="Aucune campagne pour l'instant"
            texte="Les groupeurs préparent leurs prochains arrivages. Revenez bientôt."
            action={
              <Link to="/communaute">
                <Bouton>Demander un produit</Bouton>
              </Link>
            }
          />
        )}
      </div>

      {/* ── Grand écran ───────────────────────────────────────────────────── */}
      <div className="mx-auto hidden w-full max-w-[90rem] px-6 py-8 md:block lg:px-10">
        <Banniere />

        {rayons && rayons.length > 0 && (
          <section className="mt-8">
            <h2 className="mb-4 text-lg font-bold">Explorer par rayon</h2>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 2xl:grid-cols-6">
              {rayons.map((rayon, rang) => (
                <motion.div
                  key={rayon.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: rang * 0.05 }}
                >
                  <Link
                    to={`/catalogue?categorie=${rayon.slug}`}
                    className="surface group flex items-center justify-between gap-3 rounded-2xl p-4 transition-all hover:-translate-y-0.5 hover:border-[color:var(--color-accent)] hover:shadow-lg"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-bold">{rayon.nom}</p>
                      <p className="texte-doux text-sm">
                        {rayon.nombre_campagnes} campagne
                        {rayon.nombre_campagnes > 1 ? "s" : ""}
                      </p>
                    </div>
                    <ArrowRight className="size-4 shrink-0 transition-transform group-hover:translate-x-1" />
                  </Link>
                </motion.div>
              ))}
            </div>
          </section>
        )}

        {/* ── Dernière chance ────────────────────────────────────────────── */}
        {(chargement || urgentes.length > 0) && (
          <section className="mt-12">
            {chargement ? (
              <div className="grid gap-4 xl:grid-cols-2">
                <Squelette className="h-36" />
                <Squelette className="h-36" />
              </div>
            ) : (
              <>
                <TitreDerniereChance nombre={urgentes.length} />
                {/* Deux colonnes seulement à partir de 1280 px : ces cartes
                    sont horizontales, les serrer plus tôt tasserait le
                    compte à rebours contre le titre. */}
                <div className="mt-4 grid gap-4 xl:grid-cols-2">
                  {urgentes.map((campagne, rang) => (
                    <CarteDerniereChance
                      key={campagne.id}
                      campagne={campagne}
                      index={rang}
                    />
                  ))}
                </div>
              </>
            )}
          </section>
        )}

        <section className="mt-14">
          <div className="mb-4 flex items-end justify-between">
            <div>
              <h2 className="text-xl font-bold">Campagnes en cours</h2>
              <p className="texte-doux text-sm">
                Rejoignez un groupage, payez votre part, retirez votre colis.
              </p>
            </div>
            <Link
              to="/catalogue"
              className="text-sm font-semibold text-[color:var(--color-accent)] hover:underline"
            >
              Tout voir
            </Link>
          </div>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
            {chargement
              ? Array.from({ length: 8 }, (_, rang) => <SqueletteCarte key={rang} />)
              : campagnes.map((campagne, rang) => (
                  <CarteCampagne key={campagne.id} campagne={campagne} index={rang} />
                ))}
          </div>

          {!chargement && campagnes.length === 0 && (
            <EtatVide
              icone={<Sparkles className="size-7" />}
              titre="Aucune campagne pour l'instant"
              texte="Les groupeurs préparent leurs prochains arrivages."
            />
          )}
        </section>
      </div>
    </>
  );
}

/**
 * La bannière.
 *
 * **Volontairement basse.** Une bannière pleine hauteur repousse les
 * produits sous la ligne de flottaison : le visiteur arrive sur une
 * promesse au lieu d'arriver sur l'offre. Les trois garanties passent donc
 * sur la droite, en colonne, au lieu de s'empiler dessous.
 */
function Banniere() {
  const garanties = [
    {
      icone: ShieldCheck,
      titre: "Argent consigné",
      texte: "Remis au groupeur une fois la collecte réussie.",
    },
    {
      icone: QrCode,
      titre: "Code de retrait",
      texte: "Un code unique par commande.",
    },
    {
      icone: Wallet,
      titre: "Remboursé si le groupage échoue",
      texte: "Minimum non atteint : sans décision du groupeur sous 7 jours, vous êtes remboursé.",
    },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="relative overflow-hidden rounded-[1.75rem] p-7 text-white lg:p-9"
    >
      <div className="degrade-accent absolute inset-0" />
      <span className="absolute -right-16 -top-24 size-72 rounded-full bg-white/12 blur-3xl" />
      <span className="absolute -bottom-28 left-10 size-64 rounded-full bg-black/15 blur-3xl" />

      <div className="relative flex flex-col gap-7 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-xl">
          <span className="verre-sombre inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold">
            <Sparkles className="size-3.5" />
            Achats groupés au Togo
          </span>
          <h1 className="mt-3 text-[1.9rem] font-extrabold leading-[1.15] lg:text-4xl">
            Achetez à plusieurs. Payez moins cher, sans risque.
          </h1>
          <p className="mt-2.5 text-sm text-white/85 lg:text-base">
            Rejoignez une campagne, réglez votre part par Mobile Money.
            Votre part reste consignée tant que la collecte n'est pas acquise ; votre code de retrait prouve ensuite la remise du colis.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link to="/catalogue">
              <Bouton
                ton="contour"
                className="border-none bg-white text-[color:var(--color-accent-fort)] hover:bg-white"
              >
                Voir les campagnes
              </Bouton>
            </Link>
            <Link to="/profil/devenir-groupeur">
              <Bouton
                ton="fantome"
                className="border border-white/40 text-white hover:bg-white/10"
              >
                Devenir groupeur
              </Bouton>
            </Link>
          </div>
        </div>

        {/* En colonne à droite dès qu'il y a la place : la bannière reste
            basse et les campagnes remontent dans l'écran. */}
        <div className="grid shrink-0 gap-2.5 sm:grid-cols-3 lg:w-[19rem] lg:grid-cols-1">
          {garanties.map((garantie, rang) => (
            <motion.div
              key={garantie.titre}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + rang * 0.08 }}
              className="verre-sombre flex items-center gap-3 rounded-xl px-3.5 py-2.5"
            >
              <garantie.icone className="size-4 shrink-0" />
              <div className="min-w-0">
                <p className="text-sm font-bold leading-tight">{garantie.titre}</p>
                <p className="text-xs leading-tight text-white/75">{garantie.texte}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.section>
  );
}
