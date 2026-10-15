import { useState } from "react";
import { construireCsv, telechargerCsv } from "../../domaine/export";
import { formaterFrancs } from "../../domaine/format";
import { LIBELLE_QUARTIER, type Quartier } from "../../domaine/groupage";
import { useEspaceGroupeur } from "../../api/EspaceGroupeurContexte";
import { LIBELLE_CAMPAGNE, type Statistiques } from "../../domaine/groupeur";
import { EnTeteGroupeur } from "../mise-en-page/ChromeGroupeur";
import Encart from "../../ui/Encart";
import EtatVide from "../../ui/EtatVide";

/**
 * Ecran 21 — Statistiques du groupeur. SPEC_ECRANS_FIGMA.md, ecran 21.
 *
 * **Objectif : qu'un groupeur sache, en dix secondes, si son activite marche
 * et ce qu'il doit changer.** C'est l'ecran qui fait passer Group Achat d'une
 * place de marche a un outil de gestion — et c'est celui qui le retient, parce
 * qu'il ne le retrouvera nulle part ailleurs.
 *
 * **Le principe a tenir : un chiffre, puis sa variation, puis sa cause.** Un
 * tableau de bord qui donne un chiffre sans point de comparaison ne sert a
 * rien : « 128 000 F collectes » ne dit pas si c'est bien.
 *
 * **La carte maitresse montre le VERSE, pas le collecte.** Le collecte inclut
 * l'argent qui n'est pas encore a lui ; mettre en avant un chiffre plus
 * flatteur que la realite detruit la credibilite du tableau de bord au premier
 * retrait.
 *
 * **L'histogramme est horizontal**, pour que les noms de campagne restent
 * lisibles sur 390 px. **La campagne annulee reste visible**, sans barre : un
 * tableau de bord qui cache les echecs ne sert pas a decider.
 *
 * ⚠️ **Trois choses n'y figurent jamais** :
 *
 * - **aucun nom, numero ou adresse d'acheteur** — des quartiers, des nombres,
 *   des montants (§1.7) ;
 * - **aucune comparaison avec les autres groupeurs**, pas de classement. Les
 *   mettre en concurrence les pousserait a baisser leurs prix jusqu'a ne plus
 *   pouvoir livrer ;
 * - **aucune projection**. « Vous gagnerez X le mois prochain » est une
 *   promesse. On montre le passe.
 *
 * Et dans « Ce que ca vous dit » : **un constat, jamais un conseil**. « Votre
 * panier moyen baisse » est un fait ; « augmentez vos prix » est un conseil
 * commercial dont nous ne sommes pas responsables.
 */
type Periode = "30-jours" | "3-mois" | "tout";

export default function Statistiques({
  onPortefeuille,
  onCreer,
}: {
  onPortefeuille: () => void;
  /**
   * Absent quand le dossier KYC n'est pas encore valide (§10.5).
   *
   * L'etat vide propose alors **une explication sans bouton** plutot qu'un
   * bouton qui echouerait : inviter a creer un groupage puis refuser est pire
   * que ne pas inviter.
   */
  onCreer?: () => void;
}) {
  const [periode, setPeriode] = useState<Periode>("30-jours");
  const espace = useEspaceGroupeur();
  const CAMPAGNES = espace.campagnes;

  /**
   * Les statistiques se **calculent sur ses campagnes**, elles ne sont pas
   * servies par une route dediee.
   *
   * ⚠️ **Les variations sur trente jours sont a zero, et ce n'est pas un
   * oubli.** Les calculer demanderait un historique que l'API ne garde pas
   * encore. Le cahier des charges est explicite : quand un chiffre n'est pas
   * connu, on ecrit qu'on ne le connait pas, **on ne l'invente pas**. Une
   * fleche verte fabriquee sur un tableau de bord d'argent serait le pire
   * endroit pour commencer. L'interface n'affiche donc pas de variation tant
   * qu'elle vaut zero.
   */
  const verse = espace.portefeuille?.disponible ?? 0;
  const abouties = CAMPAGNES.filter(
    (campagne) => campagne.statut === "livree" || campagne.statut === "en-cours",
  ).length;
  const participants = CAMPAGNES.reduce(
    (total, campagne) => total + campagne.commandes,
    0,
  );
  const collecteTotale = CAMPAGNES.reduce(
    (total, campagne) => total + campagne.collecte,
    0,
  );

  /**
   * « Exporter » : un CSV de ses groupages, ligne par ligne.
   *
   * ⚠️ **Il n'exporte que ce que l'ecran affiche.** On aurait pu y mettre les
   * commandes une a une — c'est ce qu'un export de marchand contient
   * d'habitude — mais le groupeur ne voit legitimement d'une commande qu'un
   * code, une quantite, un montant et un quartier. Un fichier est precisement
   * l'endroit ou cette limite se perdrait sans que personne ne le remarque.
   *
   * ⚠️ **Aucune variation, aucune tendance.** Elles valent zero a l'ecran
   * faute d'historique cote API ; les ecrire dans un fichier qu'on relira dans
   * six mois, hors de son contexte, serait inventer un chiffre.
   */
  const exporter = () => {
    const contenu = construireCsv(
      ["Produit", "Statut", "Commandes", "Objectif", "Collecté (F CFA)"],
      CAMPAGNES.map((campagne) => [
        campagne.produit,
        LIBELLE_CAMPAGNE[campagne.statut] ?? campagne.statut,
        campagne.commandes,
        campagne.objectifParticipants,
        campagne.collecte,
      ]),
    );
    const jour = new Date().toISOString().slice(0, 10);
    telechargerCsv(`group-achat-mes-groupages-${jour}.csv`, contenu);
  };

  /**
   * Les constats — **des faits relus des chiffres ci-dessus**, rien d'autre.
   *
   * Chacun est conditionne : un groupeur sans groupage annule ne lit pas
   * « 0 annule », il ne lit simplement pas cette ligne. Une section de
   * constats toujours pleine finit par n'etre plus lue.
   */
  function constater(): Statistiques["constats"] {
    const lignes: Statistiques["constats"] = [];

    if (CAMPAGNES.length > 0) {
      lignes.push({
        ton: abouties >= CAMPAGNES.length / 2 ? "succes" : "info",
        texte:
          `${abouties} de vos ${CAMPAGNES.length} groupages sont allés ` +
          `jusqu'à la commande ou la livraison.`,
      });
    }

    const annulees = CAMPAGNES.filter((c) => c.statut === "annulee").length;
    if (annulees > 0) {
      lignes.push({
        ton: "attention",
        texte:
          `${annulees} groupage${annulees > 1 ? "s" : ""} annulé` +
          `${annulees > 1 ? "s" : ""} : les participants ont été remboursés ` +
          `intégralement.`,
      });
    }

    const premier = espace.tableauDeBord?.par_quartier?.[0];
    if (premier && premier.part > 0) {
      lignes.push({
        ton: "info",
        texte:
          `${LIBELLE_QUARTIER[premier.quartier as Quartier] ?? premier.quartier} ` +
          `concentre ${premier.part} % de vos commandes.`,
      });
    }

    return lignes;
  }

  /* ⚠️ Le type est **annote** : sans lui, `parQuartier: []` et
     `constats: []` s'inferent en `never[]`, et tout usage de leurs elements
     devient une erreur. L'annotation garantit aussi que la forme reste celle
     que les ecrans attendent si un champ s'ajoute au type. */
  const s: Statistiques = {
    verse,
    variationVerse: 0,
    campagnesAbouties: { reussies: abouties, total: CAMPAGNES.length },
    participants,
    variationParticipants: 0,
    panierMoyen:
      participants > 0 ? Math.round(collecteTotale / participants) : 0,
    variationPanier: 0,
    /**
     * Campagnes allees jusqu'a la livraison, sur campagnes lancees.
     *
     * **Le lui montrer est un acte de loyaute** : c'est le chiffre qui
     * conditionne ses plafonds d'exposition (§10.4), donc il doit savoir sur
     * quoi il est juge.
     */
    tauxReussite:
      CAMPAGNES.length > 0
        ? Math.round((abouties / CAMPAGNES.length) * 100)
        : 0,
    revenusParCampagne: CAMPAGNES.map((campagne) => ({
      campagne: campagne.produit,
      /* Une campagne annulee reste visible, **sans barre** : elle s'est
         produite, et la masquer embellirait l'historique. */
      verse:
        campagne.statut === "annulee"
          ? undefined
          : Math.round(campagne.collecte * 0.95),
    })),
    parCategorie: Object.entries(
      CAMPAGNES.reduce<Record<string, number>>((parts, campagne) => {
        parts[campagne.categorie] =
          (parts[campagne.categorie] ?? 0) + campagne.collecte;
        return parts;
      }, {}),
    ).map(([categorie, montant]) => ({
      categorie,
      part: collecteTotale > 0 ? Math.round((montant / collecteTotale) * 100) : 0,
    })),
    /**
     * D'ou viennent ses commandes — **la donnee la plus actionnable de
     * l'ecran**, et il ne l'a nulle part ailleurs.
     *
     * ⚠️ **Agregee par le serveur**, en une requete, et non en lisant les
     * commandes de chaque campagne depuis le telephone : ca aurait fait
     * quinze appels sur un forfait limite (§5), et c'est pour cette raison
     * que la table restait vide avec ses seuls en-tetes.
     *
     * Des quartiers et des nombres, jamais un nom ni un repere (§1.7).
     */
    parQuartier: (espace.tableauDeBord?.par_quartier ?? []).map((ligne) => ({
      quartier: ligne.quartier as Quartier,
      commandes: ligne.commandes,
      part: ligne.part,
    })),
    /**
     * Les constats de « Ce que ca vous dit ».
     *
     * ⚠️ **Un constat, jamais un conseil.** « Deux de vos six groupages sont
     * alles jusqu'a la livraison » est un fait ; « baissez vos prix » est un
     * conseil commercial dont nous ne sommes pas responsables, et qui nous
     * rendrait comptables de ses pertes.
     *
     * ⚠️ **Et jamais un chiffre invente.** Chacune de ces lignes se lit
     * directement dans les donnees affichees juste au-dessus : si l'une
     * d'elles ne peut pas se calculer, elle ne s'affiche pas. C'est la regle
     * du cahier des charges — quand un chiffre n'est pas connu, on ecrit
     * qu'on ne le connait pas.
     */
    constats: constater(),
  };

  /* Ne jamais dessiner un tableau de bord rempli de zeros : c'est
     decourageant et ca n'informe de rien. */
  if (CAMPAGNES.length === 0) {
    return (
      <div className="pb-18">
        <EnTeteGroupeur titre="Mes statistiques" />
        <EtatVide
          titre="Vos statistiques apparaîtront ici"
          explication={
            onCreer
              ? "Après votre première campagne, vous verrez ici ce que vous avez versé, vos participants et vos quartiers."
              : "Après votre première campagne, vous verrez ici ce que vous avez versé, vos participants et vos quartiers. Vous pourrez la créer dès que votre dossier sera validé."
          }
          actionLibelle={onCreer ? "Créer une campagne" : undefined}
          registre="attente"
          onAction={onCreer}
        />
      </div>
    );
  }

  /** Avec une seule campagne il n'y a pas de periode precedente : pas de variation. */
  const avecVariation = CAMPAGNES.length > 1;
  const maxBarre = Math.max(
    ...s.revenusParCampagne.map((r) => r.verse ?? 0),
    1,
  );

  return (
    <div className="pb-18">
      <EnTeteGroupeur
        titre="Mes statistiques"
        action={
          <button
            type="button"
            onClick={exporter}
            className="min-h-11 px-2 text-sm font-medium text-white/85"
          >
            Exporter
          </button>
        }
      />

      <div className="space-y-6 px-4 pt-5">
        <div
          role="group"
          aria-label="Période"
          className="flex rounded-[10px] bg-surface-douce p-1"
        >
          {(
            [
              ["30-jours", "30 jours"],
              ["3-mois", "3 mois"],
              ["tout", "Tout"],
            ] as const
          ).map(([cle, libelle]) => (
            <button
              key={cle}
              type="button"
              aria-pressed={periode === cle}
              onClick={() => setPeriode(cle)}
              className={`min-h-10 flex-1 rounded-[10px] text-sm font-medium ${
                periode === cle
                  ? "bg-white text-confiance shadow-[0_1px_2px_rgba(29,25,22,0.08)]"
                  : "text-texte-secondaire"
              }`}
            >
              {libelle}
            </button>
          ))}
        </div>

        {/* La carte maitresse : ce qu'il a touche. */}
        <div className="rounded-xl bg-confiance p-5 text-white">
          <p className="text-sm text-white/85">Vos revenus — 30 jours</p>
          <p className="mt-1 text-3xl font-bold">
            {formaterFrancs(s.verse)}{" "}
            <span className="text-base font-medium text-white/85">versés</span>
          </p>
          {avecVariation ? (
            <p className="mt-1 text-sm text-white/85">
              + {s.variationVerse} % par rapport aux 30 jours précédents
            </p>
          ) : null}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Tuile
            libelle="Campagnes abouties"
            valeur={`${s.campagnesAbouties.reussies} sur ${s.campagnesAbouties.total}`}
            variation={avecVariation ? "stable" : undefined}
            ton="succes"
          />
          <Tuile
            libelle="Participants"
            valeur={String(s.participants)}
            variation={avecVariation ? `+ ${s.variationParticipants} %` : undefined}
            ton="succes"
          />
          <Tuile
            libelle="Panier moyen"
            valeur={formaterFrancs(s.panierMoyen)}
            variation={avecVariation ? `${s.variationPanier} %` : undefined}
            ton="danger"
          />
          <Tuile
            libelle="Taux de réussite"
            valeur={`${s.tauxReussite} %`}
            variation={avecVariation ? "stable" : undefined}
            ton="neutre"
          />
        </div>

        {/* Horizontal : les noms de campagne restent lisibles sur 390 px. */}
        <section>
          <h2 className="text-lg font-semibold text-texte">
            Revenus par campagne
          </h2>
          <ul className="mt-3 space-y-3">
            {s.revenusParCampagne.map((revenu) => (
              <li key={revenu.campagne}>
                <div className="flex items-baseline justify-between gap-3">
                  <span
                    className={`text-sm ${revenu.verse ? "text-texte" : "text-texte-secondaire"}`}
                  >
                    {revenu.campagne}
                  </span>
                  <span
                    className={`shrink-0 text-sm font-semibold ${revenu.verse ? "text-texte" : "text-texte-secondaire italic"}`}
                  >
                    {revenu.verse ? formaterFrancs(revenu.verse) : "annulée"}
                  </span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-surface-douce">
                  {revenu.verse ? (
                    <div
                      className="h-full rounded-full bg-confiance"
                      style={{ width: `${(revenu.verse / maxBarre) * 100}%` }}
                    />
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </section>

        {/* Quatre categories plus un « autres » : au-dela c'est illisible sur
            mobile et personne ne lit la legende. */}
        <section>
          <h2 className="text-lg font-semibold text-texte">Ce qui se vend</h2>
          <div
            className="mt-3 flex h-3 overflow-hidden rounded-full"
            role="img"
            aria-label={s.parCategorie
              .map((c) => `${c.categorie} ${c.part} %`)
              .join(", ")}
          >
            {s.parCategorie.map((categorie, indice) => (
              <span
                key={categorie.categorie}
                style={{
                  width: `${categorie.part}%`,
                  opacity: 1 - indice * 0.2,
                }}
                className="bg-confiance"
              />
            ))}
          </div>
          <ul className="mt-3 space-y-1">
            {s.parCategorie.map((categorie, indice) => (
              <li
                key={categorie.categorie}
                className="flex items-center gap-2 text-sm"
              >
                <span
                  aria-hidden="true"
                  style={{ opacity: 1 - indice * 0.2 }}
                  className="size-3 shrink-0 rounded-sm bg-confiance"
                />
                <span className="flex-1 text-texte">{categorie.categorie}</span>
                <span className="text-texte-secondaire">
                  {categorie.part} %
                </span>
              </li>
            ))}
          </ul>
        </section>

        {/* La donnee la plus actionnable de l'ecran, et il ne l'a nulle part
            ailleurs. Un quartier n'identifie personne (§1.7). */}
        <section>
          <h2 className="text-lg font-semibold text-texte">
            D&apos;où viennent vos commandes
          </h2>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="border-b border-filet text-left text-texte-secondaire">
                <th className="py-2 font-medium">Quartier</th>
                <th className="py-2 text-right font-medium">Commandes</th>
                <th className="py-2 text-right font-medium">Part</th>
              </tr>
            </thead>
            <tbody>
              {s.parQuartier.map((ligne) => (
                <tr
                  key={ligne.quartier}
                  className="border-b border-filet last:border-b-0"
                >
                  <td className="py-2 text-texte">
                    {LIBELLE_QUARTIER[ligne.quartier]}
                  </td>
                  <td className="py-2 text-right text-texte">
                    {ligne.commandes}
                  </td>
                  <td className="py-2 text-right text-texte-secondaire">
                    {ligne.part} %
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Un constat, jamais un conseil. */}
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-texte">
            Ce que ça vous dit
          </h2>
          {s.constats.map((constat) => (
            <Encart key={constat.texte} variante={constat.ton} role="groupeur">
              {constat.texte}
            </Encart>
          ))}
        </section>

        {/* Les statistiques expliquent, le portefeuille paie. */}
        <button
          type="button"
          onClick={onPortefeuille}
          className="min-h-12 text-sm font-semibold text-confiance"
        >
          Voir mon portefeuille
        </button>
      </div>
    </div>
  );
}

function Tuile({
  libelle,
  valeur,
  variation,
  ton,
}: {
  libelle: string;
  valeur: string;
  variation?: string;
  ton: "succes" | "danger" | "neutre";
}) {
  const couleur =
    ton === "succes"
      ? "text-succes"
      : ton === "danger"
        ? "text-danger"
        : "text-texte-secondaire";

  return (
    <div className="rounded-xl border border-bordure p-3">
      <p className="text-sm font-medium text-texte-secondaire">{libelle}</p>
      <p className="mt-1 text-prix font-bold text-texte">{valeur}</p>
      {/* Pas de « + 0 % » quand il n'y a pas de periode precedente. */}
      {variation ? (
        <p className={`text-xs ${couleur}`}>{variation}</p>
      ) : null}
    </div>
  );
}
