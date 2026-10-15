import { useState } from "react";
import {
  type GroupageAdmin,
  listerLesGroupages,
} from "../../api/administration";
import { useRequete } from "../../api/useRequete";
import { formaterFrancs } from "../../domaine/format";
import { COULEUR_STATUT } from "../../ui/Graphique";
import { ErreurReseau, ListeEnChargement } from "../../ui/EtatReseau";

/**
 * Tous les groupages, et surtout **ceux qui se sont terminés**.
 *
 * C'est l'écran où l'on voit ce que les autres cachent : les groupages
 * **annulés** par leur groupeur, ceux qui **n'ont pas abouti**, et ceux qui
 * sont allés jusqu'à la livraison. Trois choses différentes qu'on confond
 * facilement, et dont la distinction est tout l'intérêt de la page :
 *
 * | État | Ce que ça veut dire |
 * |---|---|
 * | **Ouverte** | Les acheteurs peuvent encore rejoindre |
 * | **Commande en cours** | Clôturée, le groupeur achète — c'est là qu'on attend le reçu |
 * | **Livrée** | Allée au bout. **C'est le seul chiffre qui compte vraiment** |
 * | **Annulée** | Le groupeur a renoncé, tout le monde est remboursé |
 *
 * ⚠️ **Le taux d'aboutissement conditionne les plafonds** (§10.4). Montrer ces
 * états n'est donc pas de la curiosité : c'est la matière des décisions qu'on
 * prendra sur chaque groupeur.
 */

const ETATS = [
  { cle: "", libelle: "Tous" },
  { cle: "ouverte", libelle: "Ouverts" },
  { cle: "en-cours", libelle: "Clôturés" },
  { cle: "livree", libelle: "Livrés" },
  { cle: "annulee", libelle: "Annulés" },
] as const;

const LIBELLE_STATUT: Record<string, string> = {
  ouverte: "Ouverte",
  "a-decider": "À décider",
  "en-cours": "Commande en cours",
  livree: "Livrée",
  annulee: "Annulée",
};

export default function Groupages({
  jeton,
  onJetonRefuse,
}: {
  jeton: string;
  onJetonRefuse: () => void;
}) {
  const [filtre, setFiltre] = useState<string>("");

  const requete = useRequete(
    (signal) => listerLesGroupages(jeton, filtre || undefined, signal),
    [jeton, filtre],
  );

  if (requete.erreur?.statut === 403) {
    onJetonRefuse();
  }

  const groupages = requete.donnees ?? [];

  return (
    <div className="mx-auto max-w-[1100px] px-8 py-6">
      <header>
        <h1 className="text-2xl font-semibold text-texte">Groupages</h1>
        <p className="mt-1 text-texte-secondaire">
          Ce qui tourne, ce qui est allé au bout, et ce qui a échoué.
        </p>
      </header>

      <div className="mt-4 flex gap-2">
        {ETATS.map(({ cle, libelle }) => (
          <button
            key={cle || "tous"}
            type="button"
            onClick={() => setFiltre(cle)}
            aria-pressed={filtre === cle}
            className={`rounded-xl border px-4 py-2 text-sm font-medium ${
              filtre === cle
                ? "border-texte bg-texte text-white"
                : "border-bordure text-texte hover:border-texte-secondaire"
            }`}
          >
            {libelle}
          </button>
        ))}
      </div>

      {requete.chargement ? (
        <ListeEnChargement nombre={5} className="mt-4" />
      ) : requete.erreur ? (
        <ErreurReseau erreur={requete.erreur} onReessayer={requete.recharger} />
      ) : groupages.length === 0 ? (
        <p className="mt-6 rounded-xl border border-bordure bg-white p-8 text-center text-texte-secondaire">
          Aucun groupage dans cet état.
        </p>
      ) : (
        <div className="mt-4 overflow-hidden rounded-xl border border-bordure bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-filet text-left text-texte-secondaire">
                <th className="px-5 py-3 font-medium">Produit</th>
                <th className="px-5 py-3 font-medium">Groupeur</th>
                <th className="px-5 py-3 text-right font-medium">Acheteurs</th>
                <th className="px-5 py-3 text-right font-medium">Collecte</th>
                <th className="px-5 py-3 font-medium">État</th>
                <th className="px-5 py-3 font-medium">Virement</th>
              </tr>
            </thead>
            <tbody>
              {groupages.map((groupage) => (
                <Ligne key={groupage.id} groupage={groupage} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Ligne({ groupage }: { groupage: GroupageAdmin }) {
  return (
    <tr className="border-b border-filet last:border-b-0">
      <td className="px-5 py-3">
        <span className="font-medium text-texte">{groupage.titre}</span>
      </td>
      <td className="px-5 py-3 text-texte-secondaire">{groupage.groupeur}</td>
      {/* ⚠️ Pour un groupage annule, les deux colonnes disent **ce qui a ete
          rembourse**, pas « 0 ». C'est exactement ce qu'on vient chercher sur
          un echec : combien de personnes ont ete decues, et pour combien. */}
      <td className="px-5 py-3 text-right text-texte">
        {groupage.rembourses ? (
          <span className="text-danger">
            {groupage.rembourses.acheteurs} remboursé
            {groupage.rembourses.acheteurs > 1 ? "s" : ""}
          </span>
        ) : (
          groupage.acheteurs_confirmes
        )}
      </td>
      <td className="px-5 py-3 text-right font-medium text-texte">
        {groupage.rembourses ? (
          <span className="text-danger">
            {formaterFrancs(groupage.rembourses.montant)}
          </span>
        ) : (
          formaterFrancs(Number(groupage.collecte))
        )}
      </td>
      <td className="px-5 py-3">
        {/* ⚠️ La pastille **et** le mot. L'information ne repose jamais sur la
            seule couleur : une capture en noir et blanc doit rester lisible,
            et un daltonien aussi. */}
        <span className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className="size-2.5 shrink-0 rounded-full"
            style={{
              backgroundColor: COULEUR_STATUT[groupage.statut] ?? "#9AA3AF",
            }}
          />
          <span className="text-texte">
            {LIBELLE_STATUT[groupage.statut] ?? groupage.statut}
          </span>
        </span>
      </td>
      <td className="px-5 py-3 text-texte-secondaire">
        {groupage.retrait_etat === "retirable" ||
        groupage.retrait_etat === "demande" ? (
          <span className="font-semibold text-primaire-texte-sur-fond">
            à faire
          </span>
        ) : groupage.retrait_etat === "effectue" ? (
          "versé"
        ) : groupage.retrait_etat === "annule" ? (
          "annulé"
        ) : (
          "—"
        )}
      </td>
    </tr>
  );
}
