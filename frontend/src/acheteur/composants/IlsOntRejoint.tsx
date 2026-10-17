import { LIBELLE_QUARTIER, type Quartier } from "../../domaine/groupage";
import { IconeGroupage } from "../../ui/Icones";

/**
 * « Ils ont déjà rejoint » — l'ambiance du marché, sur la fiche produit.
 *
 * ## Ce que ce bloc cherche à faire
 *
 * Une fiche produit de site marchand est une notice : une photo, un prix, un
 * bouton. Au marché, ce n'est pas ça qui décide — c'est de **voir les autres
 * prendre**. On s'approche d'un étal parce qu'il y a du monde autour, et on
 * prend sa part parce que d'autres l'ont prise.
 *
 * Ce bloc est cette foule, rendue en trois colonnes : un quartier, une
 * quantité, un délai.
 *
 * ## ⚠️ Pourquoi il n'y a aucun nom, et ce que ça change
 *
 * Le §1.7 interdit tout profil public et tout moyen de joindre quelqu'un. Un
 * nom ici — même un prénom, même une initiale — ouvrirait exactement la porte
 * que le produit referme partout ailleurs : on pourrait recouper les commandes
 * d'une même personne d'un groupage à l'autre.
 *
 * **Le quartier suffit à l'effet recherché**, et c'est déjà ce que le groupeur
 * voit de ses acheteurs. Tokoin compte des dizaines de milliers d'habitants :
 * « Tokoin · 2 parts » ne désigne personne.
 *
 * ## ⚠️ Ce n'est ni un avis ni une note
 *
 * Il n'y a rien à écrire, rien à modérer, rien à falsifier : **chaque ligne
 * est une commande payée**. C'est une preuve, pas un témoignage — et c'est ce
 * qui la rend plus convaincante qu'un système d'étoiles, qu'on sait tous
 * pouvoir s'acheter.
 *
 * ## ⚠️ Ce que ce bloc n'écrit jamais
 *
 * Ni « plus que N places », ni « il manque N personnes », ni compte à rebours
 * de rareté. La règle de l'objectif l'interdit, et pour une raison de fond :
 * **un groupage sous son objectif peut aboutir**, donc annoncer un manque
 * serait faux en plus d'être une pression. On montre ce qui s'est passé, pas
 * ce qui risque de ne pas arriver.
 */

export interface ParticipantRecent {
  quartier: string;
  quantite: number;
  /** Heures écoulées depuis la commande, servies par le serveur. */
  heures: number;
}

/**
 * « il y a 2 h », « hier », « il y a 3 jours ».
 *
 * Le serveur sert des heures et l'écran décide des mots : lui faire envoyer
 * une phrase toute faite empêcherait de l'abréger selon la place, et
 * dupliquerait une règle de langue dans le backend.
 */
function depuis(heures: number): string {
  if (heures < 1) return "à l'instant";
  if (heures < 24) return `il y a ${heures} h`;
  const jours = Math.floor(heures / 24);
  if (jours === 1) return "hier";
  return `il y a ${jours} jours`;
}

export default function IlsOntRejoint({
  participants,
  total,
}: {
  participants: ParticipantRecent[];
  /** Le nombre total d'acheteurs confirmés, pour la phrase d'en-tête. */
  total: number;
}) {
  if (participants.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-bordure p-4">
      <h2 className="flex items-center gap-2 font-semibold text-texte">
        <span className="text-primaire">
          <IconeGroupage taille={20} />
        </span>
        Ils ont déjà rejoint
      </h2>

      {/* ⚠️ **Un fait, pas une incitation.** « 27 personnes ont pris leur
          part » se vérifie ; « plus que 3 places » serait faux — un groupage
          sous son objectif aboutit quand même. */}
      <p className="mt-1 text-sm text-texte-secondaire">
        {total} personne{total > 1 ? "s" : ""} ont déjà pris leur part dans ce
        groupage.
      </p>

      <ul className="mt-3 divide-y divide-filet">
        {participants.map((participant, rang) => (
          /* La clé est l'indice : deux commandes du même quartier, de même
             quantité et à la même heure sont indiscernables **par
             construction** — c'est le but de l'anonymat — donc aucune
             combinaison de champs ne fait une clé stable. La liste ne se
             réordonne jamais, l'indice est donc sûr ici. */
          <li
            key={rang}
            className="flex items-baseline justify-between gap-3 py-2 first:pt-0 last:pb-0"
          >
            <span className="min-w-0 flex-1 truncate text-sm text-texte">
              Quelqu&apos;un à{" "}
              <strong className="font-semibold">
                {LIBELLE_QUARTIER[participant.quartier as Quartier] ??
                  participant.quartier}
              </strong>{" "}
              a pris{" "}
              <strong className="font-semibold">
                {participant.quantite} part
                {participant.quantite > 1 ? "s" : ""}
              </strong>
            </span>
            <span className="shrink-0 text-xs text-texte-mention">
              {depuis(participant.heures)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
