import Bouton from "../../ui/Bouton";
import FeuilleRemontante from "../../ui/FeuilleRemontante";
import { IconeBouclier, IconeCarton, IconeQuestion } from "../../ui/Icones";

/**
 * « Créez un compte pour continuer » — le message qui précède l'inscription.
 *
 * ## ⚠️ Ce que cet écran est, et ce qu'il n'est pas
 *
 * **Ce n'est pas un mur d'authentification**, et la distinction tient à un
 * seul fait : il n'apparaît **jamais à l'ouverture**. On lit le fil, le
 * catalogue, les fiches produit, les questions déjà posées sans compte. Il ne
 * monte qu'au moment où l'acheteur **engage quelque chose** — rejoindre un
 * groupage, poser une question publique.
 *
 * ⚠️ **Il reste en tension avec le §1.5**, qui écrit que le compte est demandé
 * « au moment de payer » et range la demande de compte parmi les choses à ne
 * pas dessiner. C'est une décision produit prise après, et assumée : le compte
 * est désormais demandé **une opération plus tôt**. Trois choses bornent cet
 * écran, et si l'une saute il redevient le mur que ce paragraphe interdit :
 *
 * - **il se ferme sans rien casser.** La croix, la touche Échap et le voile
 *   ramènent à la page intacte, et l'opération n'est pas perdue — l'appelant
 *   la reprend après l'inscription ;
 * - **il dit pourquoi**, pas seulement qu'il faut un compte. La raison change
 *   selon l'opération, d'où `motif` : « suivre votre livraison » n'a rien à
 *   voir avec « recevoir la réponse du groupeur » ;
 * - **il ne vient qu'une fois par acheteur**, puisque le compte, ensuite,
 *   existe.
 *
 * ## Les deux boutons, et pourquoi ils sont deux
 *
 * ⚠️ **Le `CLAUDE.md` interdit « Se connecter » à côté de « Créer un
 * compte »**, et cet écran enfreint cette règle. Ce n'est pas un oubli : c'est
 * la décision d'aller vers l'inscription classique, où les deux parcours
 * existent vraiment et où deviner à la place de l'acheteur reviendrait à lui
 * refuser l'un des deux.
 *
 * Ce que la règle protégeait reste tenu autrement : **l'inscription est en
 * bouton plein, la connexion en lien discret.** Quelqu'un qui ne sait pas s'il
 * a un compte chez nous n'a donc pas de choix à faire — le chemin proposé est
 * celui qui marche dans les deux cas, puisque le formulaire d'inscription
 * détecte un numéro déjà inscrit et renvoie vers la connexion.
 */

/** Ce que l'acheteur s'apprêtait à faire. */
export type OperationCompte = "rejoindre" | "question" | "compte";

/**
 * Le texte dépend de l'opération, et c'est le cœur de ce composant.
 *
 * ⚠️ **Chaque motif dit ce que le compte sert à faire, pas ce qu'il nous
 * apporte.** « Pour sécuriser nos services » ne rassure personne et ne répond
 * pas à la question que l'acheteur se pose, qui est : qu'est-ce que ça me
 * coûte et qu'est-ce que ça me donne.
 */
const TEXTES: Record<
  OperationCompte,
  {
    titre: string;
    motif: string;
    Icone: (p: { taille?: number }) => React.ReactElement;
    raisons: string[];
  }
> = {
  rejoindre: {
    titre: "Créez votre compte pour rejoindre ce groupage",
    motif:
      "Il faut un compte pour commander une part : c'est lui qui porte votre code de livraison et le suivi de votre colis.",
    Icone: IconeCarton,
    raisons: [
      "Votre code de livraison, à montrer au livreur",
      "Le suivi de votre commande jusqu'à la remise",
      "Votre argent détenu jusqu'à la clôture, ou remboursé",
    ],
  },
  /**
   * ⚠️ **Cette entrée existe mais ne s'affiche normalement jamais.**
   *
   * « compte » est l'opération de quelqu'un qui demande un compte
   * directement, depuis l'onglet Profil : il n'y a rien à lui expliquer, il
   * sait déjà ce qu'il veut, donc l'appelant l'envoie droit au formulaire.
   * Le texte est quand même écrit, parce qu'un `Record` dont une clé
   * manquerait rendrait `undefined` et planterait à la déstructuration — un
   * écran blanc, pour une branche que personne ne relit.
   */
  compte: {
    titre: "Créez votre compte",
    motif:
      "Vos commandes, vos livraisons et vos questions au même endroit, sur tous vos appareils.",
    Icone: IconeCarton,
    raisons: [
      "Vos commandes et vos codes de livraison",
      "Vos demandes de produits, et ce qu'elles deviennent",
      "Votre adresse pré-remplie à la prochaine commande",
    ],
  },
  question: {
    titre: "Créez votre compte pour poser votre question",
    motif:
      "Les questions sont publiques et signées d'un compte. C'est aussi par lui que la réponse du groupeur vous revient.",
    Icone: IconeQuestion,
    raisons: [
      "La réponse du groupeur vous est notifiée",
      "Votre numéro n'est jamais communiqué au groupeur",
      "Une question par compte : personne ne gonfle un fil",
    ],
  },
};

export default function InviteCompte({
  operation,
  onCreerUnCompte,
  onSeConnecter,
  onFermer,
}: {
  operation: OperationCompte;
  onCreerUnCompte: () => void;
  onSeConnecter: () => void;
  onFermer: () => void;
}) {
  const { titre, motif, Icone, raisons } = TEXTES[operation];

  return (
    <FeuilleRemontante titre="Créer un compte" onFermer={onFermer}>
      <div className="mt-2 space-y-5">
        {/* Le médaillon : `primaire-fond` et non `marque` plein. Un disque
            orange vif de 64 px sous un en-tête déjà orange ferait un second
            aplat de marque à trois centimètres du premier. L'icône y tient
            4,87:1, calculé — bien au-delà du seuil de 3:1 d'un élément non
            textuel. */}
        <div className="flex flex-col items-center text-center">
          <span
            aria-hidden="true"
            className="flex size-16 items-center justify-center rounded-full bg-primaire-fond text-primaire-texte-sur-fond"
          >
            <Icone taille={30} />
          </span>

          <h2 className="mt-4 font-titre text-xl font-semibold text-texte">
            {titre}
          </h2>
          <p className="mt-2 max-w-sm text-texte-secondaire">{motif}</p>
        </div>

        {/* Ce que le compte apporte, et seulement ça : trois lignes.
            Une liste plus longue se lit comme des conditions générales, au
            moment précis où l'acheteur hésite. */}
        <ul className="space-y-2.5 rounded-xl bg-surface-douce p-4">
          {raisons.map((raison) => (
            <li key={raison} className="flex items-start gap-2.5">
              {/* `text-primaire` sur `surface-douce` tient 4,36:1 — en dessous
                  du seuil de 4,5:1 pour du texte, mais **au-dessus du seuil de
                  3:1 qui s'applique à un élément non textuel** (WCAG 1.4.11).
                  C'est une icône décorative doublée par le texte à côté, donc
                  elle est conforme ; écrire ce libellé *en* orange ne le
                  serait pas. */}
              <span aria-hidden="true" className="mt-0.5 text-primaire">
                <IconeBouclier taille={18} />
              </span>
              <span className="min-w-0 flex-1 text-sm text-texte">
                {raison}
              </span>
            </li>
          ))}
        </ul>

        <div className="space-y-3">
          <Bouton onClick={onCreerUnCompte}>Créer mon compte</Bouton>

          {/* ⚠️ **En lien, jamais en second bouton plein.** C'est ce qui reste
              de la règle du `CLAUDE.md` : les deux parcours existent, mais un
              seul est proposé comme chemin par défaut. Quelqu'un qui ne sait
              pas s'il a déjà un compte suit le bouton plein, et le formulaire
              d'inscription le renverra ici si son numéro est déjà pris. */}
          <p className="text-center text-sm text-texte-secondaire">
            Vous avez déjà un compte ?{" "}
            <button
              type="button"
              onClick={onSeConnecter}
              className="min-h-12 font-medium text-primaire"
            >
              Se connecter
            </button>
          </p>
        </div>

        {/* La contrepartie de la porte : dire qu'on peut encore partir. Sans
            cette ligne, une feuille qui s'impose devant une action ressemble à
            un péage. */}
        <p className="text-center text-xs text-texte-mention">
          Fermer cette fenêtre vous ramène à la page, rien n&apos;est perdu.
        </p>
      </div>
    </FeuilleRemontante>
  );
}
