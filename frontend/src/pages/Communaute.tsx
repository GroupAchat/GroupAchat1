import { motion } from "framer-motion";
import { Flame, Hand, Lightbulb, Plus } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import type { Categorie, DemandeProduit, Page } from "@commun/api/types";
import { Feuille } from "@commun/composants/Feuille";
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
  ZoneTexte,
} from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { depuis, francs } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/**
 * L'espace communautaire : ce que les acheteurs réclament.
 *
 * Le catalogue habituel va du vendeur vers l'acheteur ; ici c'est l'inverse.
 * Le compteur « moi aussi » sert de signal aux groupeurs en quête d'une
 * campagne à lancer.
 */
export default function Communaute() {
  const { peutAgir } = useSession();
  const { donnees, chargement, recharger } = useRequete<Page<DemandeProduit>>(
    "/demandes/?statut=ouverte",
  );
  const [feuille, setFeuille] = useState(false);

  const demandes = donnees?.results ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-5 px-4 py-6">
      <header className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold">Demandes</h1>
          <p className="texte-doux text-sm">
            Vous cherchez un produit ? Dites-le. Les groupeurs lisent cette page.
          </p>
        </div>
        {peutAgir && (
          <Bouton icone={<Plus className="size-4" />} onClick={() => setFeuille(true)}>
            Demander
          </Bouton>
        )}
      </header>

      {chargement ? (
        <div className="space-y-3">
          <Squelette className="h-28" />
          <Squelette className="h-28" />
        </div>
      ) : demandes.length === 0 ? (
        <EtatVide
          icone={<Lightbulb className="size-7" />}
          titre="Aucune demande en cours"
          texte="Soyez le premier à réclamer un produit : plus vous serez nombreux à le vouloir, plus un groupeur a de raisons de le lancer."
          action={
            peutAgir ? (
              <Bouton onClick={() => setFeuille(true)}>Publier une demande</Bouton>
            ) : (
              <Link to="/connexion">
                <Bouton>Se connecter</Bouton>
              </Link>
            )
          }
        />
      ) : (
        <ul className="space-y-3">
          {demandes.map((demande, rang) => (
            <CarteDemande
              key={demande.id}
              demande={demande}
              index={rang}
              surChangement={recharger}
            />
          ))}
        </ul>
      )}

      <FeuilleDemande
        ouverte={feuille}
        surFermeture={() => setFeuille(false)}
        surSucces={async () => {
          setFeuille(false);
          await recharger();
        }}
      />
    </div>
  );
}

function CarteDemande({
  demande,
  index,
  surChangement,
}: {
  demande: DemandeProduit;
  index: number;
  surChangement: () => void;
}) {
  const { peutAgir } = useSession();
  const [interesse, setInteresse] = useState(demande.interesse);
  const [compte, setCompte] = useState(demande.nombre_interets);

  const basculer = async () => {
    if (!peutAgir) return;
    const avant = { interesse, compte };
    setInteresse(!interesse);
    setCompte(compte + (interesse ? -1 : 1));
    try {
      const retour = await api.post<{ interesse: boolean; nombre_interets: number }>(
        `/demandes/${demande.id}/moi-aussi/`,
      );
      setInteresse(retour.interesse);
      setCompte(retour.nombre_interets);
    } catch {
      setInteresse(avant.interesse);
      setCompte(avant.compte);
      surChangement();
    }
  };

  return (
    <motion.li
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index, 6) * 0.05 }}
    >
      <Carte className="space-y-3">
        <div className="flex items-start gap-3">
          <Avatar nom={demande.auteur.nom_affiche} taille={38} />
          <div className="min-w-0 flex-1">
            <p className="text-sm">
              <strong>{demande.auteur.nom_affiche}</strong>{" "}
              <span className="texte-doux">· {depuis(demande.cree_le)}</span>
            </p>
            <h3 className="mt-0.5 font-bold leading-snug">{demande.titre}</h3>
          </div>
          {compte >= 4 && (
            <Etiquette ton="accent">
              <Flame className="size-3" />
              Populaire
            </Etiquette>
          )}
        </div>

        {demande.description && (
          <p className="texte-doux text-sm leading-relaxed">{demande.description}</p>
        )}

        <div className="flex flex-wrap items-center gap-2 text-xs">
          {demande.categorie_nom && <Etiquette>{demande.categorie_nom}</Etiquette>}
          {demande.budget_indicatif && (
            <Etiquette>Budget ≈ {francs(demande.budget_indicatif)}</Etiquette>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 border-t pt-3">
          <span className="texte-doux text-sm">
            <strong className="text-[color:var(--texte)]">{compte}</strong> intéressé
            {compte > 1 ? "s" : ""}
          </span>
          <button
            onClick={basculer}
            disabled={!peutAgir}
            className={fusionner(
              "flex items-center gap-1.5 rounded-full px-3.5 py-2 text-sm font-semibold transition-all active:scale-95 disabled:opacity-50",
              interesse
                ? "degrade-accent text-white"
                : "surface hover:border-[color:var(--color-accent)]",
            )}
            aria-pressed={interesse}
          >
            <Hand className="size-4" />
            {interesse ? "Moi aussi !" : "Moi aussi"}
          </button>
        </div>
      </Carte>
    </motion.li>
  );
}

function FeuilleDemande({
  ouverte,
  surFermeture,
  surSucces,
}: {
  ouverte: boolean;
  surFermeture: () => void;
  surSucces: () => Promise<void>;
}) {
  const { donnees: rayons } = useRequete<Categorie[]>("/catalogue/categories/");
  const [saisie, setSaisie] = useState({
    titre: "",
    description: "",
    categorie: "",
    budget_indicatif: "",
  });

  const envoi = useAction(async () => {
    await api.post("/demandes/", {
      titre: saisie.titre,
      description: saisie.description,
      categorie: saisie.categorie ? Number(saisie.categorie) : null,
      budget_indicatif: saisie.budget_indicatif ? Number(saisie.budget_indicatif) : null,
    });
    setSaisie({ titre: "", description: "", categorie: "", budget_indicatif: "" });
    await surSucces();
  });

  const rayonsPlats = (rayons ?? []).flatMap((rayon) => [rayon, ...rayon.sous_categories]);

  return (
    <Feuille ouverte={ouverte} surFermeture={surFermeture} titre="Demander un produit">
      <form
        onSubmit={(evenement) => {
          evenement.preventDefault();
          void envoi.lancer(undefined as never);
        }}
        className="space-y-4 py-2"
      >
        <Champ
          etiquette="Quel produit cherchez-vous ?"
          placeholder="Panneau solaire 200 W, sacs de ciment…"
          required
          value={saisie.titre}
          onChange={(e) => setSaisie({ ...saisie, titre: e.target.value })}
          erreur={envoi.erreur?.pourChamp("titre")}
        />
        <ZoneTexte
          etiquette="Précisions (facultatif)"
          rows={3}
          placeholder="Marque souhaitée, quantité, délai…"
          value={saisie.description}
          onChange={(e) => setSaisie({ ...saisie, description: e.target.value })}
        />
        <div className="space-y-1.5">
          <label className="block text-sm font-medium">Rayon</label>
          <select
            value={saisie.categorie}
            onChange={(e) => setSaisie({ ...saisie, categorie: e.target.value })}
            className="surface h-12 w-full rounded-2xl px-4 text-[0.95rem] outline-none focus:border-[color:var(--color-accent)]"
          >
            <option value="">Sans rayon</option>
            {rayonsPlats.map((rayon) => (
              <option key={rayon.id} value={rayon.id}>
                {rayon.nom}
              </option>
            ))}
          </select>
        </div>
        <Champ
          etiquette="Budget indicatif (facultatif)"
          type="number"
          inputMode="numeric"
          min={0}
          placeholder="120000"
          prefixe="FCFA"
          value={saisie.budget_indicatif}
          onChange={(e) => setSaisie({ ...saisie, budget_indicatif: e.target.value })}
        />

        <Alerte>{envoi.erreur?.message}</Alerte>

        <Bouton type="submit" pleineLargeur taille="lg" chargement={envoi.envoi}>
          Publier ma demande
        </Bouton>
      </form>
    </Feuille>
  );
}
