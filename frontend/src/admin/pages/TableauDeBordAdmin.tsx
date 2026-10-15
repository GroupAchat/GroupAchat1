import {
  type AlerteAdmin,
  type FileAdmin,
  type IndicateurAdmin,
  lireLeTableauDeBordAdmin,
  type TableauDeBordAdmin as DonneesTableauDeBord,
} from "../../api/administration";
import { useRequete } from "../../api/useRequete";
import { formaterFrancs } from "../../domaine/format";
import { COULEUR_STATUT, Courbe, Repartition } from "../../ui/Graphique";
import { ErreurReseau, Squelette } from "../../ui/EtatReseau";
import { IconeAlerte, IconeCoche } from "../../ui/Icones";
import type { EcranAdmin } from "../mise-en-page/Sidebar";

/**
 * Écran A1 — Tableau de bord administrateur. SPEC_ECRANS_FIGMA.md, écran A1.
 *
 * **Chrome neutre, ni orange ni bleu** (§1.2) : les deux chromes de marque
 * appartiennent aux deux publics, l'outil interne n'en porte aucun. Cette
 * neutralité évite de confondre une capture d'écran interne avec le produit.
 *
 * ⚠️ **Mais la couleur n'a pas disparu pour autant — elle encode.** Une
 * pastille rouge sur une file dit qu'il y a de l'argent engagé ; une courbe
 * bleue dit la collecte. Ce que le chrome neutre interdit, c'est la couleur de
 * *marque* employée comme décor, pas la couleur employée comme information.
 * Chaque teinte de cet écran porte un chiffre écrit à côté d'elle : une
 * capture en noir et blanc reste lisible, et un daltonien aussi.
 *
 * ## L'ordre vertical, qui est tout le propos
 *
 * **Alertes → files de travail → chiffres → activité.** Un administrateur qui
 * ouvre cette page le matin a une question : qu'est-ce qui attend une
 * décision ? Pas « comment ça s'est passé ».
 *
 * L'activité est en dernier **parce que c'est le seul bloc qui regarde le
 * passé** : tout ce qui précède demande une action.
 *
 * ⚠️ **Trois absences voulues** :
 *
 * - **aucun bouton qui déplace de l'argent.** Depuis une vue d'ensemble on
 *   *va vers* un dossier ; on ne libère pas un virement sans l'avoir ouvert.
 *   Toute action sur l'argent est tracée et motivée (§18.3) ;
 * - **aucune donnée personnelle.** Des compteurs et des montants. Un nom
 *   n'apparaît qu'une fois le dossier ouvert ;
 * - **le nombre d'inscrits.** C'est la mesure qui flatte et n'engage à rien.
 *   Ce qui compte est le nombre de groupages allés jusqu'à la livraison, et
 *   c'est lui qui est affiché.
 */
export default function TableauDeBordAdmin({
  jeton,
  onNaviguer,
  onJetonRefuse,
}: {
  jeton: string;
  onNaviguer: (ecran: EcranAdmin) => void;
  onJetonRefuse: () => void;
}) {
  const requete = useRequete(
    (signal) => lireLeTableauDeBordAdmin(jeton, signal),
    [jeton],
  );

  if (requete.erreur?.statut === 403) {
    onJetonRefuse();
  }

  return (
    <div className="mx-auto max-w-[1100px] px-8 py-6">
      <header>
        <h1 className="text-2xl font-semibold text-texte">Tableau de bord</h1>
        <p className="mt-1 text-texte-secondaire">
          Ce qui attend une décision, d&apos;abord. Ce qui s&apos;est passé,
          ensuite.
        </p>
      </header>

      {requete.chargement ? (
        <EnChargement />
      ) : requete.erreur ? (
        <ErreurReseau erreur={requete.erreur} onReessayer={requete.recharger} />
      ) : requete.donnees ? (
        <Contenu donnees={requete.donnees} onNaviguer={onNaviguer} />
      ) : null}
    </div>
  );
}

function EnChargement() {
  return (
    <div className="mt-8 space-y-6" aria-busy="true">
      <div className="grid grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((indice) => (
          <div
            key={indice}
            className="space-y-2 rounded-xl border border-bordure bg-white p-5"
          >
            <Squelette largeur="60%" hauteur={13} />
            <Squelette largeur="80%" hauteur={24} />
          </div>
        ))}
      </div>
      <div className="rounded-xl border border-bordure bg-white p-5">
        <Squelette largeur="30%" hauteur={16} />
        <div className="mt-4">
          <Squelette largeur="100%" hauteur={120} />
        </div>
      </div>
    </div>
  );
}

function Contenu({
  donnees,
  onNaviguer,
}: {
  donnees: DonneesTableauDeBord;
  onNaviguer: (ecran: EcranAdmin) => void;
}) {
  return (
    <div className="mt-6 space-y-6">
      {/* 1 — Les alertes. Elles remontent toutes seules (§10.5). */}
      {donnees.alertes.length > 0 ? (
        <section>
          <h2 className="text-sm font-semibold text-danger">
            {donnees.alertes.length} alerte
            {donnees.alertes.length > 1 ? "s" : ""}
          </h2>
          <ul className="mt-2 space-y-2">
            {donnees.alertes.map((alerte) => (
              <li key={alerte.id}>
                <Alerte alerte={alerte} onNaviguer={onNaviguer} />
              </li>
            ))}
          </ul>
        </section>
      ) : (
        /* ⚠️ **La journée calme doit se dessiner aussi.** C'est l'état le plus
           fréquent, et celui qu'on oublie : un administrateur qui ouvre son
           écran tous les matins pour voir un mur rouge finit par ne plus
           l'ouvrir. */
        <p className="flex items-center gap-2 rounded-xl border border-bordure bg-white px-4 py-3 text-sm text-texte-secondaire">
          <IconeCoche taille={18} className="text-succes" />
          Aucune alerte. Rien d&apos;anormal sur le service.
        </p>
      )}

      {/* 2 — Les files de travail. */}
      <section>
        <h2 className="text-lg font-semibold text-texte">Files de travail</h2>
        <ul className="mt-3 grid grid-cols-3 gap-4">
          {donnees.files.map((file) => (
            <li key={file.id}>
              <TuileFile file={file} onNaviguer={onNaviguer} />
            </li>
          ))}
        </ul>
      </section>

      {/* 3 — Les chiffres et les courbes. */}
      <section className="grid grid-cols-2 gap-4">
        <div className="rounded-xl border border-bordure bg-white p-5">
          <h2 className="font-semibold text-texte">Collecte des 14 jours</h2>
          <p className="mt-0.5 text-sm text-texte-secondaire">
            {formaterFrancs(
              donnees.serie_collecte.reduce(
                (somme, point) => somme + point.montant,
                0,
              ),
            )}{" "}
            encaissés sur la période
          </p>
          <div className="mt-4">
            <Courbe
              points={donnees.serie_collecte}
              libelle="Collecte des quatorze derniers jours"
              couleur="#1E3A8A"
            />
          </div>
        </div>

        <div className="rounded-xl border border-bordure bg-white p-5">
          <h2 className="font-semibold text-texte">Où en sont les groupages</h2>
          <p className="mt-0.5 text-sm text-texte-secondaire">
            Tous états confondus, depuis le début
          </p>
          <div className="mt-4">
            <Repartition
              libelle="Répartition des groupages par état"
              parts={donnees.repartition_statuts.map((part) => ({
                libelle: part.libelle,
                nombre: part.nombre,
                couleur: COULEUR_STATUT[part.statut] ?? "#9AA3AF",
              }))}
            />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-texte">Indicateurs</h2>
        <ul className="mt-3 grid grid-cols-4 gap-4">
          {donnees.indicateurs.map((indicateur) => (
            <li key={indicateur.id}>
              <TuileIndicateur indicateur={indicateur} />
            </li>
          ))}
        </ul>
      </section>

      {/* 4 — L'activité. En dernier : elle ne demande rien. */}
      <section>
        <h2 className="text-lg font-semibold text-texte">Activité récente</h2>
        {donnees.activite.length === 0 ? (
          <p className="mt-2 text-sm text-texte-secondaire">
            Rien ne s&apos;est encore terminé.
          </p>
        ) : (
          <ul className="mt-3 overflow-hidden rounded-xl border border-bordure bg-white">
            {donnees.activite.map((ligne, indice) => (
              <li
                key={`${ligne.date}-${indice}`}
                className="flex items-center gap-4 border-b border-filet px-5 py-3 text-sm last:border-b-0"
              >
                <span className="w-24 shrink-0 text-texte-secondaire">
                  {ligne.date}
                </span>
                <span className="min-w-0 flex-1 text-texte">{ligne.texte}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Alerte({
  alerte,
  onNaviguer,
}: {
  alerte: AlerteAdmin;
  onNaviguer: (ecran: EcranAdmin) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onNaviguer(alerte.destination as EcranAdmin)}
      className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors hover:bg-white ${
        alerte.gravite === "danger"
          ? "border-danger bg-danger-fond"
          : "border-bordure bg-white"
      }`}
    >
      <IconeAlerte
        taille={18}
        className={
          alerte.gravite === "danger" ? "text-danger" : "text-texte-secondaire"
        }
      />
      <span
        className={`min-w-0 flex-1 text-sm ${
          alerte.gravite === "danger" ? "text-danger" : "text-texte"
        }`}
      >
        {alerte.texte}
      </span>
      <span className="shrink-0 text-xs font-semibold text-texte-secondaire">
        Ouvrir
      </span>
    </button>
  );
}

function TuileFile({
  file,
  onNaviguer,
}: {
  file: FileAdmin;
  onNaviguer: (ecran: EcranAdmin) => void;
}) {
  /* Les deux files d'argent mènent à l'écran des virements ; le reste suit
     son identifiant quand un écran existe. */
  const destination: EcranAdmin =
    file.id === "retraits" || file.id === "devis-manquants" || file.id === "recus"
      ? "retraits"
      : file.id === "kyc"
        ? "dossiers"
        : "groupages";

  return (
    <button
      type="button"
      onClick={() => onNaviguer(destination)}
      className={`w-full rounded-xl border bg-white p-5 text-left transition-colors hover:border-texte-secondaire ${
        /* ⚠️ Le filet rouge ne marque pas « beaucoup », il marque **notre
           propre trésorerie engagée**. Les autres files coûtent de la
           confiance ; celles-ci coûtent du cash, et un écran qui les traite à
           égalité ment sur les priorités. */
        file.argent_expose && file.nombre > 0
          ? "border-danger"
          : "border-bordure"
      }`}
    >
      <span
        className={`block text-prix font-bold ${
          file.nombre === 0 ? "text-texte-secondaire" : "text-texte"
        }`}
      >
        {file.nombre}
      </span>
      <span
        className={`mt-0.5 block font-semibold ${
          file.nombre === 0 ? "text-texte-secondaire" : "text-texte"
        }`}
      >
        {file.libelle}
      </span>
      <span className="mt-1 block text-xs text-texte-secondaire">
        {file.detail}
      </span>
      {/* C'est cette ligne qui fait agir, pas le compteur. */}
      {file.nombre > 0 && file.plus_ancien_jours > 0 ? (
        <span
          className={`mt-2 block text-xs font-semibold ${
            file.plus_ancien_jours > 2 ? "text-danger" : "text-texte-secondaire"
          }`}
        >
          le plus ancien : {file.plus_ancien_jours} jour
          {file.plus_ancien_jours > 1 ? "s" : ""}
        </span>
      ) : null}
    </button>
  );
}

function TuileIndicateur({ indicateur }: { indicateur: IndicateurAdmin }) {
  const couleur = {
    neutre: "text-texte",
    attention: "text-primaire-texte-sur-fond",
    succes: "text-succes",
  }[indicateur.ton];

  return (
    <div className="rounded-xl border border-bordure bg-white p-5">
      <p className="text-sm text-texte-secondaire">{indicateur.libelle}</p>
      <p className={`mt-1 text-prix font-bold ${couleur}`}>
        {indicateur.unite === "F"
          ? formaterFrancs(indicateur.valeur)
          : `${indicateur.valeur} ${indicateur.unite}`}
      </p>
      <p className="mt-1 text-xs text-texte-secondaire">{indicateur.detail}</p>
    </div>
  );
}
