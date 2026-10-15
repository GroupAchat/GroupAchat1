import {
  CATEGORIES,
  LIBELLE_CATEGORIE,
  type Categorie,
  type Groupage,
} from "../../domaine/groupage";

/**
 * Les six categories, en tuiles colorees. Inspire des rangees de categories
 * d'eBay et de Walmart.
 *
 * ## ⚠️ Ecart assume au §1.2
 *
 * Le §1.2 ecrit : « Aucun aplat "pour decorer" : une couleur signale une
 * action, un etat ou un risque, jamais un ornement. » Ces six teintes sont des
 * ornements. La demande est explicite et posterieure, donc elle s'applique.
 *
 * La raison du §1.2 reste vraie, et **une seule chose la tient** : ces teintes
 * ne colorent que des **surfaces**, jamais un signal. L'orange plein garde le
 * monopole de l'action, le bleu celui de la confiance, le rouge celui du
 * probleme. Le jour ou l'une de ces pastilles se met a dire quelque chose —
 * « nouveau », « bientot ferme » — le systeme de signal s'effondre.
 *
 * C'est aussi pourquoi elles sont **desaturees** : une pastille pale ne peut
 * pas rivaliser avec un aplat sature, donc elle ne peut pas voler le signal.
 * Les valeurs et leurs contrastes sont dans `index.css`.
 *
 * ## ⚠️ La photo vient du catalogue, elle n'est pas un visuel fourni
 *
 * Chaque tuile montre **le premier produit de sa categorie** qui a une photo.
 * C'est ce que fait eBay, et c'est ce qui evite d'avoir a dessiner six
 * illustrations qu'il faudrait ensuite tenir a jour. Consequence directe :
 * une categorie vide n'a pas de photo, et la tuile garde alors sa teinte
 * seule. Elle reste cliquable — elle mene a un etat vide qui dit qu'il n'y a
 * rien, ce qui est une reponse ; une tuile absente laisserait croire que la
 * categorie n'existe pas.
 *
 * ## Elles filtrent, elles ne naviguent pas
 *
 * Un clic pose le filtre sur la grille deja presente en dessous, comme le
 * « Voir plus » de la rangee urgente. Pas de page de categorie a ecrire, a
 * router et a tenir — et le resultat est meilleur : on arrive sur une liste
 * **filtrable**, ou le filtre pose apparait en puce et se retire d'un clic.
 */

/** Les classes sont ecrites en entier : Tailwind ne lit pas les noms calcules. */
const TEINTES: Record<Categorie, { fond: string; accent: string }> = {
  alimentaire: {
    fond: "bg-cat-alimentaire",
    accent: "text-cat-alimentaire-accent",
  },
  vetements: { fond: "bg-cat-vetements", accent: "text-cat-vetements-accent" },
  chaussures: {
    fond: "bg-cat-chaussures",
    accent: "text-cat-chaussures-accent",
  },
  hygiene: { fond: "bg-cat-hygiene", accent: "text-cat-hygiene-accent" },
  maison: { fond: "bg-cat-maison", accent: "text-cat-maison-accent" },
  electronique: {
    fond: "bg-cat-electronique",
    accent: "text-cat-electronique-accent",
  },
};

export default function TuilesCategories({
  groupages,
  actif,
  onChoisir,
}: {
  /** Le catalogue, pour y prendre une photo par categorie. */
  groupages: readonly Groupage[];
  /** La categorie filtree, ou `"toutes"`. */
  actif: Categorie | "toutes";
  onChoisir: (categorie: Categorie) => void;
}) {
  return (
    <section aria-labelledby="titre-categories">
      <h2
        id="titre-categories"
        className="text-2xl font-semibold tracking-tight text-texte"
      >
        Par catégorie
      </h2>

      {/* Six tuiles : deux rangees de trois sur telephone, une seule a partir
          de `lg`. Pas de defilement horizontal — a six elements, tout tient,
          et une rangee qui defile cache toujours son dernier element. */}
      <ul className="mt-4 grid grid-cols-3 gap-3 sm:grid-cols-6 lg:gap-4">
        {CATEGORIES.map((categorie) => {
          const vitrine = groupages.find(
            (groupage) => groupage.categorie === categorie && groupage.photo,
          );
          const teinte = TEINTES[categorie];
          const choisie = actif === categorie;

          return (
            <li key={categorie}>
              <button
                type="button"
                onClick={() => onChoisir(categorie)}
                aria-pressed={choisie}
                className="group block w-full text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primaire"
              >
                {/*
                 * ⚠️ **L'etat choisi se marque par un contour orange, pas par
                 * un changement de teinte.** La teinte appartient a la
                 * categorie ; la faire varier selon l'etat melangerait les
                 * deux langages, et on ne saurait plus si une couleur dit
                 * « alimentaire » ou « selectionne ».
                 */}
                <span
                  className={`relative block aspect-square overflow-hidden rounded-2xl ${teinte.fond} ${
                    choisie ? "ring-2 ring-primaire ring-offset-2" : ""
                  }`}
                >
                  {vitrine?.photo ? (
                    <img
                      src={vitrine.photo}
                      alt=""
                      loading="lazy"
                      decoding="async"
                      /* `p-3` et `object-contain` : le produit flotte sur la
                         teinte au lieu de la recouvrir. C'est ce qui rend la
                         couleur visible — une photo en `object-cover`
                         masquerait entierement le fond, et la rangee
                         redeviendrait six vignettes grises. */
                      className="absolute inset-0 size-full object-contain p-3 transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    /* ⚠️ **Une categorie sans produit garde une tuile pleine.**
                       Un carre de couleur vide se lit comme une image qui n'a
                       pas charge. L'initiale, dans l'accent de la categorie,
                       dit que la tuile est entiere et qu'il n'y a simplement
                       rien dedans. C'est le seul emploi de l'accent, et c'est
                       pour lui que son contraste sur la teinte est calcule —
                       le plus juste tient a 5,37:1 (`maison`). */
                    <span
                      aria-hidden="true"
                      className={`absolute inset-0 flex items-center justify-center text-3xl font-semibold ${teinte.accent}`}
                    >
                      {LIBELLE_CATEGORIE[categorie].charAt(0)}
                    </span>
                  )}
                </span>

                <span
                  className={`mt-2 block text-center text-sm font-medium ${
                    choisie ? "text-primaire-texte-sur-fond" : "text-texte"
                  }`}
                >
                  {LIBELLE_CATEGORIE[categorie]}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
