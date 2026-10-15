import { formaterFrancs } from "../domaine/format";
import { PLAFOND_PAR_NIVEAU } from "../domaine/inscription";
import {
  IllustrationAcheteur,
  IllustrationGroupeur,
} from "../ui/Illustrations";
import Logo from "../ui/Logo";
import {
  IconeBouclier,
  IconeCarton,
  IconeGroupage,
  IconeRetour,
} from "../ui/Icones";

/**
 * Le choix du profil, apres la page de demarrage.
 *
 * ⚠️ **Cet ecran est en tension avec le §1.5**, qui ecrit : « A la premiere
 * ouverture, l'utilisateur arrive **directement** sur le fil », et qui range
 * parmi les trois choses a ne jamais dessiner « un ecran Connexion /
 * Inscription au lancement ».
 *
 * La demande est explicite et posterieure, donc elle s'applique. Mais la
 * raison du §1.5 reste vraie — tout ecran place entre quelqu'un et le produit
 * fait perdre des visiteurs — et trois choses la ramenent a peu de chose :
 *
 * - **le chemin acheteur ne demande rien.** Un appui, et on est sur le fil.
 *   Pas de compte, pas de numero, pas de mot de passe. Ce n'est donc pas un
 *   mur d'authentification, c'est un aiguillage ;
 * - **il est propose en premier et en bouton plein**, l'autre en bouton de
 *   contour. Un visiteur presse n'a pas a lire pour savoir ou appuyer ;
 * - **il n'apparait qu'une fois.** Une fois le choix fait, l'application
 *   s'ouvre directement sur le fil aux lancements suivants.
 *
 * ⚠️ **Les deux illustrations ne contredisent pas le §1.0 regle 7**, qui
 * interdit l'illustration de remplissage : elles **informent**. Celle de
 * l'acheteur montre plusieurs personnes et un seul achat, celle du groupeur un
 * lot qui se repartit en parts — autrement dit le mecanisme que quelqu'un qui
 * arrive pour la premiere fois ne connait pas. Voir `ui/Illustrations.tsx`
 * pour le test a appliquer avant d'en ajouter une troisieme.
 *
 * Si l'un de ces trois points saute, l'ecran redevient le mur que le §1.5
 * interdit. Le §1.5 est a corriger pour acter l'aiguillage, sans quoi il
 * contredit l'ecran construit.
 */
export default function ChoixProfil({
  onAcheteur,
  onGroupeur,
}: {
  onAcheteur: () => void;
  onGroupeur: () => void;
}) {
  return (
    <div className="mx-auto flex min-h-dvh max-w-[430px] flex-col bg-white px-4 py-8 md:max-w-xl md:justify-center">
      <header className="text-center">
        <Logo
          variante="couleur"
          disposition="haut"
          hauteur={96}
          className="mx-auto"
        />
        <h1 className="mt-6 text-2xl font-semibold text-texte">
          Qu&apos;est-ce qui vous amène ?
        </h1>
        <p className="mt-2 text-texte-secondaire">
          Vous pourrez changer plus tard. Acheter ne demande aucun compte.
        </p>
      </header>

      <div className="mt-8 space-y-4">
        {/* Le chemin acheteur, en premier et en bouton plein : un appui, et on
            est sur le fil. */}
        <button
          type="button"
          onClick={onAcheteur}
          className="flex w-full items-center gap-4 rounded-xl bg-primaire p-5 text-left text-white active:bg-primaire-presse"
        >
          {/* L'illustration est a gauche, avant le texte : elle explique le
              mecanisme a quelqu'un qui ne connait pas encore le mot
              « groupage », donc elle doit se lire en premier. */}
          <IllustrationAcheteur className="size-20 shrink-0 sm:size-24" />

          <span className="min-w-0 flex-1">
            <span className="flex items-center gap-3">
              <IconeCarton taille={24} className="shrink-0" />
              <span className="text-lg font-semibold">Je veux acheter</span>
              <IconeRetour taille={20} className="ml-auto shrink-0 rotate-180" />
            </span>
            <span className="mt-2 block text-sm text-white/90">
              Mettez-vous à plusieurs sur un même achat et payez le prix de
              gros. Aucun compte n&apos;est demandé pour regarder.
            </span>
          </span>
        </button>

        {/* Le chemin groupeur, en contour : il engage a une inscription. */}
        <button
          type="button"
          onClick={onGroupeur}
          className="flex w-full items-center gap-4 rounded-xl border-[1.5px] border-confiance p-5 text-left active:bg-confiance-fond"
        >
          <IllustrationGroupeur className="size-20 shrink-0 text-confiance sm:size-24" />

          <span className="min-w-0 flex-1">
            <span className="flex items-center gap-3 text-confiance">
              <IconeGroupage taille={24} className="shrink-0" />
              <span className="text-lg font-semibold">
                Je veux être groupeur
              </span>
              <IconeRetour taille={20} className="ml-auto shrink-0 rotate-180" />
            </span>
            <span className="mt-2 block text-sm text-texte-secondaire">
              Achetez un lot en gros, répartissez-le en parts, encaissez à la
              clôture. Une vérification d&apos;identité est nécessaire avant
              votre premier groupage — comptez cinq minutes.
            </span>
          </span>
        </button>
      </div>

      {/* La promesse de plateforme, des le premier ecran : c'est elle qui
          distingue le produit d'un groupage WhatsApp. */}
      <div className="mt-8 flex items-start gap-2 rounded-xl bg-confiance-fond px-3 py-3 text-sm text-confiance">
        <IconeBouclier taille={20} className="mt-0.5 shrink-0" />
        <p>
          <strong className="font-semibold">
            Vous êtes livré, ou remboursé.
          </strong>{" "}
          Vous êtes livré, ou remboursé. Les groupeurs passent une vérification
          d&apos;identité et collectent jusqu&apos;à{" "}
          {formaterFrancs(PLAFOND_PAR_NIVEAU.entree ?? 0)} par groupage au
          départ.
        </p>
      </div>

      <p className="mt-auto pt-8 text-center text-xs text-texte-secondaire">
        Démonstration — aucun paiement réel n&apos;est effectué.
      </p>
    </div>
  );
}
