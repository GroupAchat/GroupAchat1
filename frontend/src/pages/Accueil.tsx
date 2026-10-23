import { motion } from "framer-motion";
import { ArrowRight, QrCode, ShieldCheck, Sparkles, Wallet } from "lucide-react";
import { Link } from "react-router-dom";

import type { CampagneResume, Categorie, Page } from "@/api/types";
import { CarteCampagne, SqueletteCarte } from "@/composants/CarteCampagne";
import { FilCampagnes } from "@/composants/FilCampagnes";
import { Bouton, EtatVide } from "@/composants/ui";
import { useRequete } from "@/outils/requetes";

/**
 * L'accueil, en deux formes selon l'écran.
 *
 * **Sur téléphone**, un fil vertical plein écran : une campagne à la fois,
 * aimantée, qu'on parcourt au pouce. **Sur ordinateur**, une bannière et une
 * grille : le geste du fil n'a pas de sens à la souris, et l'espace permet de
 * comparer plusieurs offres d'un coup d'œil.
 */
export default function Accueil() {
  const { donnees, chargement } = useRequete<Page<CampagneResume>>(
    "/catalogue/campagnes/?tri=recent&page_size=24",
  );
  const { donnees: rayons } = useRequete<Categorie[]>("/catalogue/categories/");
  const campagnes = donnees?.results ?? [];

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

      {/* ── Grand écran : bannière et grille ──────────────────────────────── */}
      <div className="mx-auto hidden max-w-6xl px-4 py-10 md:block">
        <Banniere />

        {rayons && rayons.length > 0 && (
          <section className="mt-10">
            <h2 className="mb-4 text-xl font-bold">Explorer par rayon</h2>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              {rayons.map((rayon, rang) => (
                <motion.div
                  key={rayon.id}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: rang * 0.06 }}
                >
                  <Link
                    to={`/catalogue?categorie=${rayon.slug}`}
                    className="surface group flex items-center justify-between gap-3 rounded-[var(--radius-carte)] p-5 transition-all hover:-translate-y-0.5 hover:border-[color:var(--color-accent)] hover:shadow-lg"
                  >
                    <div>
                      <p className="font-bold">{rayon.nom}</p>
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

        <section className="mt-12">
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

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {chargement
              ? Array.from({ length: 6 }, (_, rang) => <SqueletteCarte key={rang} />)
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

function Banniere() {
  const garanties = [
    {
      icone: ShieldCheck,
      titre: "Argent consigné",
      texte: "Votre part est bloquée jusqu'à la livraison. Jamais versée d'avance.",
    },
    {
      icone: QrCode,
      titre: "Code de retrait",
      texte: "Un code unique par commande. Le colis ne se remet que contre lui.",
    },
    {
      icone: Wallet,
      titre: "Livré ou remboursé",
      texte: "Minimum non atteint ? Vous êtes remboursé intégralement.",
    },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="relative overflow-hidden rounded-[2rem] p-10 text-white"
    >
      <div className="degrade-accent absolute inset-0" />
      <span className="absolute -right-16 -top-24 size-80 rounded-full bg-white/12 blur-3xl" />
      <span className="absolute -bottom-28 left-10 size-72 rounded-full bg-black/15 blur-3xl" />

      <div className="relative max-w-2xl">
        <span className="verre-sombre inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold">
          <Sparkles className="size-3.5" />
          Achats groupés au Togo
        </span>
        <h1 className="mt-4 text-4xl font-extrabold leading-tight lg:text-5xl">
          Achetez à plusieurs.
          <br />
          Payez moins cher, sans risque.
        </h1>
        <p className="mt-4 max-w-xl text-white/85">
          Rejoignez une campagne, réglez votre part par Mobile Money. L'argent
          reste consigné jusqu'à ce que vous ayez votre colis en main.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link to="/catalogue">
            <Bouton
              ton="contour"
              taille="lg"
              className="border-none bg-white text-[color:var(--color-accent-fort)] hover:bg-white"
            >
              Voir les campagnes
            </Bouton>
          </Link>
          <Link to="/profil/devenir-groupeur">
            <Bouton
              ton="fantome"
              taille="lg"
              className="border border-white/40 text-white hover:bg-white/10"
            >
              Devenir groupeur
            </Bouton>
          </Link>
        </div>
      </div>

      <div className="relative mt-10 grid gap-4 sm:grid-cols-3">
        {garanties.map((garantie, rang) => (
          <motion.div
            key={garantie.titre}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 + rang * 0.1 }}
            className="verre-sombre rounded-2xl p-4"
          >
            <garantie.icone className="size-5" />
            <p className="mt-2 font-bold">{garantie.titre}</p>
            <p className="mt-1 text-sm text-white/80">{garantie.texte}</p>
          </motion.div>
        ))}
      </div>
    </motion.section>
  );
}
