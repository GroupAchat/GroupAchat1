import { useState } from "react";
import {
  executerLeRetrait,
  listerLesRetraits,
  type RetraitAdmin,
} from "../../api/administration";
import { useAction, useRequete } from "../../api/useRequete";
import { formaterDateCourte, formaterFrancs } from "../../domaine/format";
import { ErreurReseau, ListeEnChargement } from "../../ui/EtatReseau";
import { IconeAlerte, IconeCoche } from "../../ui/Icones";

/**
 * Les retraits des groupeurs — §9 et §10.2.
 *
 * ## ⚠️ Cet écran n'est plus un écran de décision, c'en est un d'exécution
 *
 * Il s'appelait « Virements » et il portait le dernier contrôle du dispositif :
 * sans devis fournisseur, on refusait de libérer l'argent. **Ce contrôle n'existe
 * plus.** L'argent de l'acheteur est inscrit au portefeuille du groupeur dès son
 * paiement (§9 du cahier des charges) ; son solde est à lui, et le lui refuser
 * serait indéfendable. Le §9.1 dit franchement ce que cette perte nous coûte.
 *
 * Ce qui reste de notre côté est un seul geste, et il n'a pas d'alternative :
 * **faire le transfert qu'il a demandé.** Le bouton ne s'ouvre donc pas sur un
 * devis, il s'ouvre sur sa demande.
 *
 * ## Ce que l'administrateur regarde avant d'appuyer
 *
 * - **sur quel compte Mobile Money** — le nom réel et le numéro, côte à côte :
 *   on ne vire pas de l'argent à un pseudonyme ;
 * - **depuis combien de temps il attend** — un groupeur qui attend depuis cinq
 *   jours ne peut pas acheter la marchandise qu'il a vendue, et ce sont ses
 *   acheteurs qui attendront ensuite.
 *
 * Le devis reste affiché quand il existe, mais **à titre d'information** : il
 * constate chez qui le groupeur achète, il n'autorise rien.
 *
 * ⚠️ **Le montant n'est pas le chiffre qui doit faire agir**, l'ancienneté si.
 * D'où le tri : du plus ancien au plus récent, jamais du plus gros montant.
 *
 * ⚠️ **Aucun virement réel n'est émis.** Le paiement est simulé jusqu'à
 * l'agrément d'un agrégateur (§18.2) : exécuter note que l'argent doit partir,
 * et qui l'a fait. L'écran le dit plutôt que de laisser croire autre chose.
 */
export default function Retraits({
  jeton,
  onJetonRefuse,
}: {
  jeton: string;
  onJetonRefuse: () => void;
}) {
  const [filtre, setFiltre] = useState<
    "demande" | "retirable" | "effectue" | ""
  >("demande");

  const requete = useRequete(
    (signal) => listerLesRetraits(jeton, filtre || undefined, signal),
    [jeton, filtre],
  );

  const execution = useAction(async (id: number) => {
    const resultat = await executerLeRetrait(jeton, id, "Administration");
    requete.recharger();
    return resultat;
  });

  if (requete.erreur?.statut === 403) {
    onJetonRefuse();
  }

  const retraits = requete.donnees ?? [];
  const aExecuter = retraits.filter((retrait) => retrait.executable);
  const sansDevis = retraits.filter((retrait) => !retrait.devis);

  return (
    <div className="mx-auto max-w-[1100px] px-8 py-6">
      <header>
        <h1 className="text-2xl font-semibold text-texte">Retraits</h1>
        <p className="mt-1 text-texte-secondaire">
          Le solde du groupeur est à lui dès la clôture. Quand il le demande,
          nous faisons le transfert — 1 500 F retenus par groupage abouti.
        </p>
      </header>

      <div className="mt-4 flex gap-2">
        {(
          [
            ["demande", "À exécuter"],
            ["retirable", "Retirables, non demandés"],
            ["effectue", "Exécutés"],
            ["", "Tous"],
          ] as const
        ).map(([valeur, libelle]) => (
          <button
            key={valeur || "tous"}
            type="button"
            onClick={() => setFiltre(valeur)}
            aria-pressed={filtre === valeur}
            className={`rounded-xl border px-4 py-2 text-sm font-medium ${
              filtre === valeur
                ? "border-texte bg-texte text-white"
                : "border-bordure text-texte hover:border-texte-secondaire"
            }`}
          >
            {libelle}
          </button>
        ))}
      </div>

      {filtre === "demande" && retraits.length > 0 ? (
        <p className="mt-4 rounded-xl border border-bordure bg-white px-4 py-3 text-sm text-texte-secondaire">
          <strong className="font-semibold text-texte">
            {aExecuter.length} transfert{aExecuter.length > 1 ? "s" : ""} à
            faire
          </strong>
          {sansDevis.length > 0 ? (
            <>
              {" · "}
              {sansDevis.length} sans devis déposé — à relancer, mais le
              transfert part quand même
            </>
          ) : null}
        </p>
      ) : null}

      {execution.erreur ? (
        <p
          role="alert"
          className="mt-4 rounded-xl border border-danger bg-danger-fond px-4 py-3 text-sm text-danger"
        >
          {execution.erreur.estRefusDeSaisie
            ? Object.values(execution.erreur.champs)[0]?.[0]
            : execution.erreur.messageLisible}
        </p>
      ) : null}

      {requete.chargement ? (
        <ListeEnChargement nombre={3} className="mt-4" />
      ) : requete.erreur ? (
        <ErreurReseau erreur={requete.erreur} onReessayer={requete.recharger} />
      ) : retraits.length === 0 ? (
        <p className="mt-6 rounded-xl border border-bordure bg-white p-8 text-center text-texte-secondaire">
          Aucun retrait dans cet état. C&apos;est l&apos;état normal : traitez
          les transferts le jour où ils arrivent et cette liste reste vide.
        </p>
      ) : (
        <ul className="mt-4 space-y-3">
          {retraits.map((retrait) => (
            <li key={retrait.id}>
              <Ligne
                retrait={retrait}
                enCours={execution.enCours}
                onExecuter={() => execution.executer(retrait.id)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Ligne({
  retrait,
  enCours,
  onExecuter,
}: {
  retrait: RetraitAdmin;
  enCours: boolean;
  onExecuter: () => void;
}) {
  /* Au-delà de deux jours, le groupeur est bloqué pour acheter. C'est le seul
     seuil de cet écran, et il porte sur le temps, pas sur le montant.

     ⚠️ Le compteur part de **sa demande**, pas de la clôture : un solde
     retirable qu'il n'a pas réclamé ne fait attendre personne. */
  const enRetard = retrait.etat === "demande" && retrait.jours_d_attente > 2;

  return (
    <div
      className={`rounded-xl border bg-white p-5 ${
        enRetard ? "border-danger" : "border-bordure"
      }`}
    >
      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          <h2 className="font-semibold text-texte">{retrait.campagne_titre}</h2>
          <p className="mt-0.5 text-sm text-texte-secondaire">
            {/* Le pseudonyme **et** le nom réel : l'administration est le seul
                endroit où les deux se voient ensemble, et c'est nécessaire —
                on ne vire pas de l'argent à un pseudonyme. */}
            {retrait.groupeur} · {retrait.groupeur_nom} ·{" "}
            {retrait.groupeur_mobile_money}
          </p>
        </div>

        <div className="shrink-0 text-right">
          <p className="text-prix font-bold text-texte">
            {formaterFrancs(Number(retrait.net))}
          </p>
          <p className="text-xs text-texte-secondaire">
            {formaterFrancs(Number(retrait.collecte))} collectés −{" "}
            {formaterFrancs(Number(retrait.frais_plateforme))} de frais
          </p>
        </div>
      </div>

      {/* ⚠️ Les frais de livraison sont dits à part, et ils ne sont **jamais**
          touchés : ils vont au transporteur, ce n'est pas l'argent du
          groupeur. */}
      <p className="mt-2 text-xs text-texte-secondaire">
        + {formaterFrancs(Number(retrait.frais_livraison_collectes))} de frais
        de livraison collectés, destinés au transporteur
      </p>

      {retrait.devis ? (
        <div className="mt-4 rounded-[10px] bg-surface-douce px-3 py-2.5 text-sm">
          <p className="font-semibold text-texte">Devis fournisseur</p>
          <p className="mt-0.5 text-texte-secondaire">
            {retrait.devis.fournisseur} —{" "}
            {formaterFrancs(Number(retrait.devis.montant))}, déposé le{" "}
            {formaterDateCourte(retrait.devis.depose_le.slice(0, 10))}
          </p>
        </div>
      ) : retrait.etat !== "annule" ? (
        <p className="mt-4 flex items-start gap-2 rounded-[10px] bg-primaire-fond px-3 py-2.5 text-sm text-primaire-texte-sur-fond">
          <IconeAlerte taille={16} className="mt-0.5 shrink-0" />
          <span>
            <strong className="font-semibold">
              Le groupeur n&apos;a pas déposé son devis.
            </strong>{" "}
            Ça ne bloque plus le transfert — son solde est à lui (§9.1). À
            relancer, et à compter : c&apos;est une absence de reçu qui
            annulera son groupage, pas celle du devis.
          </span>
        </p>
      ) : null}

      {retrait.etat === "effectue" ? (
        <p className="mt-4 flex items-center gap-2 rounded-[10px] bg-succes-fond px-3 py-2 text-sm text-succes">
          <IconeCoche taille={16} />
          Transfert fait le{" "}
          {formaterDateCourte(retrait.libere_le?.slice(0, 10) ?? "")} par{" "}
          {retrait.libere_par}
        </p>
      ) : retrait.etat === "annule" ? (
        <p className="mt-4 rounded-[10px] bg-surface-douce px-3 py-2 text-sm text-texte-secondaire">
          Groupage annulé — aucun frais, rien n&apos;est parti.
        </p>
      ) : retrait.etat === "retirable" ? (
        <p className="mt-4 rounded-[10px] bg-surface-douce px-3 py-2.5 text-sm text-texte-secondaire">
          <strong className="font-semibold text-texte">
            Le groupeur n&apos;a pas encore demandé son retrait.
          </strong>{" "}
          Son solde l&apos;attend, et nous n&apos;avons rien à faire : exécuter
          un transfert qu&apos;il n&apos;a pas déclenché reviendrait à sortir
          son argent de la plateforme à sa place.
        </p>
      ) : (
        <>
          <div className="mt-4 flex items-center gap-3">
            <button
              type="button"
              disabled={enCours}
              onClick={onExecuter}
              className={`rounded-xl px-5 py-2.5 text-sm font-semibold ${
                enCours
                  ? "cursor-wait bg-surface-douce text-texte-secondaire"
                  : "bg-texte text-white hover:opacity-90"
              }`}
            >
              {enCours ? "…" : "Faire le transfert"}
            </button>
            <p
              className={`text-sm ${
                enRetard ? "font-semibold text-danger" : "text-texte-secondaire"
              }`}
            >
              {retrait.jours_d_attente === 0
                ? "demandé aujourd'hui"
                : `attend depuis ${retrait.jours_d_attente} jour${
                    retrait.jours_d_attente > 1 ? "s" : ""
                  }`}
            </p>
          </div>

          {/* Dit franchement ce que le bouton fait, et ne fait pas. */}
          <p className="mt-2 text-xs text-texte-secondaire">
            Aucun virement n&apos;est réellement émis : le paiement est simulé
            jusqu&apos;à l&apos;agrément d&apos;un agrégateur. Le bouton note
            que l&apos;argent doit partir, et qui l&apos;a fait.
          </p>
        </>
      )}
    </div>
  );
}
