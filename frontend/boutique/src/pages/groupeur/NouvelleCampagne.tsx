import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import type { Campagne, Categorie, Produit } from "@commun/api/types";
import {
  EnvoiMedias,
  envoiEnCours,
  mediasPrets,
  type MediaEnAttente,
} from "@/composants/EnvoiMedias";
import {
  Alerte,
  Bouton,
  Carte,
  Champ,
  ZoneTexte,
} from "@commun/composants/ui";
import { useSession } from "@commun/contexte/Session";
import { commissionSur, francs, tauxCommission } from "@commun/outils/formats";
import { api, useAction, useRequete } from "@commun/outils/requetes";

/**
 * Création d'une campagne, en deux temps : le produit, puis l'offre.
 *
 * Le produit est créé d'abord parce qu'il vit indépendamment de l'offre —
 * un autre OAG pourra proposer le même. Les deux écrans tiennent dans
 * une seule page : couper en assistant multi-pages ferait perdre la vue
 * d'ensemble sur un formulaire aussi court.
 */
export default function NouvelleCampagne() {
  const naviguer = useNavigate();
  const { utilisateur } = useSession();
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
  });
  const [medias, setMedias] = useState<MediaEnAttente[]>([]);
  const [contratAccepte, setContratAccepte] = useState(false);

  const creation = useAction(async () => {
    const fiche = await api.post<Produit>("/groupeur/produits/", {
      nom: produit.nom,
      marque: produit.marque,
      categorie: Number(produit.categorie),
      description: produit.description,
    });

    // Les fichiers sont déjà chez l'hébergeur : il ne reste qu'à les
    // rattacher. En série et non en parallèle, parce que le plafond de trois
    // photos se vérifie en comptant les lignes déjà posées — deux dépôts
    // simultanés compteraient le même état et passeraient tous les deux.
    for (const media of mediasPrets(medias)) {
      await api.post("/groupeur/medias/", { ...media, produit: fiche.id });
    }
    const campagne = await api.post<Campagne>("/groupeur/campagnes/", {
      produit: fiche.id,
      titre: offre.titre || fiche.nom,
      description: offre.description,
      prix_unitaire: Number(offre.prix_unitaire),
      quantite_minimale: Number(offre.quantite_minimale),
      quantite_maximale: offre.quantite_maximale ? Number(offre.quantite_maximale) : null,
      date_limite: new Date(offre.date_limite).toISOString(),
      paliers: [],
    });
    naviguer(`/groupeur/campagnes/${campagne.id}`);
    return campagne;
  });

  const prix = Number(offre.prix_unitaire) || 0;
  const minimum = Number(offre.quantite_minimale) || 0;
  const centiemes = utilisateur?.points.commission_centiemes ?? 350;

  return (
    <div className="w-full space-y-4 px-3.5 py-4 pb-24">
      <Link
        to="/groupeur/campagnes"
        className="texte-doux inline-flex items-center gap-1.5 text-xs font-semibold"
      >
        <ArrowLeft className="size-4" />
        Mes campagnes
      </Link>

      <header>
        <h1 className="text-xl font-extrabold text-slate-900">Nouvelle offre</h1>
        <p className="texte-doux text-xs">
          Elle démarre en brouillon : vous la publierez quand elle vous conviendra.
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
          <EnvoiMedias valeur={medias} surChangement={setMedias} />
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
              — vous en recevriez{" "}
              {francs(prix * minimum - commissionSur(prix * minimum, centiemes))} après
              commission ({tauxCommission(centiemes)}).
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

          {/* Pas de point de remise à saisir : ce n'est pas à l'OAG de
              décider où va le colis. Chaque acheteur choisit son bureau de
              poste ou se fait livrer, part par part. */}
          <p className="texte-doux surface-douce rounded-2xl p-3 text-xs">
            Vous n'avez pas de point de remise à indiquer : chaque acheteur
            choisit son bureau de poste ou la livraison à son adresse, et
            l'agence s'en charge. Les frais de livraison sont réglés à
            l'agence à la remise — ils ne passent pas par vous.
          </p>

          <ZoneTexte
            etiquette="Conditions de l'offre"
            rows={2}
            placeholder="Provenance, état, garantie, délais."
            value={offre.description}
            onChange={(e) => setOffre({ ...offre, description: e.target.value })}
          />
        </Carte>

        {/* Engagement contractuel Notarié et Charte de déontologie Togo */}
        <label className="flex items-start gap-3 rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4 text-xs dark:border-slate-800 dark:bg-slate-900/40 cursor-pointer">
          <input
            type="checkbox"
            required
            checked={contratAccepte}
            onChange={(e) => setContratAccepte(e.target.checked)}
            className="mt-0.5 size-4 rounded accent-[color:var(--color-accent)]"
          />
          <span className="leading-relaxed text-slate-700 dark:text-slate-300">
            <strong>Contrat OAG & Charte de Déontologie GROUP ACHAT TOGO</strong> :
            Je m'engage à honorer la fourniture de la marchandise et certifie accepter les conditions du contrat OAG validé par notaire au Togo. L'acceptation en ligne vaut signature électronique légale (Loi togolaise sur les transactions électroniques).
          </span>
        </label>

        <Alerte>{creation.erreur?.message}</Alerte>

        <Bouton
          type="submit"
          pleineLargeur
          taille="lg"
          chargement={creation.envoi}
          disabled={envoiEnCours(medias) || !contratAccepte}
        >
          {envoiEnCours(medias) ? "Envoi des photos…" : "Créer la campagne"}
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
