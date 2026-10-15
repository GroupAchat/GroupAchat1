import { IconeRetour } from "../../ui/Icones";

/**
 * L'en-tete d'un ecran interieur sur telephone : retour a gauche, titre, et
 * une action facultative a droite.
 *
 * Il etait copie-colle a l'identique dans quatre pages. Le regrouper n'est pas
 * qu'une economie de lignes : c'est ce qui garantit que **le retour est
 * toujours au meme endroit**, ce que demande le §1.0 (« simple », regle 2, et
 * sa cousine : le retour est toujours possible et ne detruit rien).
 *
 * `collant` par defaut : sur une fiche longue, le retour doit rester a portee
 * sans remonter toute la page.
 *
 * Sur grand ecran, il n'a pas lieu d'etre — la navigation est en haut du site
 * et le retour passe par le fil d'Ariane. Les pages concernees ne l'appellent
 * donc que dans leur branche mobile.
 */
export default function EnTeteEcran({
  titre,
  onRetour,
  action,
  collant = true,
}: {
  titre: string;
  /** Absent sur un ecran dont on ne revient pas, comme la confirmation. */
  onRetour?: () => void;
  /** Bouton facultatif a droite : partager, fermer, aider. */
  action?: React.ReactNode;
  collant?: boolean;
}) {
  return (
    <header
      className={`${collant ? "sticky top-0 z-10" : ""} flex h-14 items-center gap-1 border-b border-filet bg-white px-2`}
    >
      {onRetour ? (
        <button
          type="button"
          onClick={onRetour}
          aria-label="Retour"
          className="flex size-12 shrink-0 items-center justify-center text-texte"
        >
          <IconeRetour />
        </button>
      ) : (
        <span className="w-2" />
      )}

      <h1 className="min-w-0 flex-1 truncate text-lg font-semibold text-texte">
        {titre}
      </h1>

      {action ? <div className="shrink-0">{action}</div> : null}
    </header>
  );
}
