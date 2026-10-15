import { useState } from "react";
import { formaterDateCourte, formaterFrancs } from "../../domaine/format";
import { useEspaceGroupeur } from "../../api/EspaceGroupeurContexte";
import { retirerMesFonds } from "../../api/espaceGroupeur";
import { useAction } from "../../api/useRequete";
import { FRAIS_PLATEFORME } from "../../domaine/groupeur";
import { EnTeteGroupeur } from "../mise-en-page/ChromeGroupeur";
import Bouton from "../../ui/Bouton";
import Encart from "../../ui/Encart";
import FeuilleRemontante from "../../ui/FeuilleRemontante";
import { IconeEntree, IconeHorloge, IconeRecu } from "../../ui/Icones";

/**
 * Ecran 18 — Portefeuille groupeur. SPEC_ECRANS_FIGMA.md, ecran 18.
 *
 * **Objectif : montrer ou est l'argent et a quel titre.** C'est l'ecran qui
 * explique le modele economique sans un mot de pitch.
 *
 * **L'encart explicatif n'est pas facultatif.** Un groupeur qui decouvre la
 * retenue au moment de retirer se sent trompe. Elle est dite ici, a l'ecran 14
 * au moment de fixer le prix, et a l'ecran 16 au moment de decider : **trois
 * fois, et c'est volontaire**.
 *
 * La derniere ligne de l'historique — « Groupage annule, aucun frais » — vaut
 * d'etre montree : elle prouve ce que le §7 du cahier des charges annonce, au
 * lieu de le promettre.
 *
 * ## ⚠️ Le bouton « Retirer mes fonds » agit reellement
 *
 * Il etait inerte, et c'est desormais le geste central du modele : c'est lui
 * qui declenche la retenue des **1 500 F par groupage abouti** (§9.2). La
 * confirmation annonce donc le montant **et** les frais avant de partir — un
 * groupeur qui voit 1 500 F de moins arriver sans l'avoir lu se sent vole, et
 * il a raison.
 *
 * Le portefeuille dit *combien*, les statistiques disent *pourquoi*. **Deux
 * ecrans distincts, volontairement** : on ne melange pas l'analyse et le
 * mouvement d'argent.
 */
export default function Portefeuille({
  onStatistiques,
}: {
  onStatistiques: () => void;
}) {
  const { portefeuille, tableauDeBord, telephone, recharger } =
    useEspaceGroupeur();
  const [confirmation, setConfirmation] = useState(false);

  const retrait = useAction((numero: string) => retirerMesFonds(numero));

  const mouvements = portefeuille?.mouvements ?? [];
  const disponible = portefeuille?.disponible ?? 0;

  /**
   * Les frais se **somment depuis l'historique**, ils ne sont pas servis
   * séparément.
   *
   * C'est volontaire : un chiffre qu'on peut additionner soi-même à partir des
   * lignes affichées juste en dessous ne doit pas venir d'un autre calcul,
   * sinon le total et le détail peuvent se contredire à l'écran — et c'est le
   * détail qu'on croit, à juste titre.
   */
  const frais = -mouvements
    .filter((mouvement) => (mouvement.montant ?? 0) < 0)
    .reduce((total, mouvement) => total + (mouvement.montant ?? 0), 0);

  /** Combien de groupages ont abouti, d'après les lignes de frais. */
  const aboutis = mouvements.filter((m) => (m.montant ?? 0) < 0).length;

  const dernier = mouvements.find((mouvement) =>
    mouvement.libelle.startsWith("Retrait —"),
  );

  return (
    <div className="pb-18">
      <EnTeteGroupeur titre="Portefeuille" />

      <div className="space-y-6 px-4 pt-5">
        {/* La carte principale. Fond `confiance`, texte blanc (10,36:1). */}
        <div className="rounded-xl bg-confiance p-5 text-white">
          <p className="text-sm text-white/85">Disponible</p>
          <p className="mt-1 text-3xl font-bold">
            {formaterFrancs(disponible)}
          </p>
          {/* ⚠️ Desactive a zero, et pas masque : un bouton qui disparait
              laisse croire que la fonction n'existe pas. Il reste visible,
              avec sa raison juste en dessous. */}
          <button
            type="button"
            disabled={disponible === 0}
            onClick={() => setConfirmation(true)}
            className="mt-4 h-12 w-full rounded-[10px] bg-white font-semibold text-confiance disabled:opacity-50"
          >
            Retirer mes fonds
          </button>
          {disponible === 0 ? (
            <p className="mt-2 text-xs text-white/85">
              Rien à retirer : l&apos;argent de vos groupages ouverts est
              détenu jusqu&apos;à leur clôture.
            </p>
          ) : null}
        </div>

        <div className="space-y-3">
          <TuileMontant
            Icone={IconeHorloge}
            montant={tableauDeBord?.en_collecte ?? 0}
            libelle="En cours de collecte"
            /* ⚠️ « détenu jusqu'à la clôture », jamais « bloqué jusqu'à la
               livraison » (§1.7). Le groupeur est payé intégralement à la
               clôture : écrire autre chose serait faux, et ferait croire à une
               retenue qui n'existe pas. */
            detail="Détenu jusqu'à la clôture"
          />
          <TuileMontant
            Icone={IconeEntree}
            montant={portefeuille?.retire ?? 0}
            libelle="Retiré"
            detail={
              dernier
                ? `Dernier retrait : ${dernier.libelle.replace("Retrait — ", "")}`
                : "Aucun retrait pour l'instant"
            }
          />
          <TuileMontant
            /* ⚠️ **Plus l'icone de pourcentage** : il n'y a plus de
               pourcentage, et la garder aurait fait mentir l'ecran avant
               qu'on ait lu la ligne. */
            Icone={IconeRecu}
            montant={frais}
            libelle="Frais Group Achat"
            detail={`1 500 F par groupage abouti · ${aboutis} groupage${
              aboutis > 1 ? "s" : ""
            }`}
          />
        </div>

        {/* A ne pas omettre : c'est le troisieme et dernier rappel. */}
        <Encart variante="info" role="groupeur" titre="Comment ça marche">
          L&apos;argent de vos acheteurs est à vous dès leur paiement. Il est
          détenu jusqu&apos;à la clôture du groupage, puis vous pouvez le
          retirer en entier. Group Achat retient{" "}
          {formaterFrancs(FRAIS_PLATEFORME)} par groupage abouti, au moment du
          retrait. Aucun frais sur un groupage annulé. Les frais de livraison
          payés par vos acheteurs ne vous reviennent pas : ils vont au
          transporteur.
        </Encart>

        <section>
          <h2 className="text-lg font-semibold text-texte">Historique</h2>
          <ul className="mt-2">
            {mouvements.map((mouvement) => (
              <li
                key={mouvement.id}
                className="flex items-start justify-between gap-3 border-b border-filet py-3 last:border-b-0"
              >
                <div className="min-w-0">
                  <p className="text-sm text-texte">{mouvement.libelle}</p>
                  <p className="text-xs text-texte-secondaire">
                    {formaterDateCourte(mouvement.date)}
                  </p>
                </div>
                <span
                  className={`shrink-0 text-sm font-semibold ${
                    mouvement.montant === undefined
                      ? "text-texte-secondaire"
                      : mouvement.montant > 0
                        ? "text-succes"
                        : "text-texte"
                  }`}
                >
                  {mouvement.montant === undefined
                    ? (mouvement.mention ?? "—")
                    : `${mouvement.montant > 0 ? "+" : "−"} ${formaterFrancs(Math.abs(mouvement.montant))}`}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <button
          type="button"
          onClick={onStatistiques}
          className="min-h-12 text-sm font-semibold text-confiance"
        >
          Voir mes statistiques
        </button>

        <p className="pb-2 text-center text-xs text-texte-secondaire">
          Démonstration — aucun mouvement de fonds réel.
        </p>
      </div>

      {confirmation ? (
        <FeuilleRemontante
          titre="Retirer mes fonds"
          onFermer={() => setConfirmation(false)}
        >
          <div className="mt-4 space-y-4">
            <h2 className="text-xl font-semibold text-texte">
              Vous retirez {formaterFrancs(disponible)}
            </h2>
            {/* Les frais s'annoncent **avant** le geste, jamais apres. */}
            <p className="text-texte-secondaire">
              Group Achat retient {formaterFrancs(FRAIS_PLATEFORME)} par
              groupage abouti. Le montant ci-dessus est déjà net de ces frais.
            </p>
            <Bouton
              role="groupeur"
              chargement={retrait.enCours}
              onClick={async () => {
                const resultat = await retrait.executer(telephone);
                if (resultat) {
                  setConfirmation(false);
                  recharger();
                }
              }}
            >
              Je confirme le retrait
            </Bouton>
            {retrait.erreur ? (
              <p role="alert" className="text-sm font-medium text-danger">
                {retrait.erreur.messageLisible}
              </p>
            ) : null}
            <Bouton style="secondaire" onClick={() => setConfirmation(false)}>
              Annuler
            </Bouton>
          </div>
        </FeuilleRemontante>
      ) : null}
    </div>
  );
}

function TuileMontant({
  Icone,
  montant,
  libelle,
  detail,
}: {
  Icone: (p: { taille?: number; className?: string }) => React.ReactElement;
  montant: number;
  libelle: string;
  detail: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-bordure p-3">
      <Icone taille={20} className="mt-0.5 shrink-0 text-texte-secondaire" />
      <div className="min-w-0">
        <p className="text-lg font-bold text-texte">{formaterFrancs(montant)}</p>
        <p className="text-sm font-medium text-texte">{libelle}</p>
        <p className="text-xs text-texte-secondaire">{detail}</p>
      </div>
    </div>
  );
}
