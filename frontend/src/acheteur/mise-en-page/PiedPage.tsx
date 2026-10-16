import { IconeBouclier } from "../../ui/Icones";
import Logo from "../../ui/Logo";
import { useNavigationAcheteur } from "./NavigationContexte";

/**
 * Le pied de page des grands ecrans.
 *
 * Sur telephone, la `BarreNav` du bas remplit ce role et il n'y a pas de pied
 * de page : il serait toujours sous la barre, donc jamais vu. Sur ordinateur
 * il reprend la promesse de plateforme et les mentions qu'un site marchand
 * doit porter.
 *
 * Il repete la garantie — « livre ou rembourse » — parce que sur un catalogue
 * long, le bandeau du haut est hors champ au moment ou l'on hesite.
 *
 * ## ⚠️ Plus aucun lien mort, et cinq entrees ont disparu
 *
 * Les onze liens ne menaient **nulle part** : c'etaient des `<button>` sans
 * `onClick`. La justification d'origine — « ils sont la pour que la structure
 * du site soit juste, pas pour faire semblant » — ne tient pas a l'usage : un
 * lien qu'on clique et qui ne repond pas ne decrit aucune structure, il fait
 * douter du reste de la page.
 *
 * Six menent maintenant quelque part pour de vrai. **Les cinq autres ont ete
 * retirees**, parce qu'elles ne pouvaient pas marcher sans que j'ecrive leur
 * page :
 *
 * | Retire | Pourquoi |
 * |---|---|
 * | Comment ca marche | Page a ecrire |
 * | Frais et retraits | Page a ecrire — contenu groupeur, pas acheteur |
 * | Aide | Page a ecrire |
 * | A propos | ⚠️ La page existe, mais elle ment — voir ci-dessous |
 * | **Conditions de vente** | ⚠️ Texte juridique — a faire rediger |
 * | **Confidentialite** | ⚠️ Texte juridique — a faire rediger |
 *
 * ## ⚠️ Pourquoi « A propos » ne pointe pas vers la page de presentation
 *
 * Elle existe pourtant, servie a `/presentation/`, et elle a meme des ancres
 * utilisables (`#etapes`, `#circuit`, `#questions`). Mais **elle decrit
 * l'ancien modele economique** : « commission 5 % », « −6 400 F », « verse
 * 121 600 F », quand la regle en vigueur est **1 500 F fixes** et donc
 * 126 500 F. Elle affirme aussi qu'une campagne qui « n'atteint pas son
 * objectif » rembourse, alors que l'objectif n'est **ni un minimum ni un
 * declencheur**.
 *
 * Y envoyer quelqu'un depuis le pied de page reviendrait a lui faire lire,
 * sur notre propre site, une tarification qui n'est plus la notre. Le lien
 * reviendra quand la page aura ete corrigee — ce qui doit arriver de toute
 * facon, puisqu'elle est deja publique.
 *
 * ⚠️ **Les deux dernieres sont bloquantes pour une mise en ligne reelle.**
 * Une place de marche qui encaisse de l'argent doit porter ses conditions de
 * vente et sa politique de confidentialite. Les retirer ne supprime pas
 * l'obligation — ca retire seulement le lien qui promettait des pages
 * inexistantes, ce qui est pire qu'une absence : un lien vers des CGU laisse
 * croire qu'elles existent et qu'on les a acceptees.
 *
 * Elles reviendront ici le jour ou leur texte existera. Ce n'est pas a moi de
 * l'inventer.
 */
export default function PiedPage() {
  /*
   * ⚠️ **Par le contexte, pas par des proprietes.** Ce pied de page est monte
   * par neuf ecrans, dont aucun n'a a connaitre son contenu — `Questions` n'a
   * rien a voir avec « Devenir groupeur » et devrait pourtant le transporter.
   * Voir `NavigationContexte`.
   */
  const {
    onCatalogue,
    onDemanderProduit,
    onMesCommandes,
    onMesDemandes,
    onDevenirGroupeur,
  } = useNavigationAcheteur();

  return (
    /*
     * ⚠️ **Fond blanc**, comme le reste de l'application. Il etait sur
     * `surface-douce` : un aplat gris en bas de page, alors que tout ce qui
     * est au-dessus est blanc depuis qu'on a retire les bandes. Le filet du
     * haut suffit a le detacher — c'est son role.
     */
    <footer className="mt-16 border-t border-bordure bg-white">
      <div className="largeur-page py-12">
        {/*
         * ⚠️ **Une grille, plus un `flex-wrap` avec 48 px de gouttiere.**
         *
         * En `flex-wrap`, les quatre colonnes se rangeaient selon leur contenu
         * : la plus longue poussait les autres, et a certaines largeurs la
         * derniere passait seule a la ligne, loin a gauche. Les titres de
         * colonne ne s'alignaient alors sur rien.
         *
         * La premiere colonne est plus large que les trois autres : elle porte
         * le logo et deux phrases, les autres une liste de mots.
         */}
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1fr] lg:gap-12">
          <div className="max-w-xs">
            <Logo variante="couleur" disposition="cote" hauteur={30} />
            <p className="mt-3 text-sm text-texte-secondaire">
              Le prix de gros, à plusieurs.
            </p>
            {/* ⚠️ **Cette ligne etait bleue, elle ne l'est plus.** Le bleu est
                le chrome du cote groupeur (§1.2) ; il n'a pas a reapparaitre
                par petites touches sur les ecrans acheteur. La promesse, elle,
                reste — c'est la seule chose qui distingue ce produit d'un
                groupage WhatsApp. */}
            <p className="mt-4 flex items-start gap-2 text-sm font-medium text-texte">
              <span className="mt-0.5 shrink-0 text-primaire">
                <IconeBouclier taille={18} />
              </span>
              Vous êtes livré, ou remboursé.
            </p>
          </div>

          <Colonne titre="Acheter">
            <Lien onClick={onCatalogue}>Tous les groupages</Lien>
            <Lien onClick={onDemanderProduit}>Demander un produit</Lien>
            <Lien onClick={onMesCommandes}>Mes commandes</Lien>
            {/* ⚠️ « Suivre une livraison » a ete remplace par « Mes demandes ».
                Il n'existe pas d'ecran de suivi par code : le suivi est **dans**
                la commande (ecran 9), donc ce lien n'aurait fait que doubler
                celui du dessus. « Mes demandes » (ecran 12), lui, n'avait aucun
                chemin depuis le pied de page. */}
            <Lien onClick={onMesDemandes}>Mes demandes</Lien>
          </Colonne>

          <Colonne titre="Vendre">
            <Lien onClick={onDevenirGroupeur}>Devenir groupeur</Lien>
          </Colonne>
        </div>

        <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-filet pt-6 text-sm text-texte-mention">
          <p>© 2026 Group Achat — Lomé, Togo</p>
          {/* Dit au meme endroit que partout ailleurs : le paiement n'est pas
              reel tant que l'agregateur n'est pas agree (§18.2 du cahier des
              charges). */}
          <p>Démonstration — aucun paiement réel n&apos;est effectué.</p>
        </div>
      </div>
    </footer>
  );
}

function Colonne({
  titre,
  children,
}: {
  titre: string;
  children: React.ReactNode;
}) {
  return (
    <nav aria-label={titre}>
      <h2 className="text-sm font-semibold text-texte">{titre}</h2>
      <ul className="mt-3 space-y-2">{children}</ul>
    </nav>
  );
}

/**
 * ⚠️ **Sans `onClick`, le lien ne s'affiche pas du tout.**
 *
 * C'est le garde-fou qui empeche les liens morts de revenir : si quelqu'un
 * ajoute une entree ici sans la brancher, elle ne sera pas dessinee plutot que
 * dessinee inerte. Un pied de page incomplet se repare ; un pied de page qui
 * ment ne se remarque pas.
 */
function Lien({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick?: () => void;
}) {
  if (!onClick) {
    return null;
  }

  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        className="text-left text-sm text-texte-secondaire underline-offset-4 hover:text-primaire hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primaire"
      >
        {children}
      </button>
    </li>
  );
}
