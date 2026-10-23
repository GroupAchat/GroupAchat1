import { motion } from "framer-motion";
import { ArrowLeft, Plus, Trash2, TrendingDown } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import type { Campagne, Categorie, Produit } from "@/api/types";
import {
  Alerte,
  Bouton,
  Carte,
  Champ,
  fusionner,
  ZoneTexte,
} from "@/composants/ui";
import { francs } from "@/outils/formats";
import { api, useAction, useRequete } from "@/outils/requetes";

interface Palier {
  quantite_min: string;
  prix_unitaire: string;
}

/**
 * Création d'une campagne, en deux temps : le produit, puis l'offre.
 *
 * Le produit est créé d'abord parce qu'il vit indépendamment de l'offre —
 * un autre groupeur pourra proposer le même. Les deux écrans tiennent dans
 * une seule page : couper en assistant multi-pages ferait perdre la vue
 * d'ensemble sur un formulaire aussi court.
 */
export default function NouvelleCampagne() {
  const naviguer = useNavigate();
  const { donnees: rayons } = useRequete<Categorie[]>("/catalogue/categories/");
  const rayonsPlats = (rayons ?? []).flatMap((rayon) => [rayon, ...rayon.sous_categories]);

  const [produit, setProduit] = useState({
    nom: "",
    marque: "",
    categorie: "",
    description: "",
  });
  const [offre, setOffre] = useState({
    titre: "",
    description: "",
    prix_unitaire: "",
    quantite_minimale: "",
    quantite_maximale: "",
    date_limite: dansJours(14),
    point_remise: "",
  });
  const [paliers, setPaliers] = useState<Palier[]>([]);

  const creation = useAction(async () => {
    const fiche = await api.post<Produit>("/groupeur/produits/", {
      nom: produit.nom,
      marque: produit.marque,
      categorie: Number(produit.categorie),
      description: produit.description,
    });
    const campagne = await api.post<Campagne>("/groupeur/campagnes/", {
      produit: fiche.id,
      titre: offre.titre || fiche.nom,
      description: offre.description,
      prix_unitaire: Number(offre.prix_unitaire),
      quantite_minimale: Number(offre.quantite_minimale),
      quantite_maximale: offre.quantite_maximale ? Number(offre.quantite_maximale) : null,
      date_limite: new Date(offre.date_limite).toISOString(),
      point_remise: offre.point_remise,
      paliers: paliers
        .filter((palier) => palier.quantite_min && palier.prix_unitaire)
        .map((palier) => ({
          quantite_min: Number(palier.quantite_min),
          prix_unitaire: Number(palier.prix_unitaire),
        })),
    });
    naviguer(`/groupeur/campagnes/${campagne.id}`);
    return campagne;
  });

  const prix = Number(offre.prix_unitaire) || 0;
  const minimum = Number(offre.quantite_minimale) || 0;

  return (
    <div className="mx-auto max-w-2xl space-y-5 px-4 py-6">
      <Link
        to="/groupeur/campagnes"
        className="texte-doux inline-flex items-center gap-1.5 text-sm font-semibold"
      >
        <ArrowLeft className="size-4" />
        Mes campagnes
      </Link>

      <header>
        <h1 className="text-2xl font-extrabold">Nouvelle campagne</h1>
        <p className="texte-doux text-sm">
          Elle démarre en brouillon : vous la publierez quand elle vous
          conviendra.
        </p>
      </header>

      <form
        onSubmit={(evenement) => {
          evenement.preventDefault();
          void creation.lancer(undefined as never);
        }}
        className="space-y-5"
      >
        <Carte className="space-y-4">
          <h2 className="font-bold">1. Le produit</h2>
          <Champ
            etiquette="Nom du produit"
            placeholder="Sac de riz parfumé 25 kg"
            required
            value={produit.nom}
            onChange={(e) => setProduit({ ...produit, nom: e.target.value })}
            erreur={creation.erreur?.pourChamp("nom")}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Champ
              etiquette="Marque (facultatif)"
              placeholder="Délice"
              value={produit.marque}
              onChange={(e) => setProduit({ ...produit, marque: e.target.value })}
            />
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Rayon</label>
              <select
                required
                value={produit.categorie}
                onChange={(e) => setProduit({ ...produit, categorie: e.target.value })}
                className="surface h-12 w-full rounded-2xl px-4 text-[0.95rem] outline-none focus:border-[color:var(--color-accent)]"
              >
                <option value="">Choisir…</option>
                {rayonsPlats.map((rayon) => (
                  <option key={rayon.id} value={rayon.id}>
                    {rayon.nom}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <ZoneTexte
            etiquette="Description du produit"
            rows={3}
            placeholder="Riz jasmin importé de Thaïlande, sacs scellés d'origine."
            value={produit.description}
            onChange={(e) => setProduit({ ...produit, description: e.target.value })}
          />
        </Carte>

        <Carte className="space-y-4">
          <h2 className="font-bold">2. Votre offre</h2>
          <Champ
            etiquette="Titre de l'offre (facultatif)"
            placeholder="Riz Délice 25 kg — arrivage de novembre"
            value={offre.titre}
            onChange={(e) => setOffre({ ...offre, titre: e.target.value })}
            aide="Sans titre, c'est le nom du produit qui s'affiche."
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Champ
              etiquette="Prix unitaire"
              type="number"
              inputMode="numeric"
              min={1}
              required
              prefixe="FCFA"
              value={offre.prix_unitaire}
              onChange={(e) => setOffre({ ...offre, prix_unitaire: e.target.value })}
              erreur={creation.erreur?.pourChamp("prix_unitaire")}
            />
            <Champ
              etiquette="Minimum de pièces"
              type="number"
              inputMode="numeric"
              min={1}
              required
              value={offre.quantite_minimale}
              onChange={(e) => setOffre({ ...offre, quantite_minimale: e.target.value })}
              erreur={creation.erreur?.pourChamp("quantite_minimale")}
              aide="En dessous, tout le monde est remboursé."
            />
          </div>

          {prix > 0 && minimum > 0 && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="surface-douce rounded-xl px-3 py-2 text-sm"
            >
              Objectif de collecte :{" "}
              <strong className="text-[color:var(--color-accent)]">
                {francs(prix * minimum)}
              </strong>{" "}
              — vous en recevriez {francs(Math.max(0, prix * minimum - 1500))} après frais.
            </motion.p>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <Champ
              etiquette="Maximum de pièces (facultatif)"
              type="number"
              inputMode="numeric"
              min={1}
              value={offre.quantite_maximale}
              onChange={(e) => setOffre({ ...offre, quantite_maximale: e.target.value })}
              erreur={creation.erreur?.pourChamp("quantite_maximale")}
            />
            <Champ
              etiquette="Date limite"
              type="datetime-local"
              required
              value={offre.date_limite}
              onChange={(e) => setOffre({ ...offre, date_limite: e.target.value })}
              erreur={creation.erreur?.pourChamp("date_limite")}
            />
          </div>

          <Champ
            etiquette="Point de remise"
            placeholder="Marché d'Adawlato, Lomé"
            required
            value={offre.point_remise}
            onChange={(e) => setOffre({ ...offre, point_remise: e.target.value })}
            erreur={creation.erreur?.pourChamp("point_remise")}
          />

          <ZoneTexte
            etiquette="Conditions de l'offre"
            rows={2}
            placeholder="Provenance, état, garantie, modalités de remise."
            value={offre.description}
            onChange={(e) => setOffre({ ...offre, description: e.target.value })}
          />
        </Carte>

        <Carte className="space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="flex items-center gap-2 font-bold">
                <TrendingDown className="size-4 text-[color:var(--color-accent)]" />
                3. Paliers dégressifs (facultatif)
              </h2>
              <p className="texte-doux text-sm">
                Plus il y a de participants, moins chacun paie. C'est l'argument
                qui fait venir du monde.
              </p>
            </div>
            <Bouton
              type="button"
              ton="contour"
              taille="sm"
              icone={<Plus className="size-4" />}
              onClick={() =>
                setPaliers([...paliers, { quantite_min: "", prix_unitaire: "" }])
              }
            >
              Ajouter
            </Bouton>
          </div>

          {paliers.map((palier, rang) => (
            <motion.div
              key={rang}
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-end gap-2"
            >
              <input
                type="number"
                min={1}
                placeholder="À partir de"
                value={palier.quantite_min}
                onChange={(evenement) =>
                  setPaliers(
                    paliers.map((item, index) =>
                      index === rang
                        ? { ...item, quantite_min: evenement.target.value }
                        : item,
                    ),
                  )
                }
                className="surface h-12 flex-1 rounded-2xl px-4 text-sm outline-none focus:border-[color:var(--color-accent)]"
                aria-label={`Seuil du palier ${rang + 1}`}
              />
              <input
                type="number"
                min={1}
                placeholder="Prix FCFA"
                value={palier.prix_unitaire}
                onChange={(evenement) =>
                  setPaliers(
                    paliers.map((item, index) =>
                      index === rang
                        ? { ...item, prix_unitaire: evenement.target.value }
                        : item,
                    ),
                  )
                }
                className={fusionner(
                  "surface h-12 flex-1 rounded-2xl px-4 text-sm outline-none focus:border-[color:var(--color-accent)]",
                  prix > 0 &&
                    Number(palier.prix_unitaire) >= prix &&
                    "border-red-500",
                )}
                aria-label={`Prix du palier ${rang + 1}`}
              />
              <button
                type="button"
                onClick={() => setPaliers(paliers.filter((_, index) => index !== rang))}
                className="texte-doux grid size-12 shrink-0 place-items-center rounded-2xl transition-colors hover:text-red-600"
                aria-label="Supprimer ce palier"
              >
                <Trash2 className="size-4" />
              </button>
            </motion.div>
          ))}

          {paliers.length > 0 && (
            <p className="texte-doux text-xs">
              Un palier doit être <strong>moins cher</strong> que le prix affiché,
              sinon le prix monterait avec le nombre de participants.
            </p>
          )}
        </Carte>

        <Alerte>{creation.erreur?.message}</Alerte>

        <Bouton type="submit" pleineLargeur taille="lg" chargement={creation.envoi}>
          Créer la campagne
        </Bouton>
      </form>
    </div>
  );
}

/** Valeur par défaut du champ date, au format attendu par `datetime-local`. */
function dansJours(nombre: number): string {
  const date = new Date();
  date.setDate(date.getDate() + nombre);
  date.setHours(18, 0, 0, 0);
  const decale = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return decale.toISOString().slice(0, 16);
}
