import { useState } from "react";
import {
  type EtatLivraison,
  type Livraison,
  MOTIFS_REFUS,
  memeCode,
} from "../../domaine/livreur";
import { TOTAL_TOURNEE, TOURNEE } from "../../donnees/tournee";
import Bouton from "../../ui/Bouton";
import Encart from "../../ui/Encart";
import FeuilleRemontante from "../../ui/FeuilleRemontante";
import { IconeCoche, IconeTelephone } from "../../ui/Icones";
import Logo from "../../ui/Logo";

/**
 * Ecran 22 — Tournee du livreur. SPEC_ECRANS_FIGMA.md, ecran 22.
 *
 * **Ce n'est pas un ecran de l'application.** C'est une **page web** que le
 * livreur ouvre depuis un lien recu, sans rien installer et sans compte : il
 * est un prestataire partenaire, pas un utilisateur de Group Achat (§6 du
 * cahier des charges). D'ou l'absence de `BarreNav` — c'est une page isolee.
 *
 * ⚠️ **C'est le seul endroit de tout le produit ou l'identite d'un acheteur
 * est visible** : nom, adresse, telephone. Et uniquement le jour de sa
 * livraison, depuis un lien qui ne couvre que la tournee du jour et expire le
 * soir. Une page qui liste des noms, des adresses et des numeros est une page
 * sensible — c'est a ce titre qu'elle se dessine, et pas comme un simple
 * formulaire.
 *
 * **Le montant paye n'y figure jamais.** Le livreur n'a pas a le connaitre, et
 * l'afficher creerait une tentation inutile.
 *
 * La preuve de livraison ne conditionne **aucun retrait** — le groupeur a
 * deja ete paye a la cloture (§10.1). Elle construit son historique de
 * fiabilite, qui determine son plafond d'exposition : c'est le seul levier qui
 * nous reste sur lui, et c'est ce qui justifie cet ecran.
 *
 * **Le bouton « Colis refuse » n'est pas un detail** : sans lui, un refus
 * ressemble a une livraison non faite, et le litige devient impossible a
 * instruire.
 */
export default function TourneeLivreur() {
  const [livraisons, setLivraisons] = useState<Livraison[]>([...TOURNEE]);
  const [saisies, setSaisies] = useState<Record<string, string>>({});
  const [erreurs, setErreurs] = useState<Record<string, string>>({});
  const [refusEnCours, setRefusEnCours] = useState<Livraison>();
  const [sansCodeEnCours, setSansCodeEnCours] = useState<Livraison>();

  const faites = livraisons.filter((l) => l.etat !== "a-livrer").length;
  const aLivrer = livraisons.filter((l) => l.etat === "a-livrer");
  const terminees = livraisons.filter((l) => l.etat !== "a-livrer");

  const changerEtat = (id: string, etat: EtatLivraison) =>
    setLivraisons((liste) =>
      liste.map((l) =>
        l.id === id
          ? {
              ...l,
              etat,
              heure: new Date().toLocaleTimeString("fr-FR", {
                hour: "2-digit",
                minute: "2-digit",
              }),
            }
          : l,
      ),
    );

  const valider = (livraison: Livraison) => {
    const saisi = saisies[livraison.id] ?? "";

    if (livraison.etat !== "a-livrer") {
      setErreurs({
        ...erreurs,
        [livraison.id]: `Cette livraison a déjà été validée à ${livraison.heure}.`,
      });
      return;
    }
    if (!memeCode(saisi, livraison.codeLivraison)) {
      setErreurs({
        ...erreurs,
        [livraison.id]: "Code incorrect. Vérifiez auprès du client.",
      });
      return;
    }
    setErreurs({ ...erreurs, [livraison.id]: "" });
    changerEtat(livraison.id, "livree");
  };

  return (
    /* Pensee pour 390 px puisqu'elle sera ouverte sur un telephone, mais
       centree sur un ecran plus large : le livreur peut aussi l'ouvrir sur un
       ordinateur du depot. */
    <div className="mx-auto min-h-dvh max-w-[430px] bg-white pb-10">
      {/* En-tete simple. Pas de navigation, pas de menu. */}
      <header className="border-b border-filet px-4 py-4">
        <div className="flex items-center justify-between gap-3">
          <Logo variante="couleur" disposition="cote" hauteur={24} />
          <span className="text-sm text-texte-secondaire">
            {new Date().toLocaleDateString("fr-FR", {
              day: "numeric",
              month: "long",
            })}
          </span>
        </div>
        <p className="mt-1 text-sm font-medium text-texte">Livraisons</p>
      </header>

      <div className="space-y-5 px-4 pt-5">
        <section>
          <p className="font-semibold text-texte">
            {faites} livrées sur {TOTAL_TOURNEE}
          </p>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-douce">
            <div
              className="h-full rounded-full bg-marque"
              style={{ width: `${(faites / TOTAL_TOURNEE) * 100}%` }}
            />
          </div>
        </section>

        {/* Les cartes validees passent en haut, repliees. */}
        {terminees.length > 0 ? (
          <ul className="space-y-2">
            {terminees.map((livraison) => (
              <li
                key={livraison.id}
                className="flex items-center gap-2 rounded-xl bg-succes-fond px-3 py-2.5 text-sm text-succes"
              >
                <IconeCoche taille={18} className="shrink-0" />
                <span className="min-w-0 flex-1 truncate">
                  {livraison.nom} —{" "}
                  {livraison.etat === "refusee"
                    ? "colis refusé"
                    : `livrée à ${livraison.heure}`}
                </span>
              </li>
            ))}
          </ul>
        ) : null}

        <ul className="space-y-4">
          {aLivrer.map((livraison) => (
            <li
              key={livraison.id}
              className="rounded-xl border border-bordure p-4"
            >
              {/* Le seul endroit du produit ou ces trois lignes coexistent. */}
              <p className="font-semibold text-texte">{livraison.nom}</p>
              <p className="mt-0.5 text-sm text-texte-secondaire">
                {livraison.adresse}
              </p>

              <a
                href={`tel:${livraison.telephone.replace(/\s/g, "")}`}
                className="mt-2 inline-flex min-h-12 items-center gap-2 text-sm font-semibold text-primaire"
              >
                <IconeTelephone taille={18} />
                {livraison.telephone}
              </a>

              <p className="mt-1 text-sm text-texte">{livraison.contenu}</p>

              <div className="mt-4">
                <label
                  htmlFor={`code-${livraison.id}`}
                  className="block text-sm font-medium text-texte"
                >
                  Code présenté par le client
                </label>
                <input
                  id={`code-${livraison.id}`}
                  value={saisies[livraison.id] ?? ""}
                  onChange={(e) =>
                    setSaisies({
                      ...saisies,
                      [livraison.id]: e.target.value.toUpperCase(),
                    })
                  }
                  placeholder="ABC-123"
                  autoCapitalize="characters"
                  autoComplete="off"
                  className={`mt-1.5 h-13 w-full rounded-[10px] border px-3 text-center text-xl font-bold tracking-[0.2em] text-texte uppercase outline-none ${
                    erreurs[livraison.id]
                      ? "border-danger bg-danger-fond"
                      : "border-bordure focus:border-2 focus:border-primaire"
                  }`}
                />
                {erreurs[livraison.id] ? (
                  <p className="mt-1 text-sm text-danger">
                    {erreurs[livraison.id]}
                  </p>
                ) : null}
              </div>

              <div className="mt-3 space-y-2">
                <Bouton onClick={() => valider(livraison)}>
                  Valider la livraison
                </Bouton>
                <Bouton
                  style="danger-texte"
                  onClick={() => setRefusEnCours(livraison)}
                >
                  Colis refusé
                </Bouton>
              </div>

              {/* La livraison est marquee confirmee sans code et signalee pour
                  controle, sans bloquer le groupeur (§11.1). */}
              <button
                type="button"
                onClick={() => setSansCodeEnCours(livraison)}
                className="mt-1 min-h-12 w-full text-sm text-texte-secondaire underline"
              >
                Le client n&apos;a pas son code
              </button>
            </li>
          ))}
        </ul>

        {/* La saisie reste possible hors reseau. */}
        <Encart variante="attention">
          Pas de connexion ? Vos validations seront envoyées dès le retour du
          réseau.
        </Encart>

        <p className="text-center text-xs text-texte-secondaire">
          Ce lien ne couvre que la tournée du jour et expire ce soir.
        </p>
      </div>

      {refusEnCours ? (
        <FeuilleRemontante
          titre="Colis refusé"
          onFermer={() => setRefusEnCours(undefined)}
        >
          <div className="mt-4 space-y-4">
            <h2 className="text-xl font-semibold text-texte">
              Pourquoi le colis est-il refusé ?
            </h2>
            <ul className="space-y-2">
              {MOTIFS_REFUS.map((motif) => (
                <li key={motif}>
                  <button
                    type="button"
                    className="min-h-12 w-full rounded-[10px] border border-bordure px-3 text-left text-sm text-texte"
                  >
                    {motif}
                  </button>
                </li>
              ))}
            </ul>
            <textarea
              rows={2}
              placeholder="Décrivez brièvement…"
              aria-label="Description"
              className="w-full resize-none rounded-[10px] border border-bordure px-3 py-2.5 text-sm outline-none focus:border-2 focus:border-primaire"
            />
            <Bouton
              style="danger-texte"
              onClick={() => {
                changerEtat(refusEnCours.id, "refusee");
                setRefusEnCours(undefined);
              }}
            >
              Enregistrer le refus
            </Bouton>
          </div>
        </FeuilleRemontante>
      ) : null}

      {sansCodeEnCours ? (
        <FeuilleRemontante
          titre="Livraison sans code"
          onFermer={() => setSansCodeEnCours(undefined)}
        >
          <div className="mt-4 space-y-4">
            <h2 className="text-xl font-semibold text-texte">
              Confirmer sans code
            </h2>
            <div className="rounded-xl bg-surface-douce p-3 text-sm">
              <p className="font-semibold text-texte">{sansCodeEnCours.nom}</p>
              <p className="text-texte-secondaire">
                {sansCodeEnCours.telephone}
              </p>
            </div>
            <Encart variante="attention">
              La livraison sera marquée « confirmée sans code » et signalée pour
              contrôle. Le groupeur n&apos;est pas bloqué.
            </Encart>
            <Bouton
              onClick={() => {
                changerEtat(sansCodeEnCours.id, "livree-sans-code");
                setSansCodeEnCours(undefined);
              }}
            >
              Confirmer sans code
            </Bouton>
          </div>
        </FeuilleRemontante>
      ) : null}
    </div>
  );
}
