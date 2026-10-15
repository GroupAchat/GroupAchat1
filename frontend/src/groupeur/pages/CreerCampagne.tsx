import { creerUneCampagne } from "../../api/espaceGroupeur";
import { useAction } from "../../api/useRequete";
import { useState } from "react";
import { formaterFrancs } from "../../domaine/format";
import {
  CATEGORIES,
  LIBELLE_CATEGORIE,
  type Categorie,
  type MediaProduit,
} from "../../domaine/groupage";
import DepotMedias from "../composants/DepotMedias";
import { FRAIS_PLATEFORME } from "../../domaine/groupeur";
import { FRAIS_PROVISOIRES } from "../../domaine/livraison";
import { EnTeteGroupeur } from "../mise-en-page/ChromeGroupeur";
import Bouton from "../../ui/Bouton";
import Champ from "../../ui/Champ";
import Encart from "../../ui/Encart";
import { IconeCoche } from "../../ui/Icones";

/**
 * Ecran 14 — Creer une campagne. SPEC_ECRANS_FIGMA.md, ecran 14.
 *
 * **Trois etapes.** Un formulaire de douze champs sur un seul ecran mobile ne
 * se remplit pas — c'est la regle des cinq champs du §1.0 appliquee a un cas
 * qui en demande douze.
 *
 * **Etape 1, le produit.** C'est elle qui decide si une campagne se vend. Un
 * acheteur qui ne trouve pas une information ne pose pas de question : il
 * passe a la campagne suivante. Le formulaire **reclame** donc les details au
 * lieu de les rendre optionnels — mais il guide par une liste de controle
 * plutot qu'il ne refuse par une suite d'erreurs. **Un formulaire qui guide
 * obtient de meilleures fiches qu'un formulaire qui bloque.**
 *
 * **Etape 2, le prix a la piece d'abord.** C'est l'ordre naturel pour un
 * commercant : il connait son prix unitaire, pas son prix par lot. Les paliers
 * se deduisent, et leur troisieme colonne — le prix a la piece — est
 * **calculee, jamais saisie**.
 *
 * Un palier dont le prix unitaire *monte* declenche un avertissement, **pas un
 * blocage** : le groupeur peut avoir une raison.
 *
 * **Pas de champ « prix au detail ».** Il a ete retire : aucun prix barre dans
 * l'application (§3). Un groupeur qui le reclame s'entend repondre que son
 * prix de groupe est l'argument.
 *
 * **Les frais se disent ici**, au moment de fixer le prix — c'est le premier
 * des trois rappels, avant l'ecran 16 et l'ecran 18.
 *
 * ⚠️ **Et ils ne se disent pas par part.** 1 500 F sont retenus une seule fois,
 * sur le groupage, au moment du retrait (§9.2). Ecrire « vous recevrez 3 800 F
 * par part » reviendrait a repartir le frais sur chaque part : c'etait vrai du
 * pourcentage, c'est faux d'un montant fixe, et ca ferait croire au groupeur
 * qu'il perd d'autant plus qu'il vend.
 */

interface Palier {
  quantite: number;
  prixTotal: number;
}

export default function CreerCampagne({
  prerempli,
  telephone = "",
  onRetour,
  onPubliee,
}: {
  /** Arrivee depuis l'ecran 19 : la demande agregee qui a declenche la creation. */
  prerempli?: { produit: string; quantite: number; quartier: string };
  /** Le numero du groupeur : c'est lui qui l'identifie (§1.5). */
  telephone?: string;
  onRetour: () => void;
  onPubliee: () => void;
}) {
  const [etape, setEtape] = useState(1);
  const [produit, setProduit] = useState(prerempli?.produit ?? "");
  const [categorie, setCategorie] = useState<Categorie | "">("");
  const [contenuPart, setContenuPart] = useState("");
  const [description, setDescription] = useState("");
  const [medias, setMedias] = useState<MediaProduit[]>([]);
  const [garantie, setGarantie] = useState("");
  const [prixPiece, setPrixPiece] = useState("");
  /* Combien de personnes il veut reunir. **Obligatoire** : c'est le
     denominateur de la barre de progression des cartes (§2.5), et le serveur
     refuse une creation sans lui. */
  const [objectif, setObjectif] = useState("");
  const [coutPiece, setCoutPiece] = useState("");
  const [paliers, setPaliers] = useState<Palier[]>([]);
  const [duree, setDuree] = useState(7);
  const [livraison, setLivraison] = useState<"partenaire" | "propre">(
    "partenaire",
  );

  const publication = useAction(creerUneCampagne);

  const prix = Number(prixPiece) || 0;
  const objectifVoulu = Number(objectif) || 0;
  const cout = Number(coutPiece) || 0;

  /**
   * Publie le groupage. **C'est le moment ou il devient visible des acheteurs.**
   *
   * ⚠️ Le serveur peut refuser, et pour deux raisons qui ne sont pas des
   * fautes de saisie : un dossier KYC non valide (§10.5) et un depassement du
   * plafond de collecte (§10.4). Les deux vivent dans le modele, donc une
   * interface qui masquerait le bouton ne protegerait de rien — il suffit
   * d'une requete directe. Le message du refus est explicite, on l'affiche tel
   * quel.
   */
  const publier = async () => {
    const creee = await publication.executer({
      telephone,
      titre: produit.trim(),
      description: description.trim() || produit.trim(),
      contenu_part: contenuPart.trim() || produit.trim(),
      categorie: categorie as Categorie,
      prix_part: prix,
      objectif_participants: objectifVoulu,
      duree_heures: duree * 24,
      quartier_remise: prerempli?.quartier ?? "Tokoin",
      point_remise: "Point de remise à préciser",
      caracteristiques: garantie.trim()
        ? [{ cle: "Garantie", valeur: garantie.trim() }]
        : [],
      /* Les lignes laissees vides ne partent pas : un media sans adresse
         produirait une image cassee sur la fiche, et le serveur le refuserait
         de toute facon. */
      medias: medias.filter((media) => media.url.trim() !== ""),
    });
    if (creee) {
      onPubliee();
    }
  };

  /** La liste de controle : un bloc a cocher, pas une suite d'erreurs. */
  const controles = [
    { libelle: "Nom du produit", fait: produit.trim() !== "" },
    { libelle: "Catégorie", fait: categorie !== "" },
    { libelle: "Ce que contient une part", fait: contenuPart.trim() !== "" },
    {
      libelle: "Description de 200 caractères minimum",
      fait: description.trim().length >= 200,
    },
    { libelle: "Garantie renseignée", fait: garantie.trim() !== "" },
    /* ⚠️ **Au moins une photo**, et c'est la seule ligne de la liste qui porte
       sur ce que l'acheteur verra avant d'ouvrir la fiche. Un groupage sans
       photo n'est pas incomplet : il est invisible. */
    {
      libelle: "Au moins une photo",
      fait: medias.some(
        (media) => media.type === "image" && media.url.trim() !== "",
      ),
    },
  ];
  const etape1Complete = controles.every((c) => c.fait);

  return (
    <div className="pb-28">
      <EnTeteGroupeur
        titre="Créer une campagne"
        sousTitre={`Étape ${etape} sur 3`}
        onRetour={etape === 1 ? onRetour : () => setEtape(etape - 1)}
      />

      {/* Indicateur de progression. */}
      <div className="flex gap-1 px-4 pt-3">
        {[1, 2, 3].map((n) => (
          <span
            key={n}
            aria-hidden="true"
            className={`h-1 flex-1 rounded-full ${n <= etape ? "bg-confiance" : "bg-bordure"}`}
          />
        ))}
      </div>

      <div className="space-y-5 px-4 pt-5">
        {prerempli ? (
          <Encart variante="info" role="groupeur">
            Créée à partir de {prerempli.quantite} demandes pour «{" "}
            {prerempli.produit} » à {prerempli.quartier}.
          </Encart>
        ) : null}

        {etape === 1 ? (
          <>
            <Champ
              libelle="Nom du produit"
              valeur={produit}
              onChanger={setProduit}
              exemple="Écouteurs filaires avec micro"
              aide="Avec la marque si elle existe."
            />

            <div>
              <label htmlFor="categorie" className="block text-sm font-medium text-texte">
                Catégorie
              </label>
              <select
                id="categorie"
                value={categorie}
                onChange={(e) => setCategorie(e.target.value as Categorie)}
                className="mt-1.5 h-13 w-full rounded-[10px] border border-bordure bg-white px-3 text-texte outline-none focus:border-2 focus:border-confiance"
              >
                <option value="">Choisissez une catégorie</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {LIBELLE_CATEGORIE[c]}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-texte-secondaire">
                Elle pilote les filtres du catalogue.
              </p>
            </div>

            <DepotMedias medias={medias} onChanger={setMedias} />

            <Champ
              libelle="Ce que contient une part"
              valeur={contenuPart}
              onChanger={setContenuPart}
              exemple="1 écouteur filaire avec micro, garantie 3 mois"
              aide="La question que tout acheteur se pose en premier."
            />

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-texte">
                Description
              </label>
              <textarea
                id="description"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="mt-1.5 w-full resize-none rounded-[10px] border border-bordure bg-white px-3 py-2.5 outline-none focus:border-2 focus:border-confiance"
              />
              <p className="mt-1 text-xs text-texte-secondaire">
                {description.trim().length} / 200 caractères minimum
              </p>
            </div>

            <Champ
              libelle="Garantie"
              valeur={garantie}
              onChanger={setGarantie}
              exemple="3 mois, ou « aucune »"
              aide="Ne laissez pas ce champ vide : c'est une question fréquente."
            />

            {/* Un bloc a cocher, pas une suite d'erreurs. */}
            <section className="rounded-xl bg-surface-douce p-4">
              <h2 className="font-semibold text-texte">Avant de publier</h2>
              <ul className="mt-2 space-y-1.5">
                {controles.map((controle) => (
                  <li
                    key={controle.libelle}
                    className={`flex items-center gap-2 text-sm ${
                      controle.fait ? "text-succes" : "text-texte-secondaire"
                    }`}
                  >
                    <IconeCoche taille={16} className="shrink-0" />
                    {controle.libelle}
                  </li>
                ))}
              </ul>
            </section>
          </>
        ) : null}

        {etape === 2 ? (
          <>
            <Champ
              libelle="Prix pour 1 pièce"
              valeur={prixPiece}
              onChanger={(v) => setPrixPiece(v.replace(/\D/g, ""))}
              inputMode="numeric"
              exemple="4000"
              aide="C'est ce prix qui s'affiche partout dans l'application."
            />

            {prix > 0 ? (
              /* Les frais se disent au moment de fixer le prix, pas au moment
                 de retirer. */
              <Encart variante="info" role="groupeur">
                Sur {formaterFrancs(prix)},{" "}
                <strong className="font-semibold">
                  vous recevez {formaterFrancs(prix)} par part
                </strong>
                . Group Achat retient {formaterFrancs(FRAIS_PLATEFORME)} une
                seule fois, au retrait, si le groupage aboutit.
              </Encart>
            ) : null}

            <section>
              <Champ
                libelle="Combien de personnes voulez-vous réunir ?"
                valeur={objectif}
                onChanger={(v) => setObjectif(v.replace(/\D/g, ""))}
                inputMode="numeric"
                exemple="20"
                aide="Les acheteurs verront où en est le groupage par rapport à ce nombre."
              />

              {/* ⚠️ **Dire tout de suite les trois choses que ce nombre ne
                  fait pas.** Un groupeur qui le prend pour une limite de
                  places le met trop haut « pour avoir de la marge », et sa
                  barre reste au quart pendant toute la campagne. Celui qui le
                  prend pour un minimum le met trop bas par peur de l'annulation
                  automatique — qui n'existe pas. */}
              {objectifVoulu > 0 ? (
                <Encart variante="info" role="groupeur">
                  Ce nombre n&apos;est <strong>ni une limite ni un minimum</strong>.
                  Vous pouvez dépasser {objectifVoulu} personnes, et à la clôture
                  c&apos;est vous qui décidez de maintenir le groupage ou non,
                  même s&apos;il n&apos;est pas atteint.
                </Encart>
              ) : null}
            </section>

            <section>
              <h2 className="font-semibold text-texte">Autres quantités</h2>
              <p className="mt-1 text-sm text-texte-secondaire">
                Facultatif. Une campagne sans palier reste parfaitement valable.
              </p>

              {paliers.length > 0 ? (
                <table className="mt-3 w-full text-sm">
                  <thead>
                    <tr className="border-b border-filet text-left text-texte-secondaire">
                      <th className="py-2 font-medium">Quantité</th>
                      <th className="py-2 text-right font-medium">Prix total</th>
                      <th className="py-2 text-right font-medium">À la pièce</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paliers.map((palier, indice) => {
                      const unitaire = Math.round(
                        palier.prixTotal / palier.quantite,
                      );
                      return (
                        <tr key={indice} className="border-b border-filet">
                          <td className="py-2 text-texte">
                            {palier.quantite} pièces
                          </td>
                          <td className="py-2 text-right text-texte">
                            {formaterFrancs(palier.prixTotal)}
                          </td>
                          {/* Calculee, pas saisie. */}
                          <td className="py-2 text-right text-texte-secondaire italic">
                            {formaterFrancs(unitaire)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : null}

              {/* On avertit, on ne bloque pas : il peut avoir une raison. */}
              {paliers.some(
                (p) => prix > 0 && Math.round(p.prixTotal / p.quantite) > prix,
              ) ? (
                <div className="mt-3">
                  <Encart variante="attention" role="groupeur">
                    Sur un de vos paliers, le prix unitaire est plus élevé
                    qu&apos;à 1 pièce. C&apos;est voulu ?
                  </Encart>
                </div>
              ) : null}

              <div className="mt-3">
                <Bouton
                  role="groupeur"
                  style="secondaire"
                  onClick={() =>
                    setPaliers([
                      ...paliers,
                      {
                        quantite: paliers.length === 0 ? 3 : 5,
                        prixTotal:
                          prix * (paliers.length === 0 ? 3 : 5) * 0.92,
                      },
                    ])
                  }
                >
                  + Ajouter une quantité
                </Bouton>
              </div>
            </section>

            {/* Son calcul a lui, qui ne sort jamais de son interface. */}
            <section className="rounded-xl bg-surface-douce p-4">
              <h2 className="font-semibold text-texte">Votre marge</h2>
              <p className="mt-1 text-sm text-texte-secondaire">
                Pour vous seul. Jamais visible de l&apos;acheteur.
              </p>
              <div className="mt-3">
                <Champ
                  libelle="Ce que ça vous coûte à la pièce"
                  valeur={coutPiece}
                  onChanger={(v) => setCoutPiece(v.replace(/\D/g, ""))}
                  inputMode="numeric"
                  exemple="2800"
                />
              </div>
              {prix > 0 && cout > 0 ? (
                <p className="mt-3 text-sm text-texte">
                  Prix de vente {formaterFrancs(prix)} · votre coût{" "}
                  {formaterFrancs(cout)}
                  <br />
                  <strong className="font-semibold">
                    Votre marge : {formaterFrancs(prix - cout)} par pièce
                  </strong>
                  <br />
                  {/* ⚠️ La marge est entiere a la piece : le frais ne se
                      calcule plus par part, il se retient une fois sur le
                      groupage. C'est plus simple a comprendre pour lui, et
                      c'est une des raisons du changement. */}
                  Moins {formaterFrancs(FRAIS_PLATEFORME)} de frais Group Achat
                  au retrait.
                </p>
              ) : null}
            </section>

            <div>
              <p className="text-sm font-medium text-texte">
                Durée de la campagne
              </p>
              <div className="mt-2 flex gap-2">
                {[3, 7, 14].map((jours) => (
                  <button
                    key={jours}
                    type="button"
                    aria-pressed={duree === jours}
                    onClick={() => setDuree(jours)}
                    className={`min-h-12 flex-1 rounded-[10px] border font-medium ${
                      duree === jours
                        ? "border-confiance bg-confiance-fond text-confiance"
                        : "border-bordure text-texte"
                    }`}
                  >
                    {jours} jours
                  </button>
                ))}
              </div>
            </div>
          </>
        ) : null}

        {etape === 3 ? (
          <>
            <h2 className="text-lg font-semibold text-texte">Livraison</h2>
            <div className="space-y-3">
              {(
                [
                  ["partenaire", "J'utilise le service partenaire de Group Achat"],
                  ["propre", "J'ai mon propre livreur"],
                ] as const
              ).map(([cle, libelle]) => (
                <button
                  key={cle}
                  type="button"
                  aria-pressed={livraison === cle}
                  onClick={() => setLivraison(cle)}
                  className={`w-full rounded-xl border p-4 text-left ${
                    livraison === cle
                      ? "border-2 border-confiance bg-confiance-fond"
                      : "border-bordure"
                  }`}
                >
                  <span className="font-medium text-texte">{libelle}</span>
                </button>
              ))}
            </div>

            {/* Une mention qui evite un malentendu couteux. */}
            <p className="text-sm text-texte-secondaire">
              Les frais de livraison ({formaterFrancs(FRAIS_PROVISOIRES)} dans
              Lomé) sont payés par l&apos;acheteur et vont au transporteur. Ils
              n&apos;entrent jamais dans votre solde.
            </p>

            <section className="rounded-xl bg-surface-douce p-4">
              <h3 className="font-semibold text-texte">Récapitulatif</h3>
              <dl className="mt-2 space-y-1 text-sm">
                <Ligne cle="Produit" valeur={produit || "—"} />
                <Ligne
                  cle="Prix d'une part"
                  valeur={prix ? formaterFrancs(prix) : "—"}
                />
                <Ligne
                  cle="Objectif"
                  valeur={
                    objectifVoulu ? `${objectifVoulu} personnes` : "—"
                  }
                />
                <Ligne cle="Durée" valeur={`${duree} jours`} />
                <Ligne
                  cle="Vous recevez"
                  valeur={prix ? `${formaterFrancs(prix)} par part` : "—"}
                />
              </dl>
            </section>
          </>
        ) : null}
      </div>

      <div className="fixed inset-x-0 bottom-0 z-20 mx-auto max-w-[430px] bg-white px-4 py-3 shadow-[0_-2px_12px_rgba(29,25,22,0.06)]">
        {etape < 3 ? (
          <Bouton
            role="groupeur"
            /* ⚠️ L'objectif compte autant que le prix pour passer a
               l'etape 3 : le serveur refuse une creation sans lui, et decouvrir
               ce refus a la derniere etape obligerait a revenir en arriere. */
            desactive={
              etape === 1 ? !etape1Complete : prix <= 0 || objectifVoulu <= 0
            }
            onClick={() => setEtape(etape + 1)}
          >
            Continuer
          </Bouton>
        ) : (
          <>
            {/* Le refus du serveur, colle au bouton : en haut de l'ecran, il
                serait hors champ au moment ou l'on appuie. C'est ici
                qu'atterrissent le dossier KYC non valide (§10.5) et le
                depassement de plafond (§10.4) — deux refus qui s'expliquent,
                et dont le message du modele dit la raison. */}
            {publication.erreur ? (
              <p role="alert" className="mb-2 text-sm font-medium text-danger">
                {publication.erreur.estRefusDeSaisie
                  ? Object.values(publication.erreur.champs)[0]?.[0]
                  : publication.erreur.messageLisible}
              </p>
            ) : null}

            <Bouton
              role="groupeur"
              chargement={publication.enCours}
              onClick={publier}
            >
              Publier le groupage
            </Bouton>
          </>
        )}
      </div>
    </div>
  );
}

function Ligne({ cle, valeur }: { cle: string; valeur: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-texte-secondaire">{cle}</dt>
      <dd className="text-right font-medium text-texte">{valeur}</dd>
    </div>
  );
}
